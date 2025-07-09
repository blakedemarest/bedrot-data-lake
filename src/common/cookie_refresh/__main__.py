#!/usr/bin/env python3
"""Command-line interface for cookie refresh system."""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from common.cookie_refresh.storage import CookieStorageManager
from common.cookie_refresh.config import CookieRefreshConfig
from common.cookie_refresh.refresher import CookieRefresher
from common.cookie_refresh.notifier import CookieRefreshNotifier

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CookieRefreshCLI:
    """Command-line interface for cookie refresh system."""
    
    def __init__(self):
        """Initialize CLI."""
        self.config = CookieRefreshConfig()
        self.storage = CookieStorageManager(self.config.get_path('cookies_dir'))
        self.refresher = CookieRefresher()
        self.notifier = CookieRefreshNotifier(self.config)
    
    def check_status(self, service=None):
        """Check cookie status for all or specific service."""
        print("\n=== Cookie Status Check ===\n")
        
        if service:
            # Check specific service
            status = self.storage.get_expiration_info(service)
            self._print_status(status)
        else:
            # Check all services
            statuses = self.storage.get_all_services_status()
            
            if not statuses:
                print("No services with stored cookies found.")
                return 0
            
            # Sort by status priority (expired first, then by days left)
            statuses.sort(key=lambda s: (
                0 if s.is_expired else 1,
                s.days_until_expiration or 999
            ))
            
            for status in statuses:
                self._print_status(status)
        
        return 0
    
    def _print_status(self, status):
        """Print formatted status for a service."""
        status_emoji = {
            'EXPIRED': '❌',
            'CRITICAL': '⚠️',
            'WARNING': '⚡',
            'VALID': '✅',
            'UNKNOWN': '❓'
        }
        
        emoji = status_emoji.get(status.status, '❓')
        days_text = f"{status.days_until_expiration} days" if status.days_until_expiration else "unknown"
        
        print(f"{emoji} {status.service}:")
        print(f"   Status: {status.status}")
        print(f"   Last refresh: {status.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Expires in: {days_text}")
        print(f"   Cookie count: {status.cookie_count}")
        print()
    
    def refresh_cookies(self, service=None, interactive=True):
        """Refresh cookies for services."""
        print("\n=== Cookie Refresh ===\n")
        
        # Determine which services need refresh
        if service:
            services_to_refresh = [service]
        else:
            # Check all services
            statuses = self.storage.get_all_services_status()
            services_to_refresh = []
            
            for status in statuses:
                if status.is_expired:
                    services_to_refresh.append(status.service.split('/')[0])
                elif status.days_until_expiration and status.days_until_expiration <= self.config.get_general_setting('expiration_critical_days', 3):
                    services_to_refresh.append(status.service.split('/')[0])
        
        if not services_to_refresh:
            print("All cookies are up to date!")
            return 0
        
        print(f"Services needing refresh: {', '.join(services_to_refresh)}\n")
        
        if interactive:
            response = input("Proceed with refresh? (y/n): ")
            if response.lower() != 'y':
                print("Refresh cancelled.")
                return 1
        
        # Refresh each service
        success_count = 0
        for service_name in services_to_refresh:
            print(f"\nRefreshing {service_name}...")
            try:
                success = self.refresher.refresh_service(service_name)
                if success:
                    print(f"✅ Successfully refreshed {service_name}")
                    success_count += 1
                else:
                    print(f"❌ Failed to refresh {service_name}")
            except Exception as e:
                print(f"❌ Error refreshing {service_name}: {e}")
                logger.exception(f"Error refreshing {service_name}")
        
        # Send notification summary
        self.notifier.send_refresh_summary(services_to_refresh, success_count)
        
        print(f"\nRefresh complete: {success_count}/{len(services_to_refresh)} successful")
        return 0 if success_count == len(services_to_refresh) else 1
    
    def backup_cookies(self, service=None):
        """Backup cookies for services."""
        print("\n=== Cookie Backup ===\n")
        
        if service:
            services = [service]
        else:
            # Backup all services
            statuses = self.storage.get_all_services_status()
            services = [s.service.split('/')[0] for s in statuses]
        
        for service_name in services:
            try:
                cookie_backup, state_backup = self.storage.backup_auth_state(service_name)
                if cookie_backup or state_backup:
                    print(f"✅ Backed up {service_name}")
                    if cookie_backup:
                        print(f"   - Cookies: {cookie_backup}")
                    if state_backup:
                        print(f"   - State: {state_backup}")
                else:
                    print(f"⚠️  No files to backup for {service_name}")
            except Exception as e:
                print(f"❌ Error backing up {service_name}: {e}")
        
        return 0

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='BEDROT Cookie Refresh System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --check                    # Check all cookie status
  %(prog)s --check --service spotify  # Check specific service
  %(prog)s --refresh                  # Refresh expired cookies
  %(prog)s --refresh --no-interactive # Auto-refresh without prompts
  %(prog)s --backup                   # Backup all cookies
        """
    )
    
    # Actions
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--check', action='store_true',
                            help='Check cookie expiration status')
    action_group.add_argument('--refresh', action='store_true',
                            help='Refresh expired or expiring cookies')
    action_group.add_argument('--backup', action='store_true',
                            help='Backup current cookies')
    
    # Options
    parser.add_argument('--service', type=str,
                      help='Specific service to operate on')
    parser.add_argument('--no-interactive', action='store_true',
                      help='Run without user prompts')
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create CLI instance
    cli = CookieRefreshCLI()
    
    # Execute action
    try:
        if args.check:
            return cli.check_status(args.service)
        elif args.refresh:
            return cli.refresh_cookies(args.service, interactive=not args.no_interactive)
        elif args.backup:
            return cli.backup_cookies(args.service)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        return 1
    except Exception as e:
        logger.exception("Unexpected error")
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())