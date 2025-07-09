"""DistroKid cookie refresh strategy implementation.

This module implements the automated cookie refresh strategy for DistroKid,
using stored credentials for login automation and handling 2FA when required.
"""

import os
import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime

from playwright.sync_api import Page, BrowserContext, TimeoutError as PlaywrightTimeout

from .base import BaseRefreshStrategy, RefreshResult
from ..storage import CookieStorageManager
from ..notifier import CookieRefreshNotifier

logger = logging.getLogger(__name__)


class DistroKidRefreshStrategy(BaseRefreshStrategy):
    """Cookie refresh strategy for DistroKid."""
    
    def __init__(self, 
                 service_name: str,
                 storage_manager: CookieStorageManager,
                 notifier: Optional[CookieRefreshNotifier] = None,
                 config: Optional[Dict[str, Any]] = None):
        """Initialize DistroKid refresh strategy.
        
        Args:
            service_name: Service name (should be 'distrokid')
            storage_manager: Cookie storage manager instance
            notifier: Optional notifier for alerts
            config: Service-specific configuration
        """
        super().__init__(service_name, storage_manager, notifier, config)
        
        # DistroKid specific settings
        self.login_url = 'https://distrokid.com/signin'
        self.dashboard_url = 'https://distrokid.com/stats/?data=streams'
        self.success_indicators = ['/dashboard', '/mymusic', '/stats']
        
        # Get credentials from environment
        self.email = os.environ.get('DK_EMAIL')
        self.password = os.environ.get('DK_PASSWORD')
        
    def refresh_cookies(self, account: Optional[str] = None) -> RefreshResult:
        """Refresh cookies for DistroKid.
        
        Args:
            account: Not used for DistroKid (single account)
            
        Returns:
            RefreshResult object
        """
        # Validate credentials
        if not self.email or not self.password:
            error_msg = "DK_EMAIL and DK_PASSWORD must be set in environment variables"
            logger.error(error_msg)
            return RefreshResult(
                success=False,
                message=error_msg,
                manual_intervention_required=True
            )
        
        logger.info("Starting DistroKid cookie refresh...")
        
        # Backup current auth state
        self.backup_current_auth()
        
        # Try to refresh
        for attempt in range(1, self.max_attempts + 1):
            self._log_refresh_attempt(attempt, self.max_attempts)
            
            try:
                # Load existing auth state if available
                existing_auth = self.load_existing_auth()
                
                with self.create_browser_context(existing_auth) as (browser, context, page):
                    # Navigate to login page
                    logger.info(f"Navigating to {self.login_url}")
                    page.goto(self.login_url)
                    
                    # Check if already logged in
                    if self._is_logged_in(page):
                        logger.info("Already logged in, validating session...")
                        if self.validate_cookies(context):
                            # Save the current state
                            if self.save_auth_state(context):
                                return RefreshResult(
                                    success=True,
                                    message="Session already valid, cookies refreshed",
                                    cookies_saved=True,
                                    storage_state_saved=True
                                )
                    
                    # Perform login
                    if not self._perform_login(page):
                        continue
                    
                    # Wait for successful login
                    if not self._wait_for_dashboard(page):
                        continue
                    
                    # Validate cookies work
                    if not self.validate_cookies(context):
                        logger.error("Cookie validation failed after login")
                        continue
                    
                    # Save authentication state
                    if self.save_auth_state(context):
                        logger.info("DistroKid cookies refreshed successfully")
                        
                        if self.notifier:
                            self.notifier.notify_refresh_success(self.service_name)
                        
                        return RefreshResult(
                            success=True,
                            message="Cookies refreshed successfully",
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
            message=f"Failed after {self.max_attempts} attempts",
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
            
            # Try to access dashboard directly
            logger.info(f"Validating cookies by accessing {self.dashboard_url}")
            page.goto(self.dashboard_url)
            page.wait_for_load_state('networkidle', timeout=30000)
            
            # Check if redirected to login
            if 'login' in page.url or 'signin' in page.url:
                logger.warning("Redirected to login page, cookies invalid")
                return False
            
            # Check for dashboard elements
            try:
                page.wait_for_selector('body', timeout=5000)
                # Look for common dashboard elements
                if any(indicator in page.url for indicator in self.success_indicators):
                    logger.info("Dashboard access confirmed, cookies valid")
                    return True
            except PlaywrightTimeout:
                pass
            
            return False
            
        except Exception as e:
            logger.error(f"Cookie validation error: {e}")
            return False
        finally:
            if 'page' in locals():
                page.close()
    
    def _is_logged_in(self, page: Page) -> bool:
        """Check if already logged in.
        
        Args:
            page: Browser page
            
        Returns:
            True if logged in
        """
        try:
            # Check URL for dashboard indicators
            if any(indicator in page.url for indicator in self.success_indicators):
                return True
            
            # Wait a moment for any redirects
            page.wait_for_timeout(2000)
            
            # Check again after potential redirect
            return any(indicator in page.url for indicator in self.success_indicators)
            
        except Exception:
            return False
    
    def _perform_login(self, page: Page) -> bool:
        """Perform login with credentials.
        
        Args:
            page: Browser page
            
        Returns:
            True if login form submitted successfully
        """
        try:
            # Wait for login form
            logger.info("Waiting for login form...")
            page.wait_for_selector('input[type="email"]', timeout=10000)
            
            # Fill credentials
            logger.info("Filling login credentials...")
            page.fill('input[type="email"]', self.email)
            page.fill('input[type="password"]', self.password)
            
            # Take screenshot before submit
            if self.screenshot_on_failure:
                self._save_screenshot(page, "before_login")
            
            # Submit form
            logger.info("Submitting login form...")
            page.click('button[type="submit"]')
            
            return True
            
        except PlaywrightTimeout:
            logger.error("Login form not found")
            if self.screenshot_on_failure:
                self._save_screenshot(page, "login_timeout")
            return False
        except Exception as e:
            logger.error(f"Login failed: {e}")
            if self.screenshot_on_failure:
                self._save_screenshot(page, "login_error")
            return False
    
    def _wait_for_dashboard(self, page: Page) -> bool:
        """Wait for successful login and handle 2FA if needed.
        
        Args:
            page: Browser page
            
        Returns:
            True if login successful
        """
        logger.info("Waiting for login to complete...")
        
        # Check for 2FA
        start_time = time.time()
        timeout = 300  # 5 minutes for 2FA
        
        while time.time() - start_time < timeout:
            try:
                # Check if we're on the dashboard
                if any(indicator in page.url for indicator in self.success_indicators):
                    logger.info(f"Dashboard detected at {page.url}")
                    return True
                
                # Check for 2FA indicators
                if self._check_for_2fa(page):
                    logger.info("2FA detected, waiting for user to complete...")
                    if self.notifier:
                        self.notifier.notify_manual_intervention_required(
                            self.service_name,
                            "Please complete 2FA verification in the browser"
                        )
                    
                    # Wait for user to complete 2FA
                    if not self.wait_for_2fa(page, timeout_seconds=int(timeout - (time.time() - start_time))):
                        return False
                
                # Check for login errors
                try:
                    error_element = page.query_selector('.alert-danger, .error-message, [class*="error"]')
                    if error_element:
                        error_text = error_element.inner_text()
                        logger.error(f"Login error: {error_text}")
                        if self.screenshot_on_failure:
                            self._save_screenshot(page, "login_error")
                        return False
                except:
                    pass
                
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error waiting for dashboard: {e}")
                return False
        
        logger.error(f"Login timeout after {timeout} seconds")
        if self.screenshot_on_failure:
            self._save_screenshot(page, "login_timeout")
        return False
    
    def _check_for_2fa(self, page: Page) -> bool:
        """Check if 2FA is required.
        
        Args:
            page: Browser page
            
        Returns:
            True if 2FA detected
        """
        try:
            # Common 2FA indicators
            two_fa_selectors = [
                'input[name="code"]',
                'input[placeholder*="code"]',
                'input[placeholder*="2FA"]',
                'input[placeholder*="verification"]',
                '.two-factor',
                '[class*="2fa"]',
                'text="Two-Factor"',
                'text="Verification Code"',
                'text="Enter code"'
            ]
            
            for selector in two_fa_selectors:
                try:
                    if page.query_selector(selector):
                        return True
                except:
                    continue
            
            return False
            
        except Exception:
            return False
    
    def wait_for_2fa(self, page: Page, timeout_seconds: int = 120) -> bool:
        """Wait for user to complete 2FA.
        
        Args:
            page: Browser page
            timeout_seconds: Maximum time to wait for 2FA
            
        Returns:
            True if 2FA completed and dashboard reached
        """
        logger.info(f"Waiting up to {timeout_seconds} seconds for 2FA completion...")
        
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            try:
                # Check if we've reached the dashboard
                if any(indicator in page.url for indicator in self.success_indicators):
                    logger.info("2FA completed successfully")
                    return True
                
                # Wait a bit before checking again
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error during 2FA wait: {e}")
                return False
        
        logger.error("2FA timeout")
        return False