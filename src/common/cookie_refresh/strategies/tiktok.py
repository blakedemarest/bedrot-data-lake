"""TikTok cookie refresh strategy implementation.

This module implements the cookie refresh strategy for TikTok with
multi-account support and handling for QR code or manual login methods.
"""

import json
import logging
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Page, BrowserContext, TimeoutError as PlaywrightTimeout

from .base import BaseRefreshStrategy, RefreshResult
from ..storage import CookieStorageManager
from ..notifier import CookieRefreshNotifier

logger = logging.getLogger(__name__)


class TikTokRefreshStrategy(BaseRefreshStrategy):
    """Cookie refresh strategy for TikTok with multi-account support."""
    
    def __init__(self, 
                 service_name: str,
                 storage_manager: CookieStorageManager,
                 notifier: Optional[CookieRefreshNotifier] = None,
                 config: Optional[Dict[str, Any]] = None):
        """Initialize TikTok refresh strategy.
        
        Args:
            service_name: Name of the service (should be 'tiktok')
            storage_manager: Cookie storage manager instance
            notifier: Optional notifier for alerts
            config: Service-specific configuration
        """
        super().__init__(service_name, storage_manager, notifier, config)
        
        # TikTok specific settings
        self.login_url = 'https://www.tiktok.com/login'
        self.creator_center_url = 'https://www.tiktok.com/creator-center'
        self.studio_url = 'https://www.tiktok.com/tiktokstudio/creator_center/homepage'
        
        # Multi-account support
        self.supported_accounts = config.get('accounts', ['pig1987', 'zone.a0']) if config else ['pig1987', 'zone.a0']
        
        # Required cookies for TikTok
        self.required_cookies = ['sessionid', 'sid_guard', 'uid_tt']
        
        # Success indicators
        self.success_indicators = [
            'creator-center',
            'tiktokstudio',
            'creator_center',
            'analytics',
            'profile'
        ]
        
        # Logged in selectors
        self.logged_in_selectors = [
            '[data-e2e="profile-icon"]',
            '[data-e2e="nav-profile"]',
            '[class*="DivHeaderRightContainer"]',
            '[class*="avatar"]',
            'div[class*="UserAvatar"]',
            'a[href*="/profile"]'
        ]
        
    def refresh_cookies(self, account: Optional[str] = None) -> RefreshResult:
        """Refresh cookies for TikTok account.
        
        Args:
            account: Account identifier (e.g., 'pig1987', 'zone.a0')
            
        Returns:
            RefreshResult object
        """
        # Validate account
        if account and account not in self.supported_accounts:
            return RefreshResult(
                success=False,
                message=f"Unsupported account: {account}. Supported: {self.supported_accounts}",
                manual_intervention_required=True
            )
        
        # If no account specified, refresh all accounts
        if not account:
            logger.info("No account specified, refreshing all TikTok accounts...")
            results = []
            for acc in self.supported_accounts:
                logger.info(f"Refreshing cookies for account: {acc}")
                result = self._refresh_single_account(acc)
                results.append((acc, result))
            
            # Aggregate results
            all_success = all(r[1].success for r in results)
            message = "; ".join(f"{acc}: {r.message}" for acc, r in results)
            
            return RefreshResult(
                success=all_success,
                message=message,
                cookies_saved=all_success,
                storage_state_saved=all_success,
                manual_intervention_required=any(r[1].manual_intervention_required for r in results)
            )
        
        # Refresh single account
        return self._refresh_single_account(account)
    
    def _refresh_single_account(self, account: str) -> RefreshResult:
        """Refresh cookies for a single TikTok account.
        
        Args:
            account: Account identifier
            
        Returns:
            RefreshResult object
        """
        logger.info(f"Starting TikTok cookie refresh for account: {account}")
        
        # Backup current auth state
        self.backup_current_auth(account)
        
        # Try to refresh
        for attempt in range(1, self.max_attempts + 1):
            self._log_refresh_attempt(attempt, self.max_attempts, account)
            
            try:
                # Load existing auth state if available
                existing_auth = self.load_existing_auth(account)
                
                with self.create_browser_context(existing_auth) as (browser, context, page):
                    # First check if existing auth works
                    if existing_auth:
                        logger.info(f"Testing existing authentication for {account}...")
                        page.goto(self.studio_url)
                        page.wait_for_load_state('networkidle', timeout=15000)
                        
                        if self._is_logged_in(page):
                            logger.info(f"Existing authentication still valid for {account}")
                            if self.validate_cookies(context):
                                # Refresh the auth state
                                if self.save_auth_state(context, account):
                                    return RefreshResult(
                                        success=True,
                                        message=f"Session already valid for {account}, cookies refreshed",
                                        cookies_saved=True,
                                        storage_state_saved=True
                                    )
                    
                    # Navigate to login page
                    logger.info(f"Navigating to {self.login_url}")
                    page.goto(self.login_url)
                    page.wait_for_load_state('domcontentloaded')
                    
                    # Detect login method
                    login_method = self._detect_login_method(page)
                    logger.info(f"Detected login method: {login_method}")
                    
                    # Notify user about manual login
                    if login_method == 'qr':
                        message = f"Please scan QR code to login TikTok account: {account}"
                    else:
                        message = f"Please complete TikTok login for account: {account}"
                    
                    logger.info(message)
                    if self.notifier:
                        self.notifier.notify_manual_intervention_required(
                            self.service_name,
                            message,
                            details={'account': account, 'method': login_method}
                        )
                    
                    # Wait for manual login
                    if not self._wait_for_manual_login(page, account):
                        logger.error(f"Manual login timeout or failed for {account}")
                        continue
                    
                    # Validate successful login
                    if not self._verify_login_success(page, context, account):
                        logger.error(f"Login verification failed for {account}")
                        continue
                    
                    # Save authentication state
                    if self.save_auth_state(context, account):
                        logger.info(f"TikTok cookies refreshed successfully for {account}")
                        
                        # Also save in legacy format for compatibility
                        self._save_legacy_cookies(context, account)
                        
                        if self.notifier:
                            self.notifier.notify_refresh_success(
                                self.service_name,
                                account,
                                details={'method': login_method}
                            )
                        
                        return RefreshResult(
                            success=True,
                            message=f"Cookies refreshed successfully for {account}",
                            cookies_saved=True,
                            storage_state_saved=True
                        )
                    else:
                        logger.error(f"Failed to save authentication state for {account}")
                        
            except Exception as e:
                logger.error(f"Attempt {attempt} failed for {account}: {e}")
                if attempt == self.max_attempts:
                    return self._handle_refresh_error(e, account)
        
        return RefreshResult(
            success=False,
            message=f"Failed after {self.max_attempts} attempts for {account}",
            manual_intervention_required=True
        )
    
    def validate_cookies(self, context: BrowserContext) -> bool:
        """Validate that cookies are working properly.
        
        Args:
            context: Browser context with loaded cookies
            
        Returns:
            True if cookies are valid
        """
        try:
            # Check if we have required cookies
            cookies = context.cookies()
            cookie_names = {c['name'] for c in cookies}
            
            missing_cookies = set(self.required_cookies) - cookie_names
            if missing_cookies:
                logger.warning(f"Missing required cookies: {missing_cookies}")
                return False
            
            # Check cookie expiration
            now = datetime.now().timestamp()
            expired_count = sum(1 for c in cookies if c.get('expires', float('inf')) < now)
            if expired_count > 0:
                logger.warning(f"{expired_count} cookies have expired")
            
            # Try to access TikTok Studio
            page = context.new_page()
            logger.info(f"Validating cookies by accessing {self.studio_url}")
            page.goto(self.studio_url)
            page.wait_for_load_state('networkidle', timeout=30000)
            
            # Check if we're logged in
            if self._is_logged_in(page):
                logger.info("TikTok cookies validated successfully")
                return True
            
            # Check if redirected to login
            if 'login' in page.url:
                logger.warning("Redirected to login page, cookies invalid")
                return False
            
            logger.warning("Unable to verify login status")
            return False
            
        except Exception as e:
            logger.error(f"Cookie validation error: {e}")
            return False
        finally:
            if 'page' in locals():
                page.close()
    
    def _is_logged_in(self, page: Page) -> bool:
        """Check if user is logged in to TikTok.
        
        Args:
            page: Browser page
            
        Returns:
            True if logged in
        """
        try:
            # Check URL first
            current_url = page.url
            if any(indicator in current_url for indicator in self.success_indicators):
                # Try to find user elements
                for selector in self.logged_in_selectors:
                    try:
                        element = page.query_selector(selector)
                        if element:
                            logger.debug(f"Found logged-in indicator: {selector}")
                            return True
                    except:
                        continue
            
            # Check for login page indicators
            if 'login' in current_url or 'signup' in current_url:
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return False
    
    def _detect_login_method(self, page: Page) -> str:
        """Detect available login methods on the page.
        
        Args:
            page: Browser page
            
        Returns:
            Login method type ('qr', 'email', 'phone', 'social')
        """
        try:
            # Wait for login options to load
            page.wait_for_timeout(2000)
            
            # Check for QR code
            qr_selectors = [
                '[data-e2e="qrcode-login"]',
                'canvas[class*="qrcode"]',
                'img[alt*="QR"]',
                'div[class*="QRCode"]'
            ]
            
            for selector in qr_selectors:
                if page.query_selector(selector):
                    return 'qr'
            
            # Check for other methods
            if page.query_selector('input[placeholder*="Email"], input[placeholder*="email"]'):
                return 'email'
            elif page.query_selector('input[placeholder*="Phone"], input[placeholder*="phone"]'):
                return 'phone'
            else:
                return 'social'
                
        except Exception:
            return 'unknown'
    
    def _wait_for_manual_login(self, page: Page, account: str) -> bool:
        """Wait for user to complete manual login.
        
        Args:
            page: Browser page
            account: Account identifier
            
        Returns:
            True if login successful
        """
        logger.info(f"Waiting for manual login completion for {account}...")
        
        timeout_seconds = 300  # 5 minutes
        start_time = time.time()
        check_interval = 2  # seconds
        
        while time.time() - start_time < timeout_seconds:
            try:
                current_url = page.url
                
                # Check if we've navigated away from login
                if 'login' not in current_url and 'signup' not in current_url:
                    # Give page time to load
                    page.wait_for_load_state('networkidle', timeout=10000)
                    
                    # Check if we're logged in
                    if self._is_logged_in(page):
                        logger.info(f"Login successful for {account}! Now at: {current_url}")
                        return True
                    
                    # Check for specific success pages
                    if any(indicator in current_url for indicator in self.success_indicators):
                        logger.info(f"Reached success page for {account}: {current_url}")
                        return True
                
                # Visual feedback
                elapsed = int(time.time() - start_time)
                remaining = timeout_seconds - elapsed
                if elapsed % 30 == 0:  # Update every 30 seconds
                    logger.info(f"Still waiting for {account} login... ({remaining}s remaining)")
                
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error during login wait for {account}: {e}")
                time.sleep(check_interval)
        
        logger.error(f"Login timeout after {timeout_seconds} seconds for {account}")
        if self.screenshot_on_failure:
            self._save_screenshot(page, f"login_timeout_{account}")
        return False
    
    def _verify_login_success(self, page: Page, context: BrowserContext, account: str) -> bool:
        """Verify that login was successful.
        
        Args:
            page: Browser page
            context: Browser context
            account: Account identifier
            
        Returns:
            True if login verified
        """
        try:
            logger.info(f"Verifying login success for {account}...")
            
            # Navigate to TikTok Studio
            if 'tiktokstudio' not in page.url and 'creator-center' not in page.url:
                logger.info(f"Navigating to {self.studio_url} for verification...")
                page.goto(self.studio_url)
                page.wait_for_load_state('networkidle', timeout=20000)
            
            # Check if we can access creator tools
            if any(indicator in page.url for indicator in self.success_indicators):
                logger.info(f"Successfully accessed TikTok creator tools for {account}")
                
                # Verify we have required cookies
                cookies = context.cookies()
                cookie_names = {c['name'] for c in cookies}
                
                missing = set(self.required_cookies) - cookie_names
                if missing:
                    logger.warning(f"Missing required cookies for {account}: {missing}")
                    return False
                
                logger.info(f"Login verified for {account} with all required cookies")
                return True
            
            logger.error(f"Login verification failed for {account}")
            if self.screenshot_on_failure:
                self._save_screenshot(page, f"verification_failed_{account}")
            return False
            
        except Exception as e:
            logger.error(f"Error during login verification for {account}: {e}")
            if self.screenshot_on_failure:
                self._save_screenshot(page, f"verification_error_{account}")
            return False
    
    def _save_legacy_cookies(self, context: BrowserContext, account: str):
        """Save cookies in legacy format for compatibility with existing extractors.
        
        Args:
            context: Browser context
            account: Account identifier
        """
        try:
            cookies = context.cookies()
            
            # Convert to legacy format
            legacy_cookies = []
            for cookie in cookies:
                if cookie['domain'].endswith('tiktok.com'):
                    legacy_cookie = {
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': cookie['domain'],
                        'path': cookie['path'],
                        'expires': cookie.get('expires', -1),
                        'httpOnly': cookie.get('httpOnly', False),
                        'secure': cookie.get('secure', False),
                        'sameSite': cookie.get('sameSite', 'None')
                    }
                    
                    # Add expiration date if available
                    if 'expires' in cookie and cookie['expires'] > 0:
                        legacy_cookie['expirationDate'] = cookie['expires']
                    
                    legacy_cookies.append(legacy_cookie)
            
            # Save to legacy location
            project_root = Path(self.storage_manager.cookies_dir).parent
            legacy_path = project_root / 'tiktok' / 'cookies' / f'tiktok_cookies_{account}.json'
            legacy_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(legacy_path, 'w') as f:
                json.dump(legacy_cookies, f, indent=2)
            
            logger.info(f"Saved legacy cookies for {account} to {legacy_path}")
            
        except Exception as e:
            logger.error(f"Failed to save legacy cookies for {account}: {e}")