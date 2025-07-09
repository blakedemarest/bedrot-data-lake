"""Main cookie refresh orchestrator.

This module coordinates the cookie refresh process across all configured
services, managing priorities, scheduling, and error handling.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
import importlib
import traceback

from .config import CookieRefreshConfig
from .storage import CookieStorageManager, AuthStateInfo
from .notifier import CookieRefreshNotifier
from .strategies.base import BaseRefreshStrategy, RefreshResult
from .service_validator import ServiceURLValidator, validate_service_strategy

logger = logging.getLogger(__name__)


class ServiceRefreshInfo:
    """Container for service refresh information."""
    
    def __init__(self, service: str, strategy_class: Optional[Type[BaseRefreshStrategy]] = None,
                 accounts: Optional[List[str]] = None):
        """Initialize service refresh info.
        
        Args:
            service: Service name
            strategy_class: Strategy class for this service
            accounts: List of accounts for multi-account services
        """
        self.service = service
        self.strategy_class = strategy_class
        self.accounts = accounts or []
        self.last_attempt: Optional[datetime] = None
        self.last_result: Optional[RefreshResult] = None
        self.attempts_today = 0


class CookieRefresher:
    """Main orchestrator for cookie refresh operations."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize cookie refresher.
        
        Args:
            config_path: Optional path to configuration file
        """
        # Load configuration
        self.config = CookieRefreshConfig(config_path)
        
        # Initialize components
        self.storage_manager = CookieStorageManager(
            base_path=self.config.get_path('cookies_dir'),
            backup_path=self.config.get_path('backup_dir')
        )
        
        self.notifier = CookieRefreshNotifier(
            self.config.get_notification_config()
        )
        
        # Initialize URL validator
        self.url_validator = ServiceURLValidator()
        
        # Track service information
        self.services: Dict[str, ServiceRefreshInfo] = {}
        self._load_service_strategies()
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging for the refresher."""
        log_path = self.config.get_path('logs_dir') / 'cookie_refresh.log'
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    def _load_service_strategies(self):
        """Load service-specific refresh strategies."""
        for service in self.config.get_enabled_services():
            service_config = self.config.get_service_config(service)
            if not service_config:
                continue
            
            # Get accounts if multi-account service
            accounts = service_config.get('accounts', [])
            
            # Try to load strategy class
            strategy_class = self._get_strategy_class(service, service_config)
            
            self.services[service] = ServiceRefreshInfo(
                service=service,
                strategy_class=strategy_class,
                accounts=accounts
            )
    
    def _get_strategy_class(self, service: str, 
                           service_config: Dict[str, Any]) -> Optional[Type[BaseRefreshStrategy]]:
        """Get strategy class for a service.
        
        Args:
            service: Service name
            service_config: Service configuration
            
        Returns:
            Strategy class or None if not found
        """
        strategy_name = service_config.get('refresh_strategy', service)
        
        # Try to import service-specific strategy
        try:
            module = importlib.import_module(
                f'.strategies.{strategy_name}',
                package='common.cookie_refresh'
            )
            
            # Look for strategy class
            class_name = f"{strategy_name.title().replace('_', '')}RefreshStrategy"
            if hasattr(module, class_name):
                return getattr(module, class_name)
            
            # Try alternate naming
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, BaseRefreshStrategy) and 
                    attr != BaseRefreshStrategy):
                    return attr
                    
        except ImportError as e:
            logger.warning(f"Strategy module not found for {service}: {e}")
        except Exception as e:
            logger.error(f"Error loading strategy for {service}: {e}")
        
        return None
    
    def check_all_services(self) -> List[AuthStateInfo]:
        """Check expiration status for all services.
        
        Returns:
            List of AuthStateInfo objects
        """
        logger.info("Checking cookie status for all services...")
        status_list = self.storage_manager.get_all_services_status()
        
        # Log summary
        expired = sum(1 for s in status_list if s.is_expired)
        critical = sum(1 for s in status_list if s.status == "CRITICAL")
        warning = sum(1 for s in status_list if s.status == "WARNING")
        
        logger.info(f"Cookie status summary: {len(status_list)} services, "
                   f"{expired} expired, {critical} critical, {warning} warnings")
        
        # Send notification
        self.notifier.notify_all_services_status([s.__dict__ for s in status_list])
        
        return status_list
    
    def refresh_service(self, service: str, account: Optional[str] = None,
                       force: bool = False) -> RefreshResult:
        """Refresh cookies for a specific service.
        
        Args:
            service: Service name
            account: Optional account identifier
            force: Force refresh even if not needed
            
        Returns:
            RefreshResult object
        """
        if service not in self.services:
            return RefreshResult(
                success=False,
                message=f"Service {service} not configured or enabled"
            )
        
        service_info = self.services[service]
        
        # Check if strategy is available
        if not service_info.strategy_class:
            logger.warning(f"No refresh strategy available for {service}")
            return RefreshResult(
                success=False,
                message=f"No refresh strategy implemented for {service}",
                manual_intervention_required=True
            )
        
        # Create strategy instance
        service_config = self.config.get_service_config(service)
        general_config = {
            'browser_headless': self.config.get_general_setting('browser_headless'),
            'browser_timeout_seconds': self.config.get_general_setting('browser_timeout_seconds'),
            'screenshot_on_failure': self.config.get_general_setting('screenshot_on_failure'),
            'screenshots_dir': str(self.config.get_path('screenshots_dir')),
            'max_refresh_attempts': self.config.get_general_setting('max_refresh_attempts')
        }
        
        # Merge configurations
        config = {**general_config, **service_config}
        
        strategy = service_info.strategy_class(
            service_name=service,
            storage_manager=self.storage_manager,
            notifier=self.notifier,
            config=config
        )
        
        # Validate strategy URLs before proceeding
        try:
            validate_service_strategy(service, strategy)
            logger.info(f"✅ URL validation passed for {service}")
        except ValueError as e:
            logger.error(f"❌ URL validation failed for {service}: {e}")
            return RefreshResult(
                success=False,
                message=f"Configuration error: {str(e)}",
                manual_intervention_required=True
            )
        
        # Check if refresh is needed
        if not force:
            needs_refresh, reason = strategy.needs_refresh(
                account, 
                self.config.get_general_setting('expiration_warning_days', 7)
            )
            
            if not needs_refresh:
                logger.info(f"No refresh needed for {service}" + 
                           (f" ({account})" if account else ""))
                return RefreshResult(
                    success=True,
                    message="Cookies are still valid"
                )
        
        # Perform refresh
        logger.info(f"Starting cookie refresh for {service}" + 
                   (f" ({account})" if account else ""))
        
        try:
            result = strategy.refresh_cookies(account)
            
            # Update service info
            service_info.last_attempt = datetime.now()
            service_info.last_result = result
            service_info.attempts_today += 1
            
            # Send notifications
            if result.success:
                self.notifier.notify_refresh_success(
                    service, account,
                    details={
                        'cookies_saved': result.cookies_saved,
                        'storage_state_saved': result.storage_state_saved
                    }
                )
            elif result.manual_intervention_required:
                self.notifier.notify_manual_intervention_required(
                    service,
                    result.message,
                    account
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error refreshing {service}: {e}")
            logger.debug(traceback.format_exc())
            
            return RefreshResult(
                success=False,
                message=f"Unexpected error: {str(e)}",
                error=e,
                manual_intervention_required=True
            )
    
    def refresh_all_needed(self, force: bool = False) -> Dict[str, List[RefreshResult]]:
        """Refresh all services that need it.
        
        Args:
            force: Force refresh all services
            
        Returns:
            Dictionary mapping service names to list of results
        """
        logger.info("Starting refresh check for all services...")
        results = {}
        
        # Check all services
        status_list = self.check_all_services()
        
        # Group by service
        service_statuses = {}
        for status in status_list:
            parts = status.service.split('/')
            service = parts[0]
            account = parts[1] if len(parts) > 1 else None
            
            if service not in service_statuses:
                service_statuses[service] = []
            service_statuses[service].append((account, status))
        
        # Process each service
        for service in self.config.get_enabled_services():
            if service not in self.services:
                continue
            
            results[service] = []
            
            # Get all accounts for this service
            accounts_to_refresh = []
            
            if service in service_statuses:
                for account, status in service_statuses[service]:
                    if force or status.is_expired or status.status in ["CRITICAL", "WARNING"]:
                        accounts_to_refresh.append(account)
            elif force:
                # If forcing and no status found, try to refresh anyway
                accounts_to_refresh = self.services[service].accounts or [None]
            
            # Refresh each account
            for account in accounts_to_refresh:
                logger.info(f"Refreshing {service}" + (f" ({account})" if account else ""))
                result = self.refresh_service(service, account, force)
                results[service].append(result)
                
                # Add delay between accounts to avoid rate limiting
                if len(accounts_to_refresh) > 1:
                    import time
                    time.sleep(5)
        
        # Log summary
        total_attempts = sum(len(r) for r in results.values())
        successful = sum(1 for r in results.values() for res in r if res.success)
        failed = total_attempts - successful
        
        logger.info(f"Refresh complete: {successful} successful, {failed} failed out of {total_attempts} attempts")
        
        return results
    
    def run_check_only(self) -> List[AuthStateInfo]:
        """Run check-only mode without refreshing.
        
        Returns:
            List of service status information
        """
        logger.info("Running in check-only mode...")
        return self.check_all_services()
    
    def get_service_status(self, service: str) -> Optional[ServiceRefreshInfo]:
        """Get current status for a service.
        
        Args:
            service: Service name
            
        Returns:
            ServiceRefreshInfo or None
        """
        return self.services.get(service)


def main():
    """Main entry point for cookie refresh script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='BEDROT Cookie Refresh System')
    parser.add_argument('--service', help='Refresh specific service only')
    parser.add_argument('--account', help='Account for multi-account services')
    parser.add_argument('--force', action='store_true', help='Force refresh even if not needed')
    parser.add_argument('--check-only', action='store_true', help='Check status without refreshing')
    parser.add_argument('--config', help='Path to configuration file')
    
    args = parser.parse_args()
    
    # Create refresher
    refresher = CookieRefresher(args.config)
    
    # Execute based on arguments
    if args.check_only:
        status_list = refresher.run_check_only()
        
        # Print status table
        print("\nCookie Status Summary")
        print("=" * 80)
        print(f"{'Service':<20} {'Status':<10} {'Last Refresh':<20} {'Days Until Expiry':<15}")
        print("-" * 80)
        
        for status in status_list:
            last_refresh = status.last_refresh.strftime('%Y-%m-%d %H:%M') if status.last_refresh != datetime.min else 'Never'
            days_left = str(status.days_until_expiration) if status.days_until_expiration is not None else 'N/A'
            
            print(f"{status.service:<20} {status.status:<10} {last_refresh:<20} {days_left:<15}")
        
        print("=" * 80)
        
    elif args.service:
        # Refresh specific service
        result = refresher.refresh_service(args.service, args.account, args.force)
        
        print(f"\nRefresh result for {args.service}:")
        print(f"Success: {result.success}")
        print(f"Message: {result.message}")
        
        if not result.success:
            sys.exit(1)
            
    else:
        # Refresh all needed
        results = refresher.refresh_all_needed(args.force)
        
        # Print results
        print("\nRefresh Results")
        print("=" * 60)
        
        for service, service_results in results.items():
            for result in service_results:
                status = "✓" if result.success else "✗"
                print(f"{status} {service}: {result.message}")
        
        print("=" * 60)
        
        # Exit with error if any failed
        if any(not r.success for results_list in results.values() for r in results_list):
            sys.exit(1)


if __name__ == '__main__':
    main()