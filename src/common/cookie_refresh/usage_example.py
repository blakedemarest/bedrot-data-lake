#!/usr/bin/env python3
"""Usage examples for the cookie refresh system.

This script demonstrates how to use the cookie refresh strategies
for different scenarios.
"""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = os.getenv("PROJECT_ROOT", str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, PROJECT_ROOT)

from src.common.cookie_refresh.refresher import CookieRefresher
from src.common.cookie_refresh.storage import CookieStorageManager
from src.common.cookie_refresh.notifier import CookieRefreshNotifier


def example_check_all_services():
    """Example: Check status of all services."""
    print("\n" + "=" * 60)
    print("Example 1: Check All Services Status")
    print("=" * 60)
    
    refresher = CookieRefresher()
    status_list = refresher.check_all_services()
    
    print(f"\nFound {len(status_list)} services:")
    for status in status_list:
        print(f"  - {status.service}: {status.status} "
              f"(expires in {status.days_until_expiration} days)")


def example_refresh_critical_service():
    """Example: Refresh TooLost (critical due to 7-day JWT expiration)."""
    print("\n" + "=" * 60)
    print("Example 2: Refresh Critical Service (TooLost)")
    print("=" * 60)
    
    refresher = CookieRefresher()
    
    # Check TooLost status first
    auth_info = refresher.storage_manager.get_expiration_info('toolost')
    print(f"\nTooLost status: {auth_info.status}")
    print(f"Days until expiration: {auth_info.days_until_expiration}")
    
    # Refresh if needed
    if auth_info.is_expired or auth_info.days_until_expiration <= 1:
        print("\nTooLost needs urgent refresh! Starting...")
        result = refresher.refresh_service('toolost')
        print(f"Result: {result.message}")
    else:
        print("\nTooLost JWT is still valid.")


def example_refresh_specific_tiktok_account():
    """Example: Refresh specific TikTok account."""
    print("\n" + "=" * 60)
    print("Example 3: Refresh Specific TikTok Account")
    print("=" * 60)
    
    refresher = CookieRefresher()
    
    # Check both TikTok accounts
    for account in ['pig1987', 'zone.a0']:
        auth_info = refresher.storage_manager.get_expiration_info('tiktok', account)
        print(f"\nTikTok/{account} status: {auth_info.status}")
        
        if auth_info.is_expired:
            print(f"Refreshing {account}...")
            result = refresher.refresh_service('tiktok', account=account)
            print(f"Result: {result.message}")


def example_force_refresh():
    """Example: Force refresh a service even if not expired."""
    print("\n" + "=" * 60)
    print("Example 4: Force Refresh Service")
    print("=" * 60)
    
    refresher = CookieRefresher()
    
    # Force refresh Spotify
    print("\nForce refreshing Spotify cookies...")
    result = refresher.refresh_service('spotify', force=True)
    print(f"Success: {result.success}")
    print(f"Message: {result.message}")


def example_refresh_all_expired():
    """Example: Refresh all services that need it."""
    print("\n" + "=" * 60)
    print("Example 5: Refresh All Expired Services")
    print("=" * 60)
    
    refresher = CookieRefresher()
    
    print("\nChecking and refreshing all services that need it...")
    results = refresher.refresh_all_needed()
    
    print("\nResults:")
    for service, service_results in results.items():
        for result in service_results:
            status = "✓" if result.success else "✗"
            print(f"  {status} {service}: {result.message}")


def example_direct_strategy_usage():
    """Example: Use a strategy directly without the refresher."""
    print("\n" + "=" * 60)
    print("Example 6: Direct Strategy Usage")
    print("=" * 60)
    
    from src.common.cookie_refresh.strategies import LinktreeRefreshStrategy
    
    # Create components
    storage_manager = CookieStorageManager(
        base_path=Path(PROJECT_ROOT) / 'data_lake' / 'src',
        backup_path=Path(PROJECT_ROOT) / 'data_lake' / 'backups' / 'cookies'
    )
    
    notifier = CookieRefreshNotifier({
        'enabled': True,
        'console': {'enabled': True}
    })
    
    # Create strategy
    strategy = LinktreeRefreshStrategy(
        storage_manager=storage_manager,
        notifier=notifier,
        config={'browser_headless': False}
    )
    
    # Check if refresh needed
    needs_refresh, reason = strategy.needs_refresh()
    print(f"\nLinktree needs refresh: {needs_refresh}")
    if reason:
        print(f"Reason: {reason}")
    
    # Refresh if needed
    if needs_refresh:
        print("\nStarting Linktree refresh...")
        result = strategy.refresh_cookies()
        print(f"Result: {result.message}")


def main():
    """Run usage examples."""
    print("\n" + "=" * 80)
    print("Cookie Refresh System - Usage Examples")
    print("=" * 80)
    
    examples = [
        ("Check all services", example_check_all_services),
        ("Refresh critical service", example_refresh_critical_service),
        ("Refresh specific account", example_refresh_specific_tiktok_account),
        ("Force refresh", example_force_refresh),
        ("Refresh all expired", example_refresh_all_expired),
        ("Direct strategy usage", example_direct_strategy_usage)
    ]
    
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nRunning all examples...")
    
    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\nExample '{name}' failed: {e}")
    
    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80)


if __name__ == "__main__":
    # Command line usage
    import argparse
    
    parser = argparse.ArgumentParser(description='Cookie refresh usage examples')
    parser.add_argument('--example', type=int, help='Run specific example (1-6)')
    
    args = parser.parse_args()
    
    if args.example:
        examples = [
            example_check_all_services,
            example_refresh_critical_service,
            example_refresh_specific_tiktok_account,
            example_force_refresh,
            example_refresh_all_expired,
            example_direct_strategy_usage
        ]
        
        if 1 <= args.example <= len(examples):
            examples[args.example - 1]()
        else:
            print(f"Invalid example number. Choose 1-{len(examples)}")
    else:
        main()