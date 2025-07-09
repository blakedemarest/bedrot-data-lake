"""Base refresh strategy for cookie management.

This module provides the abstract base class for all service-specific
cookie refresh strategies, with common functionality for browser automation,
cookie management, and error handling.
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from contextlib import contextmanager

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Cookie
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from ..storage import CookieStorageManager, AuthStateInfo
from ..notifier import CookieRefreshNotifier, NotificationLevel

logger = logging.getLogger(__name__)


class RefreshResult:
    """Container for refresh operation results."""
    
    def __init__(self, success: bool, message: str, 
                 cookies_saved: bool = False,
                 storage_state_saved: bool = False,
                 manual_intervention_required: bool = False,
                 error: Optional[Exception] = None):
        """Initialize refresh result.
        
        Args:
            success: Whether refresh was successful
            message: Result message
            cookies_saved: Whether cookies were saved
            storage_state_saved: Whether storage state was saved
            manual_intervention_required: Whether manual action is needed
            error: Exception if any
        """
        self.success = success
        self.message = message
        self.cookies_saved = cookies_saved
        self.storage_state_saved = storage_state_saved
        self.manual_intervention_required = manual_intervention_required
        self.error = error
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'success': self.success,
            'message': self.message,
            'cookies_saved': self.cookies_saved,
            'storage_state_saved': self.storage_state_saved,
            'manual_intervention_required': self.manual_intervention_required,
            'error': str(self.error) if self.error else None,
            'timestamp': self.timestamp.isoformat()
        }


class BaseRefreshStrategy(ABC):
    """Abstract base class for cookie refresh strategies."""
    
    def __init__(self, 
                 service_name: str,
                 storage_manager: CookieStorageManager,
                 notifier: Optional[CookieRefreshNotifier] = None,
                 config: Optional[Dict[str, Any]] = None):
        """Initialize base refresh strategy.
        
        Args:
            service_name: Name of the service (e.g., 'spotify', 'tiktok')
            storage_manager: Cookie storage manager instance
            notifier: Optional notifier for alerts
            config: Service-specific configuration
        """
        self.service_name = service_name
        self.storage_manager = storage_manager
        self.notifier = notifier
        self.config = config or {}
        
        # Browser settings
        self.headless = self.config.get('browser_headless', False)
        self.browser_timeout = self.config.get('browser_timeout_seconds', 300) * 1000  # Convert to ms
        self.screenshot_on_failure = self.config.get('screenshot_on_failure', True)
        self.screenshots_dir = Path(self.config.get('screenshots_dir', 'logs/screenshots'))
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Authentication settings
        self.auth_url = self.config.get('auth_url', '')
        self.requires_2fa = self.config.get('requires_2fa', False)
        self.max_attempts = self.config.get('max_refresh_attempts', 3)
        
    @abstractmethod
    def refresh_cookies(self, account: Optional[str] = None) -> RefreshResult:
        """Refresh cookies for the service.
        
        Args:
            account: Optional account identifier for multi-account services
            
        Returns:
            RefreshResult object
        """
        pass
    
    @abstractmethod
    def validate_cookies(self, context: BrowserContext) -> bool:
        """Validate that cookies are working properly.
        
        Args:
            context: Browser context with loaded cookies
            
        Returns:
            True if cookies are valid
        """
        pass
    
    def check_expiration(self, account: Optional[str] = None) -> AuthStateInfo:
        """Check cookie expiration status.
        
        Args:
            account: Optional account identifier
            
        Returns:
            AuthStateInfo object
        """
        return self.storage_manager.get_expiration_info(self.service_name, account)
    
    def needs_refresh(self, account: Optional[str] = None, 
                     warning_days: int = 7) -> Tuple[bool, Optional[str]]:
        """Check if cookies need refreshing.
        
        Args:
            account: Optional account identifier
            warning_days: Days before expiration to trigger refresh
            
        Returns:
            Tuple of (needs_refresh, reason)
        """
        auth_info = self.check_expiration(account)
        
        if auth_info.is_expired:
            return True, "Cookies are expired"
        
        if auth_info.days_until_expiration is not None:
            if auth_info.days_until_expiration <= warning_days:
                return True, f"Cookies expire in {auth_info.days_until_expiration} days"
        
        if auth_info.cookie_count == 0:
            return True, "No cookies found"
        
        return False, None
    
    @contextmanager
    def create_browser_context(self, existing_auth: Optional[Dict[str, Any]] = None):
        """Create a browser context with proper configuration.
        
        Args:
            existing_auth: Existing authentication state to load
            
        Yields:
            Tuple of (browser, context, page)
        """
        browser = None
        context = None
        page = None
        
        try:
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(
                    headless=self.headless,
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                # Create context with existing auth if available
                context_args = {
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'viewport': {'width': 1920, 'height': 1080},
                    'locale': 'en-US'
                }
                
                if existing_auth:
                    if 'cookies' in existing_auth:
                        context = browser.new_context(**context_args)
                        context.add_cookies(existing_auth['cookies'])
                    else:
                        # Full storage state
                        context = browser.new_context(storage_state=existing_auth, **context_args)
                else:
                    context = browser.new_context(**context_args)
                
                # Set default timeout
                context.set_default_timeout(self.browser_timeout)
                
                # Create page
                page = context.new_page()
                
                # Stealth mode settings
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)
                
                yield browser, context, page
                
        except Exception as e:
            logger.error(f"Error creating browser context: {e}")
            if page and self.screenshot_on_failure:
                self._save_screenshot(page, "browser_error")
            raise
        finally:
            if page:
                page.close()
            if context:
                context.close()
            if browser:
                browser.close()
    
    def wait_for_manual_login(self, page: Page, success_url_pattern: str,
                             timeout_seconds: int = 300) -> bool:
        """Wait for user to complete manual login.
        
        Args:
            page: Browser page
            success_url_pattern: URL pattern that indicates successful login
            timeout_seconds: Maximum time to wait
            
        Returns:
            True if login successful
        """
        logger.info(f"Waiting for manual login on {self.service_name}...")
        logger.info(f"Please complete login in the browser window (timeout: {timeout_seconds}s)")
        
        if self.notifier:
            self.notifier.notify_manual_intervention_required(
                self.service_name,
                "Please complete login in the browser window"
            )
        
        try:
            # Wait for navigation to success URL
            page.wait_for_url(success_url_pattern, timeout=timeout_seconds * 1000)
            logger.info("Login successful!")
            return True
            
        except PlaywrightTimeout:
            logger.error(f"Login timeout after {timeout_seconds} seconds")
            return False
        except Exception as e:
            logger.error(f"Error during manual login: {e}")
            return False
    
    def wait_for_2fa(self, page: Page, timeout_seconds: int = 120) -> bool:
        """Wait for user to complete 2FA.
        
        Args:
            page: Browser page
            timeout_seconds: Maximum time to wait for 2FA
            
        Returns:
            True if 2FA completed
        """
        logger.info("2FA required. Please complete in the browser window...")
        
        if self.notifier:
            self.notifier.notify_manual_intervention_required(
                self.service_name,
                "2FA verification required"
            )
        
        try:
            # This should be overridden by specific strategies
            # Default behavior is just to wait
            page.wait_for_timeout(timeout_seconds * 1000)
            return True
        except Exception as e:
            logger.error(f"Error during 2FA: {e}")
            return False
    
    def save_auth_state(self, context: BrowserContext, account: Optional[str] = None) -> bool:
        """Save authentication state from browser context.
        
        Args:
            context: Browser context with authenticated session
            account: Optional account identifier
            
        Returns:
            True if saved successfully
        """
        try:
            # Get storage state (includes cookies, localStorage, etc.)
            storage_state = context.storage_state()
            
            # Save full storage state
            self.storage_manager.save_storage_state(
                self.service_name, 
                storage_state,
                account
            )
            
            # Also save cookies in legacy format
            cookies = context.cookies()
            if cookies:
                self.storage_manager.save_cookies(
                    self.service_name,
                    cookies,
                    account
                )
            
            logger.info(f"Saved authentication state for {self.service_name}" + 
                       (f" ({account})" if account else ""))
            return True
            
        except Exception as e:
            logger.error(f"Failed to save auth state: {e}")
            return False
    
    def load_existing_auth(self, account: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load existing authentication state.
        
        Args:
            account: Optional account identifier
            
        Returns:
            Authentication state dict or None
        """
        return self.storage_manager.load_auth_state(self.service_name, account)
    
    def backup_current_auth(self, account: Optional[str] = None) -> Tuple[Optional[Path], Optional[Path]]:
        """Backup current authentication state.
        
        Args:
            account: Optional account identifier
            
        Returns:
            Tuple of backup paths
        """
        return self.storage_manager.backup_auth_state(self.service_name, account)
    
    def _save_screenshot(self, page: Page, suffix: str = ""):
        """Save screenshot for debugging.
        
        Args:
            page: Browser page
            suffix: Optional suffix for filename
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.service_name}_{suffix}_{timestamp}.png"
            filepath = self.screenshots_dir / filename
            page.screenshot(path=str(filepath))
            logger.info(f"Screenshot saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save screenshot: {e}")
    
    def _handle_refresh_error(self, error: Exception, account: Optional[str] = None) -> RefreshResult:
        """Handle refresh error with proper logging and notification.
        
        Args:
            error: Exception that occurred
            account: Optional account identifier
            
        Returns:
            RefreshResult with error details
        """
        error_msg = str(error)
        logger.error(f"Cookie refresh failed for {self.service_name}: {error_msg}")
        
        if self.notifier:
            self.notifier.notify_refresh_failed(
                self.service_name,
                error_msg,
                account,
                details={'error_type': type(error).__name__}
            )
        
        return RefreshResult(
            success=False,
            message=f"Refresh failed: {error_msg}",
            error=error,
            manual_intervention_required=True
        )
    
    def _log_refresh_attempt(self, attempt: int, max_attempts: int, account: Optional[str] = None):
        """Log refresh attempt information.
        
        Args:
            attempt: Current attempt number
            max_attempts: Maximum attempts allowed
            account: Optional account identifier
        """
        service_id = f"{self.service_name}" + (f"/{account}" if account else "")
        logger.info(f"Cookie refresh attempt {attempt}/{max_attempts} for {service_id}")
        
        if self.notifier and attempt == 1:
            self.notifier.notify_refresh_started(self.service_name, account)