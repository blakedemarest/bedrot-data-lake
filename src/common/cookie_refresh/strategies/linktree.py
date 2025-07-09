"""Linktree cookie refresh strategy implementation.

This module implements the cookie refresh strategy for Linktree,
using standard cookie-based authentication with 30-day expiration.
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


class LinktreeRefreshStrategy(BaseRefreshStrategy):
    """Cookie refresh strategy for Linktree."""
    
    def __init__(self, 
                 service_name: str,
                 storage_manager: CookieStorageManager,
                 notifier: Optional[CookieRefreshNotifier] = None,
                 config: Optional[Dict[str, Any]] = None):
        """Initialize Linktree refresh strategy.
        
        Args:
            service_name: Name of the service (should be 'linktree')
            storage_manager: Cookie storage manager instance
            notifier: Optional notifier for alerts
            config: Service-specific configuration
        """
        super().__init__(service_name, storage_manager, notifier, config)
        
        # Linktree specific settings
        self.login_url = 'https://linktr.ee/login'
        self.dashboard_url = 'https://linktr.ee/admin'
        self.analytics_url = 'https://linktr.ee/admin/analytics'
        
        # Success indicators
        self.success_indicators = [
            'linktr.ee/admin',
            '/admin/analytics',
            '/admin/links',
            '/admin/appearance',
            '/admin/settings'
        ]
        
        # Logged in selectors
        self.logged_in_selectors = [
            '[data-testid="user-menu"]',
            '[data-testid="nav-user-avatar"]',
            '[aria-label="User menu"]',
            'button[aria-label*="account"]',
            'nav [class*="Avatar"]',
            'img[alt*="Profile"]',
            '[class*="UserMenu"]',
            '[class*="dashboard"]'
        ]
        
        # Login form selectors
        self.login_selectors = {
            'email': 'input[name="email"], input[type="email"], input[placeholder*="Email"]',
            'password': 'input[name="password"], input[type="password"], input[placeholder*="Password"]',
            'submit': 'button[type="submit"], button:has-text("Log in"), button:has-text("Sign in")'
        }
        
    def refresh_cookies(self, account: Optional[str] = None) -> RefreshResult:
        """Refresh cookies for Linktree.
        
        Args:
            account: Not used for Linktree (single account)
            
        Returns:
            RefreshResult object
        """
        logger.info("Starting Linktree cookie refresh...")
        
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
                        page.goto(self.dashboard_url)
                        page.wait_for_load_state('networkidle', timeout=15000)
                        
                        if self._is_logged_in(page):
                            logger.info("Existing authentication still valid")
                            if self.validate_cookies(context):
                                # Refresh the auth state
                                if self.save_auth_state(context):
                                    return RefreshResult(
                                        success=True,
                                        message="Session already valid, cookies refreshed",
                                        cookies_saved=True,
                                        storage_state_saved=True
                                    )
                    
                    # Navigate to login page
                    logger.info(f"Navigating to {self.login_url}")
                    page.goto(self.login_url)
                    page.wait_for_load_state('domcontentloaded')
                    
                    # Check if already logged in (might redirect to dashboard)
                    if self._check_auto_redirect(page):
                        if self.validate_cookies(context):
                            if self.save_auth_state(context):
                                return RefreshResult(
                                    success=True,
                                    message="Auto-redirected to dashboard, cookies refreshed",
                                    cookies_saved=True,
                                    storage_state_saved=True
                                )
                    
                    # Notify user about manual login
                    logger.info("Linktree login page loaded. Please complete login manually.")
                    
                    if self.notifier:
                        self.notifier.notify_manual_intervention_required(
                            self.service_name,
                            "Please complete Linktree login in the browser window"
                        )
                    
                    # Wait for manual login
                    if not self._wait_for_manual_login(page):
                        logger.error("Manual login timeout or failed")
                        continue
                    
                    # Verify successful login
                    if not self._verify_login_success(page, context):
                        logger.error("Login verification failed")
                        continue
                    
                    # Save authentication state
                    if self.save_auth_state(context):
                        logger.info("Linktree cookies refreshed successfully")
                        
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
            
            # Try to access dashboard
            logger.info(f"Validating cookies by accessing {self.dashboard_url}")
            page.goto(self.dashboard_url)
            page.wait_for_load_state('networkidle', timeout=30000)
            
            # Check if we're logged in
            if self._is_logged_in(page):
                logger.info("Linktree cookies validated successfully")
                return True
            
            # Check if redirected to login
            if 'login' in page.url or 'signin' in page.url:
                logger.warning("Redirected to login page, cookies invalid")
                return False
            
            # Try analytics page as secondary check
            logger.info("Trying analytics page for validation...")
            page.goto(self.analytics_url)
            page.wait_for_load_state('networkidle', timeout=15000)
            
            if 'analytics' in page.url and self._is_logged_in(page):
                logger.info("Analytics page accessible, cookies valid")
                return True
            
            logger.warning("Unable to verify login status")
            return False
            
        except Exception as e:
            logger.error(f"Cookie validation error: {e}")
            return False
        finally:
            if 'page' in locals():
                page.close()
    
    def _is_logged_in(self, page: Page) -> bool:
        """Check if user is logged in to Linktree.
        
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
            
            # Check for login page indicators (negative check)
            if 'login' in current_url or 'signin' in current_url:
                return False
            
            # Check for dashboard-specific elements
            dashboard_elements = [
                'text="Analytics"',
                'text="Links"',
                'text="Appearance"',
                'text="Settings"'
            ]
            
            for element in dashboard_elements:
                try:
                    if page.query_selector(element):
                        logger.debug(f"Found dashboard element: {element}")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return False
    
    def _check_auto_redirect(self, page: Page) -> bool:
        """Check if we were auto-redirected to dashboard (already logged in).
        
        Args:
            page: Browser page
            
        Returns:
            True if auto-redirected to dashboard
        """
        try:
            # Wait a moment for potential redirect
            page.wait_for_timeout(3000)
            
            current_url = page.url
            if 'login' not in current_url and any(indicator in current_url for indicator in self.success_indicators):
                logger.info(f"Auto-redirected to dashboard: {current_url}")
                return True
            
            return False
            
        except Exception:
            return False
    
    def _wait_for_manual_login(self, page: Page) -> bool:
        """Wait for user to complete manual login.
        
        Args:
            page: Browser page
            
        Returns:
            True if login successful
        """
        logger.info("Waiting for manual login completion...")
        logger.info("Please enter your Linktree credentials in the browser window.")
        
        timeout_seconds = 300  # 5 minutes
        start_time = time.time()
        check_interval = 2  # seconds
        
        # Check if login form is visible
        try:
            email_input = page.query_selector(self.login_selectors['email'])
            if email_input:
                logger.info("Login form detected. Waiting for submission...")
        except:
            pass
        
        while time.time() - start_time < timeout_seconds:
            try:
                current_url = page.url
                
                # Check if we've navigated away from login
                if 'login' not in current_url and 'signin' not in current_url:
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
                
                # Check for login errors
                try:
                    error_selectors = [
                        '[role="alert"]',
                        '.error-message',
                        '[class*="error"]',
                        'text="Invalid email or password"',
                        'text="Please try again"'
                    ]
                    
                    for selector in error_selectors:
                        error_element = page.query_selector(selector)
                        if error_element:
                            error_text = error_element.inner_text()
                            logger.warning(f"Login error detected: {error_text}")
                            break
                except:
                    pass
                
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
    
    def _verify_login_success(self, page: Page, context: BrowserContext) -> bool:
        """Verify that login was successful and we can access Linktree services.
        
        Args:
            page: Browser page
            context: Browser context
            
        Returns:
            True if login verified
        """
        try:
            logger.info("Verifying login success...")
            
            # Navigate to dashboard if not already there
            if '/admin' not in page.url:
                logger.info(f"Navigating to {self.dashboard_url} for verification...")
                page.goto(self.dashboard_url)
                page.wait_for_load_state('networkidle', timeout=20000)
            
            # Check if we're on the dashboard
            if '/admin' in page.url and self._is_logged_in(page):
                logger.info("Successfully accessed Linktree dashboard")
                
                # Try to access analytics as additional verification
                logger.info("Verifying analytics access...")
                page.goto(self.analytics_url)
                page.wait_for_load_state('networkidle', timeout=15000)
                
                if 'analytics' in page.url:
                    logger.info("Analytics page accessible, login fully verified")
                    return True
                else:
                    # Dashboard access is enough
                    logger.info("Dashboard accessible, login verified")
                    return True
            
            logger.error("Login verification failed - unable to access dashboard")
            if self.screenshot_on_failure:
                self._save_screenshot(page, "verification_failed")
            return False
            
        except Exception as e:
            logger.error(f"Error during login verification: {e}")
            if self.screenshot_on_failure:
                self._save_screenshot(page, "verification_error")
            return False