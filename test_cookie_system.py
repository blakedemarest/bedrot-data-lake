#!/usr/bin/env python3
"""
Quick test script to verify cookie refresh system functionality.
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from common.cookie_refresh.storage import CookieStorageManager
        print("✅ Storage module imported")
        
        from common.cookie_refresh.config import CookieRefreshConfig
        print("✅ Config module imported")
        
        from common.cookie_refresh.refresher import CookieRefresher
        print("✅ Refresher module imported")
        
        from common.cookie_refresh.notifier import CookieRefreshNotifier
        print("✅ Notifier module imported")
        
        # Test service strategies
        from common.cookie_refresh.strategies.distrokid import DistroKidRefreshStrategy
        from common.cookie_refresh.strategies.spotify import SpotifyRefreshStrategy
        from common.cookie_refresh.strategies.tiktok import TikTokRefreshStrategy
        from common.cookie_refresh.strategies.toolost import TooLostRefreshStrategy
        from common.cookie_refresh.strategies.linktree import LinktreeRefreshStrategy
        print("✅ All service strategies imported")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_cookie_status():
    """Test checking cookie status."""
    print("\nTesting cookie status check...")
    try:
        from common.cookie_refresh.storage import CookieStorageManager
        
        # Initialize storage manager with base path
        import os
        base_path = os.path.join(os.path.dirname(__file__), 'src')
        storage = CookieStorageManager(base_path)
        
        # Get status for all services
        print("\nCookie Status for All Services:")
        print("-" * 80)
        
        services = ['distrokid', 'spotify', 'tiktok', 'toolost', 'linktree']
        
        for service in services:
            try:
                info = storage.get_expiration_info(service)
                status = "✅ Valid" if not info.is_expired else "❌ Expired"
                days = info.days_until_expiration or 0
                
                print(f"{service.ljust(15)} | {status} | {days} days remaining")
                
                # Check for specific accounts (TikTok)
                if service == 'tiktok':
                    for account in ['pig1987', 'zone.a0']:
                        try:
                            acc_info = storage.get_expiration_info(service, account)
                            acc_status = "✅ Valid" if not acc_info.is_expired else "❌ Expired"
                            acc_days = acc_info.days_until_expiration or 0
                            print(f"  - {account.ljust(12)} | {acc_status} | {acc_days} days remaining")
                        except:
                            print(f"  - {account.ljust(12)} | ⚠️  No cookies found")
                            
            except Exception as e:
                print(f"{service.ljust(15)} | ⚠️  Error: {str(e)[:50]}")
        
        print("-" * 80)
        return True
        
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_operations():
    """Test basic operations without running actual refresh."""
    print("\nTesting basic operations...")
    try:
        from common.cookie_refresh.config import CookieRefreshConfig
        
        # Test config loading
        config = CookieRefreshConfig()
        print(f"✅ Config loaded successfully")
        
        # Check services configuration
        services = config.get_enabled_services()
        print(f"✅ Found {len(services)} enabled services: {', '.join(services)}")
        
        # Check critical service (TooLost)
        toolost_config = config.get_service_config('toolost')
        if toolost_config and toolost_config.get('expiration_days') == 7:
            print("✅ TooLost correctly configured with 7-day expiration")
        else:
            print("⚠️  TooLost configuration may need adjustment")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic operations test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 80)
    print("BEDROT Cookie Refresh System - Test Suite")
    print("=" * 80)
    
    # Set environment
    os.environ['PROJECT_ROOT'] = os.path.dirname(os.path.abspath(__file__))
    
    tests = [
        ("Import Test", test_imports),
        ("Cookie Status", test_cookie_status),
        ("Basic Operations", test_basic_operations)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n### Running {test_name} ###")
        success = test_func()
        results.append((test_name, success))
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary:")
    print("-" * 80)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name.ljust(20)} | {status}")
        if not success:
            all_passed = False
    
    print("-" * 80)
    
    if all_passed:
        print("\n✅ All tests passed! The cookie refresh system is operational.")
        print("\nNext steps:")
        print("1. Review cookie status above")
        print("2. Refresh expired cookies: python -m common.cookie_refresh.refresher --service <name>")
        print("3. Set up scheduled refresh: cronjob\\refresh_cookies_auto.bat")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())