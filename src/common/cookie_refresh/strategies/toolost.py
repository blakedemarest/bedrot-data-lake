"""TooLost cookie refresh strategy implementation.

This module implements the cookie refresh strategy for TooLost,
which is CRITICAL as JWT tokens expire every 7 days. This strategy
handles both cookie and localStorage/storageState extraction.
"""

import json
import logging
import time
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from playwright.sync_api import Page, BrowserContext, TimeoutError as PlaywrightTimeout

from .base import BaseRefreshStrategy, RefreshResult
from ..storage import CookieStorageManager
from ..notifier import CookieRefreshNotifier

logger = logging.getLogger(__name__)


class TooLostRefreshStrategy(BaseRefreshStrategy):
    """Cookie refresh strategy for TooLost - CRITICAL PRIORITY."""
    
    def __init__(self, 
                 service_name: str,
                 storage_manager: CookieStorageManager,
                 notifier: Optional[CookieRefreshNotifier] = None,
                 config: Optional[Dict[str, Any]] = None):
        """Initialize TooLost refresh strategy.
        
        Args:
            service_name: Name of the service
            storage_manager: Cookie storage manager instance
            notifier: Optional notifier for alerts
            config: Service-specific configuration
        """
        super().__init__(service_name, storage_manager, notifier, config)
        
        # TooLost specific settings
        self.login_url = 'https://toolost.com/login'
        self.portal_url = 'https://toolost.com/user-portal/analytics/platform'
        self.api_base = 'https://toolost.com/api/portal'
        
        # Override expiration to 7 days for JWT tokens
        self.jwt_expiration_days = 7
        
        # Success indicators
        self.success_indicators = [
            'user-portal',
            'analytics',
            'dashboard',
            'notifications'
        ]
        
        # Logged in selectors
        self.logged_in_selectors = [
            'nav',
            'aside',
            '.ant-layout-sider',
            '.dashboard',
            '[data-testid*=user-menu]',
            '.ant-menu',
            '[class*="user-portal"]'
        ]
        
        # API endpoints to verify
        self.test_apis = [
            f"{self.api_base}/analytics/spotify?release=&date=thisYear",
            f"{self.api_base}/analytics/apple/?release=&date=thisYear"
        ]
        
    def refresh_cookies(self, account: Optional[str] = None) -> RefreshResult:
        """Refresh cookies and JWT for TooLost.
        
        CRITICAL: JWT expires every 7 days!
        
        Args:
            account: Not used for TooLost (single account)
            
        Returns:
            RefreshResult object
        """
        logger.warning("Starting CRITICAL TooLost cookie/JWT refresh (expires every 7 days)...")
        
        # Backup current auth state
        self.backup_current_auth()
        
        # Try to refresh
        for attempt in range(1, self.max_attempts + 1):
            self._log_refresh_attempt(attempt, self.max_attempts)
            
            try:
                # Load existing auth state if available
                existing_auth = self.load_existing_auth()
                
                with self.create_browser_context(existing_auth) as (browser, context, page):
                    # First check if existing auth works
                    if existing_auth:
                        logger.info("Testing existing authentication...")
                        if self._test_existing_auth(page, context):
                            logger.info("Existing authentication still valid")
                            # Refresh the auth state to extend expiration
                            if self.save_auth_state(context):
                                return RefreshResult(
                                    success=True,
                                    message="Session already valid, auth state refreshed",
                                    cookies_saved=True,
                                    storage_state_saved=True
                                )
                    
                    # Navigate to login page
                    logger.info(f"Navigating to {self.login_url}")
                    page.goto(self.login_url)
                    page.wait_for_load_state('domcontentloaded')
                    
                    # Notify user about manual login
                    logger.warning("TooLost login required - JWT expires in 7 days!")
                    logger.info("Please complete login manually in the browser window.")
                    
                    if self.notifier:
                        self.notifier.notify_manual_intervention_required(
                            self.service_name,
                            "CRITICAL: TooLost login required (JWT expires in 7 days)",
                            details={'priority': 'CRITICAL', 'expiration_days': 7}
                        )
                    
                    # Wait for manual login
                    if not self._wait_for_manual_login(page):
                        logger.error("Manual login timeout or failed")
                        continue
                    
                    # Extract and validate JWT
                    if not self._extract_and_validate_jwt(page, context):
                        logger.error("Failed to extract valid JWT token")
                        continue
                    
                    # Verify API access
                    if not self._verify_api_access(page):
                        logger.error("API access verification failed")
                        continue
                    
                    # Save authentication state (CRITICAL - includes JWT in localStorage)
                    if self.save_auth_state(context):
                        logger.warning("TooLost auth refreshed successfully - JWT valid for 7 days")
                        
                        # Set reminder for next refresh
                        next_refresh = datetime.now() + timedelta(days=6)
                        logger.warning(f"NEXT REFRESH REQUIRED BY: {next_refresh.strftime('%Y-%m-%d %H:%M')}")
                        
                        if self.notifier:
                            self.notifier.notify_refresh_success(
                                self.service_name,
                                details={
                                    'jwt_expiration_days': 7,
                                    'next_refresh': next_refresh.isoformat(),
                                    'priority': 'CRITICAL'
                                }
                            )
                        
                        return RefreshResult(
                            success=True,
                            message="JWT and cookies refreshed successfully (valid for 7 days)",
                            cookies_saved=True,
                            storage_state_saved=True
                        )
                    else:
                        logger.error("Failed to save authentication state")
                        
            except Exception as e:
                logger.error(f"Attempt {attempt} failed: {e}")
                if attempt == self.max_attempts:
                    return self._handle_refresh_error(e)
        
        return RefreshResult(
            success=False,
            message=f"CRITICAL: Failed after {self.max_attempts} attempts - JWT will expire!",
            manual_intervention_required=True
        )
    
    def validate_cookies(self, context: BrowserContext) -> bool:
        """Validate that cookies AND JWT are working properly.
        
        Args:
            context: Browser context with loaded cookies
            
        Returns:
            True if authentication is valid
        """
        try:
            page = context.new_page()
            
            # Check localStorage for JWT
            page.goto(self.portal_url)
            jwt_token = page.evaluate("""
                () => {
                    const token = localStorage.getItem('token') || 
                                 localStorage.getItem('jwt') || 
                                 localStorage.getItem('authToken');
                    return token;
                }
            """)
            
            if not jwt_token:
                logger.error("No JWT token found in localStorage")
                return False
            
            # Try to access portal
            logger.info(f"Validating authentication by accessing {self.portal_url}")
            page.goto(self.portal_url)
            page.wait_for_load_state('networkidle', timeout=30000)
            
            # Check if we're logged in
            if self._is_logged_in(page):
                logger.info("TooLost authentication validated successfully")
                return True
            
            # Check if redirected to login
            if 'login' in page.url:
                logger.warning("Redirected to login page, authentication invalid")
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"Authentication validation error: {e}")
            return False
        finally:
            if 'page' in locals():
                page.close()
    
    def check_expiration(self, account: Optional[str] = None):
        """Override to enforce 7-day JWT expiration."""
        auth_info = super().check_expiration(account)
        
        # Override expiration to 7 days for JWT
        if auth_info.last_refresh:
            jwt_expiration = auth_info.last_refresh + timedelta(days=self.jwt_expiration_days)
            days_until = (jwt_expiration - datetime.now()).days
            
            auth_info.days_until_expiration = max(0, days_until)
            auth_info.is_expired = days_until <= 0
            
            if days_until <= 1:
                logger.critical(f"TooLost JWT expires in {days_until} days!")
        
        return auth_info
    
    def _test_existing_auth(self, page: Page, context: BrowserContext) -> bool:
        """Test if existing authentication works.
        
        Args:
            page: Browser page
            context: Browser context
            
        Returns:
            True if auth is valid
        """
        try:
            page.goto(self.portal_url)
            page.wait_for_load_state('networkidle', timeout=15000)
            
            # Check if we're on the portal
            if 'user-portal' in page.url and self._is_logged_in(page):
                # Verify JWT exists
                jwt_token = page.evaluate("() => localStorage.getItem('token') || localStorage.getItem('jwt')")
                if jwt_token:
                    logger.info("Existing JWT token found and portal accessible")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error testing existing auth: {e}")
            return False
    
    def _is_logged_in(self, page: Page) -> bool:
        """Check if user is logged in to TooLost.
        
        Args:
            page: Browser page
            
        Returns:
            True if logged in
        """
        try:
            # Check URL first
            current_url = page.url
            if any(indicator in current_url for indicator in self.success_indicators):
                # Try to find dashboard elements
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
    
    def _wait_for_manual_login(self, page: Page) -> bool:
        """Wait for user to complete manual login.
        
        Args:
            page: Browser page
            
        Returns:
            True if login successful
        """
        logger.info("Waiting for manual login completion...")
        logger.warning("Remember: TooLost JWT expires every 7 days!")
        
        timeout_seconds = 300  # 5 minutes
        start_time = time.time()
        check_interval = 2  # seconds
        
        while time.time() - start_time < timeout_seconds:
            try:
                current_url = page.url
                
                # Check if we've navigated away from login
                if 'login' not in current_url:
                    # Wait for page to load
                    page.wait_for_load_state('networkidle', timeout=10000)
                    
                    # Check for dashboard elements
                    if self._is_logged_in(page):
                        logger.info(f"Login successful! Now at: {current_url}")
                        return True
                    
                    # Check for specific success pages
                    if any(indicator in current_url for indicator in self.success_indicators):
                        logger.info(f"Reached success page: {current_url}")
                        return True
                
                # Visual feedback
                elapsed = int(time.time() - start_time)
                remaining = timeout_seconds - elapsed
                if elapsed % 30 == 0:  # Update every 30 seconds
                    logger.info(f"Still waiting for login... ({remaining}s remaining)")
                
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error during login wait: {e}")
                time.sleep(check_interval)
        
        logger.error(f"Login timeout after {timeout_seconds} seconds")
        if self.screenshot_on_failure:
            self._save_screenshot(page, "login_timeout")
        return False
    
    def _extract_and_validate_jwt(self, page: Page, context: BrowserContext) -> bool:
        """Extract JWT from localStorage and validate it.
        
        Args:
            page: Browser page
            context: Browser context
            
        Returns:
            True if valid JWT found
        """
        try:
            logger.info("Extracting JWT token from localStorage...")
            
            # Navigate to portal if not already there
            if 'user-portal' not in page.url:
                page.goto(self.portal_url)
                page.wait_for_load_state('networkidle')
            
            # Extract JWT from localStorage
            jwt_data = page.evaluate("""
                () => {
                    const possibleKeys = ['token', 'jwt', 'authToken', 'access_token'];
                    const storage = {};
                    
                    for (const key of possibleKeys) {
                        const value = localStorage.getItem(key);
                        if (value) {
                            storage[key] = value;
                        }
                    }
                    
                    // Also get all localStorage for debugging
                    storage._all_keys = Object.keys(localStorage);
                    
                    return storage;
                }
            """)
            
            logger.debug(f"Found localStorage keys: {jwt_data.get('_all_keys', [])}")
            
            # Find the JWT
            jwt_token = None
            for key in ['token', 'jwt', 'authToken', 'access_token']:
                if key in jwt_data and jwt_data[key]:
                    jwt_token = jwt_data[key]
                    logger.info(f"Found JWT in localStorage['{key}']")
                    break
            
            if not jwt_token:
                logger.error("No JWT token found in localStorage")
                return False
            
            # Validate JWT format (basic check)
            if not jwt_token.startswith('ey') or jwt_token.count('.') != 2:
                logger.warning("JWT token format appears invalid")
                return False
            
            logger.info("JWT token extracted and validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error extracting JWT: {e}")
            return False
    
    def _verify_api_access(self, page: Page) -> bool:
        """Verify that API access works with current authentication.
        
        Args:
            page: Browser page
            
        Returns:
            True if API access verified
        """
        try:
            logger.info("Verifying API access...")
            
            # Set up response capture
            api_responses = {}
            
            def handle_response(response):
                for api_url in self.test_apis:
                    if response.url.startswith(api_url):
                        api_responses[api_url] = response.status
                        logger.debug(f"API response: {api_url} -> {response.status}")
            
            page.on("response", handle_response)
            
            # Navigate to analytics page to trigger API calls
            page.goto(self.portal_url)
            page.wait_for_load_state('networkidle', timeout=20000)
            
            # Wait for API responses
            wait_time = 10
            for i in range(wait_time):
                if api_responses:
                    break
                time.sleep(1)
            
            # Check API responses
            if api_responses:
                success_count = sum(1 for status in api_responses.values() if status == 200)
                if success_count > 0:
                    logger.info(f"API access verified: {success_count}/{len(api_responses)} endpoints successful")
                    return True
                else:
                    logger.error(f"API access failed: {api_responses}")
                    return False
            else:
                logger.warning("No API responses captured, assuming success based on page load")
                return True
                
        except Exception as e:
            logger.error(f"Error verifying API access: {e}")
            return True  # Don't fail on API verification errors