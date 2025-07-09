#!/usr/bin/env python3
"""
Production-ready cookie refresh command-line interface.
This is the main entry point for the cookie refresh system.
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Set up paths
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_cookie_status():
    """Check and display cookie status for all services."""
    from common.cookie_refresh.storage import CookieStorageManager
    from common.cookie_refresh.config import CookieRefreshConfig
    
    print("\n" + "=" * 80)
    print("BEDROT Cookie Status Report")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")
    
    # Initialize with proper paths
    config = CookieRefreshConfig()
    base_path = PROJECT_ROOT / 'src'
    storage = CookieStorageManager(base_path)
    
    services = {
        'distrokid': {'critical': False, 'max_days': 14},
        'spotify': {'critical': False, 'max_days': 30},
        'tiktok': {'critical': False, 'max_days': 30, 'accounts': ['pig1987', 'zone.a0']},
        'toolost': {'critical': True, 'max_days': 7},  # JWT expires in 7 days!
        'linktree': {'critical': False, 'max_days': 30}
    }
    
    critical_issues = []
    warnings = []
    
    for service, info in services.items():
        print(f"📊 {service.upper()}")
        print("-" * 40)
        
        if 'accounts' in info:
            # Multi-account service
            for account in info['accounts']:
                try:
                    status = storage.get_expiration_info(service, account)
                    display_status(f"{service}/{account}", status, info, critical_issues, warnings)
                except Exception as e:
                    print(f"  {account}: ❌ Error - {str(e)[:50]}")
                    if info['critical']:
                        critical_issues.append(f"{service}/{account}: No cookies found")
        else:
            # Single account service
            try:
                status = storage.get_expiration_info(service)
                display_status(service, status, info, critical_issues, warnings)
            except Exception as e:
                print(f"  Status: ❌ Error - {str(e)[:50]}")
                if info['critical']:
                    critical_issues.append(f"{service}: No cookies found")
        
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if critical_issues:
        print("\n🚨 CRITICAL ISSUES:")
        for issue in critical_issues:
            print(f"  - {issue}")
    
    if warnings:
        print("\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not critical_issues and not warnings:
        print("\n✅ All cookies are healthy!")
    
    print("\n" + "=" * 80)
    
    # Recommendations
    if critical_issues or warnings:
        print("\n📋 RECOMMENDED ACTIONS:")
        if any('toolost' in issue for issue in critical_issues):
            print("  1. URGENT: Refresh TooLost cookies (JWT expires every 7 days!)")
            print("     Run: python cookie_refresh.py --refresh toolost")
        
        for warning in warnings:
            service = warning.split(':')[0]
            print(f"  - Refresh {service}: python cookie_refresh.py --refresh {service}")
    
    return len(critical_issues) == 0

def display_status(name, status, info, critical_issues, warnings):
    """Display status for a single service/account."""
    # Handle both dict and AuthStateInfo object
    if hasattr(status, '__dict__'):
        # Convert object to dict
        status = status.__dict__
    
    is_valid = status.get('is_valid', False)
    days_remaining = status.get('days_remaining', 0)
    last_update = status.get('last_update', 'Unknown')
    
    # Determine status icon and message
    if not is_valid:
        icon = "❌"
        message = "EXPIRED"
        if info['critical']:
            critical_issues.append(f"{name}: Cookies expired")
        else:
            warnings.append(f"{name}: Cookies expired")
    elif days_remaining <= 3:
        icon = "⚠️"
        message = f"Expires in {days_remaining} days"
        if info['critical']:
            critical_issues.append(f"{name}: Expires in {days_remaining} days")
        else:
            warnings.append(f"{name}: Expires in {days_remaining} days")
    else:
        icon = "✅"
        message = f"Valid for {days_remaining} days"
    
    # Display
    print(f"  Status: {icon} {message}")
    print(f"  Last Update: {last_update}")
    print(f"  Cookie File: {status.get('cookie_file', 'Not found')}")

def refresh_cookies(service=None, force=False):
    """Refresh cookies for specified service or all services."""
    from common.cookie_refresh.refresher import CookieRefresher
    
    print(f"\n🔄 Starting cookie refresh...")
    
    try:
        refresher = CookieRefresher()
        
        if service:
            print(f"Refreshing cookies for: {service}")
            result = refresher.refresh_service(service, force=force)
            if result.success:
                print(f"✅ Successfully refreshed {service}")
            else:
                print(f"❌ Failed to refresh {service}: {result.message}")
                return False
        else:
            print("Refreshing all services...")
            results = refresher.refresh_all_services(force=force)
            
            success_count = sum(1 for r in results.values() if r.success)
            total_count = len(results)
            
            print(f"\n✅ Refreshed {success_count}/{total_count} services successfully")
            
            if success_count < total_count:
                print("\nFailed services:")
                for svc, result in results.items():
                    if not result.success:
                        print(f"  - {svc}: {result.message}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Refresh failed: {e}")
        print(f"❌ Error during refresh: {e}")
        return False

def run_health_monitor():
    """Run the enhanced pipeline health monitor."""
    print("\n🏥 Running Pipeline Health Monitor...")
    
    try:
        # Run the health monitor script
        import subprocess
        result = subprocess.run(
            [sys.executable, "src/common/pipeline_health_monitor.py", "--auto-remediate"],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        
        if result.returncode == 0:
            print("✅ Pipeline health check completed successfully")
        else:
            print("⚠️  Pipeline health check found issues")
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Health monitor error: {e}")
        return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="BEDROT Cookie Refresh System - Production CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cookie_refresh.py --check              # Check all cookie status
  python cookie_refresh.py --refresh toolost    # Refresh TooLost cookies (critical!)
  python cookie_refresh.py --refresh-all        # Refresh all expired cookies
  python cookie_refresh.py --health             # Run pipeline health monitor
  python cookie_refresh.py --refresh tiktok --account zone.a0  # Refresh specific account
        """
    )
    
    parser.add_argument('--check', '-c', action='store_true',
                       help='Check cookie status for all services')
    parser.add_argument('--refresh', '-r', metavar='SERVICE',
                       help='Refresh cookies for specific service')
    parser.add_argument('--refresh-all', '-R', action='store_true',
                       help='Refresh all expired cookies')
    parser.add_argument('--force', '-f', action='store_true',
                       help='Force refresh even if not expired')
    parser.add_argument('--account', '-a', metavar='ACCOUNT',
                       help='Specify account for multi-account services')
    parser.add_argument('--health', '-H', action='store_true',
                       help='Run pipeline health monitor')
    
    args = parser.parse_args()
    
    # Default to check if no action specified
    if not any([args.check, args.refresh, args.refresh_all, args.health]):
        args.check = True
    
    # Set environment
    os.environ['PROJECT_ROOT'] = str(PROJECT_ROOT)
    os.environ['PYTHONPATH'] = str(PROJECT_ROOT / 'src')
    
    success = True
    
    if args.check:
        success = check_cookie_status()
    
    if args.refresh:
        # Handle account specification for multi-account services
        service = args.refresh
        if args.account and service == 'tiktok':
            service = f"{service}/{args.account}"
        success = refresh_cookies(service, force=args.force)
    
    if args.refresh_all:
        success = refresh_cookies(force=args.force)
    
    if args.health:
        success = run_health_monitor()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())