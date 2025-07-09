"""Spotify cookie refresh strategy implementation.

This module implements the manual cookie refresh strategy for Spotify,
which requires user interaction for login due to various auth methods.
"""

import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime

from playwright.sync_api import Page, BrowserContext, TimeoutError as PlaywrightTimeout

from .base import BaseRefreshStrategy, RefreshResult
from ..storage import CookieStorageManager
from ..notifier import CookieRefreshNotifier

logger = logging.getLogger(__name__)


class SpotifyRefreshStrategy(BaseRefreshStrategy):
    """Cookie refresh strategy for Spotify."""
    
    def __init__(self, 
                 service_name: str,
                 storage_manager: CookieStorageManager,
                 notifier: Optional[CookieRefreshNotifier] = None,
                 config: Optional[Dict[str, Any]] = None):
        """Initialize Spotify refresh strategy.
        
        Args:
            service_name: Name of the service (should be 'spotify')
            storage_manager: Cookie storage manager instance
            notifier: Optional notifier for alerts
            config: Service-specific configuration
        """
        super().__init__(service_name, storage_manager, notifier, config)
        
        # Spotify for Artists specific settings
        self.artists_url = 'https://artists.spotify.com'
        self.login_url = 'https://artists.spotify.com'  # Start directly at artists page - it will redirect to login if needed
        self.success_url_pattern = '*://artists.spotify.com/*'
        
        # Multi-account support for artist profiles
        self.supported_accounts = config.get('accounts', ['ZONE A0', 'PIG1987']) if config else ['ZONE A0', 'PIG1987']
        
        # Success indicators for Spotify for Artists
        self.success_indicators = [
            'artists.spotify.com',
            'artists.spotify.com/home',
            'artists.spotify.com/c/',
            'artists.spotify.com/profile'
        ]
        
        # Validate URLs are correct for Spotify for Artists
        self._validate_urls()
        
        # Elements that indicate successful login to Spotify for Artists
        self.logged_in_selectors = [
            '[data-testid="user-widget"]',
            '[data-testid="user-menu"]',
            'button[aria-label*="Menu"]',
            'nav[role="navigation"]',
            '.s4a-header',
            '[class*="navbar"]',
            '[class*="Header"]',
            'button[class*="ProfileButton"]',
            '[aria-label*="Profile"]',
            '[data-testid*="profile"]',
            'div[class*="UserMenu"]',
            'img[alt*="Profile"]'
        ]
        
    def _validate_urls(self) -> None:
        """Validate that URLs are configured correctly for Spotify for Artists.
        
        Raises:
            ValueError: If URLs are not compatible with Spotify for Artists
        """
        # Check that we're using artists.spotify.com, not regular consumer URLs
        required_domain = 'artists.spotify.com'
        invalid_domains = ['accounts.spotify.com/login', 'open.spotify.com', 'spotify.com/login']
        
        # Validate login URL
        if required_domain not in self.login_url:
            raise ValueError(
                f"Invalid login URL for Spotify for Artists: {self.login_url}. "
                f"Must contain '{required_domain}' for artist accounts."
            )
        
        # Check for common mistakes
        for invalid_domain in invalid_domains:
            if invalid_domain in self.login_url:
                raise ValueError(
                    f"Login URL contains consumer domain '{invalid_domain}'. "
                    f"Use '{required_domain}' for Spotify for Artists instead."
                )
        
        # Validate artists URL
        if required_domain not in self.artists_url:
            raise ValueError(
                f"Invalid artists URL: {self.artists_url}. "
                f"Must contain '{required_domain}'."
            )
        
        # Validate success indicators
        if not any(required_domain in indicator for indicator in self.success_indicators):
            raise ValueError(
                f"Success indicators must include '{required_domain}' for Spotify for Artists"
            )
        
        logger.info("✅ Spotify strategy URLs validated for Spotify for Artists")
        
    def refresh_cookies(self, account: Optional[str] = None) -> RefreshResult:
        """Refresh cookies for Spotify for Artists using manual login.
        
        Args:
            account: Artist account name ('ZONE A0', 'PIG1987', or None for all)
            
        Returns:
            RefreshResult object
        """
        # Validate account if specified
        if account and account not in self.supported_accounts:
            return RefreshResult(
                success=False,
                message=f"Unsupported artist account: {account}. Supported: {self.supported_accounts}",
                manual_intervention_required=True
            )
        
        # If no account specified, default to first account or prompt user
        if not account:
            account = self.supported_accounts[0]  # Default to first account
            logger.info(f"No account specified, using default: {account}")
        
        logger.info(f"Starting Spotify for Artists cookie refresh for: {account}")
        logger.info("This will refresh access to Spotify for Artists dashboard and analytics")
        
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
                        page.goto(self.artists_url)
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
                    
                    # Navigate to Spotify for Artists (will redirect to login if needed)
                    logger.info(f"Navigating to Spotify for Artists: {self.login_url}")
                    page.goto(self.login_url)
                    page.wait_for_load_state('domcontentloaded')
                    
                    # Notify user about manual login
                    logger.info(f"Spotify for Artists login required for: {account}")
                    logger.info("Please complete login manually in the browser window.")
                    logger.info("After login, make sure to select the correct artist profile!")
                    
                    if self.notifier:
                        self.notifier.notify_manual_intervention_required(
                            self.service_name,
                            f"Please complete Spotify for Artists login for: {account}",
                            details={'account': account, 'type': 'artist_login'}
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
                        logger.info(f"Spotify for Artists cookies refreshed successfully for {account}")
                        
                        if self.notifier:
                            self.notifier.notify_refresh_success(
                                self.service_name,
                                account,
                                details={'type': 'artist_account'}
                            )
                        
                        return RefreshResult(
                            success=True,
                            message=f"Cookies refreshed successfully for artist: {account}",
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
            message=f"Failed after {self.max_attempts} attempts for artist: {account}",
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
            page = context.new_page()
            
            # Try to access Spotify for Artists
            logger.info(f"Validating cookies by accessing {self.artists_url}")
            page.goto(self.artists_url)
            page.wait_for_load_state('networkidle', timeout=30000)
            
            # Check if we're logged in
            if self._is_logged_in(page):
                logger.info("Spotify cookies validated successfully")
                return True
            
            # Check if redirected to login
            if 'accounts.spotify.com/login' in page.url:
                logger.warning("Redirected to login page, cookies invalid")
                return False
            
            # Additional check - try to find user elements
            for selector in self.logged_in_selectors[:3]:  # Check first few selectors
                try:
                    if page.query_selector(selector):
                        logger.info(f"Found logged-in element: {selector}")
                        return True
                except:
                    continue
            
            logger.warning("No logged-in indicators found, cookies may be invalid")
            return False
            
        except Exception as e:
            logger.error(f"Cookie validation error: {e}")
            return False
        finally:
            if 'page' in locals():
                page.close()
    
    def _is_logged_in(self, page: Page) -> bool:
        """Check if user is logged in to Spotify.
        
        Args:
            page: Browser page
            
        Returns:
            True if logged in
        """
        try:
            # Check URL first
            current_url = page.url
            if any(indicator in current_url for indicator in self.success_indicators):
                # Not on login page - good sign
                if 'login' not in current_url:
                    # Try to find user elements
                    for selector in self.logged_in_selectors:
                        try:
                            element = page.query_selector(selector)
                            if element:
                                logger.debug(f"Found logged-in indicator: {selector}")
                                return True
                        except:
                            continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return False
    
    def _wait_for_manual_login(self, page: Page, account: str) -> bool:
        """Wait for user to complete manual login.
        
        Args:
            page: Browser page
            account: Artist account name
            
        Returns:
            True if login successful
        """
        logger.info(f"Waiting for manual login completion for artist: {account}...")
        logger.info("Please log in and select the correct artist profile!")
        logger.info("Looking for successful navigation to Spotify for Artists...")
        
        timeout_seconds = 300  # 5 minutes
        start_time = time.time()
        check_interval = 2  # seconds
        
        while time.time() - start_time < timeout_seconds:
            try:
                current_url = page.url
                
                # Check if we've navigated away from login
                if 'accounts.spotify.com/login' not in current_url:
                    # Give page time to load
                    page.wait_for_load_state('networkidle', timeout=10000)
                    
                    # Check if we're logged in
                    if self._is_logged_in(page):
                        logger.info(f"Login successful! Now at: {current_url}")
                        return True
                    
                    # Check for specific success pages
                    if any(indicator in current_url for indicator in self.success_indicators):
                        logger.info(f"Reached success page: {current_url}")
                        return True
                
                # Check for OAuth redirects (Facebook, Google, Apple)
                oauth_providers = ['facebook.com', 'accounts.google.com', 'appleid.apple.com']
                if any(provider in current_url for provider in oauth_providers):
                    logger.info(f"OAuth login detected: {current_url}")
                    logger.info("Waiting for OAuth completion...")
                
                # Visual feedback
                elapsed = int(time.time() - start_time)
                remaining = timeout_seconds - elapsed
                if elapsed % 30 == 0:  # Update every 30 seconds
                    logger.info(f"Still waiting for login... ({remaining}s remaining)")
                
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error during login wait: {e}")
                # Don't fail immediately, user might still be logging in
                time.sleep(check_interval)
        
        logger.error(f"Login timeout after {timeout_seconds} seconds")
        if self.screenshot_on_failure:
            self._save_screenshot(page, "login_timeout")
        return False
    
    def _verify_login_success(self, page: Page, context: BrowserContext, account: str) -> bool:
        """Verify that login was successful and we can access Spotify services.
        
        Args:
            page: Browser page
            context: Browser context
            account: Artist account name
            
        Returns:
            True if login verified
        """
        try:
            logger.info(f"Verifying login success for artist: {account}...")
            
            # Navigate to Spotify for Artists if not already there
            if 'artists.spotify.com' not in page.url:
                logger.info(f"Navigating to {self.artists_url} for verification...")
                page.goto(self.artists_url)
                page.wait_for_load_state('networkidle', timeout=20000)
            
            # Check if we stayed on artists page (not redirected to login)
            if 'artists.spotify.com' in page.url and 'login' not in page.url:
                logger.info("Successfully accessed Spotify for Artists")
                
                # Try to find user elements as final confirmation
                for selector in self.logged_in_selectors[:5]:  # Check first 5 selectors
                    try:
                        if page.query_selector(selector):
                            logger.info(f"Login verified with element: {selector}")
                            return True
                    except:
                        continue
                
                # Even if we don't find specific elements, being on artists page is good
                logger.info("On artists page, assuming login successful")
                return True
            
            # Try regular Spotify web player
            logger.info("Trying Spotify web player for verification...")
            page.goto('https://open.spotify.com')
            page.wait_for_load_state('networkidle', timeout=20000)
            
            if 'open.spotify.com' in page.url and self._is_logged_in(page):
                logger.info("Login verified via Spotify web player")
                return True
            
            logger.error("Login verification failed - unable to access Spotify services")
            if self.screenshot_on_failure:
                self._save_screenshot(page, "verification_failed")
            return False
            
        except Exception as e:
            logger.error(f"Error during login verification: {e}")
            if self.screenshot_on_failure:
                self._save_screenshot(page, "verification_error")
            return False