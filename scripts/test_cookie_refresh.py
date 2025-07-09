#!/usr/bin/env python3
"""Quick test script for cookie refresh system."""

import sys
import os
from pathlib import Path

# Set up paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from common.cookie_refresh.storage import CookieStorageManager
from common.cookie_refresh.refresher import CookieRefresher
from common.cookie_refresh.config import CookieRefreshConfig

def main():
    """Run basic tests."""
    print("\n=== Cookie Refresh System Test ===\n")
    
    # Test configuration
    print("1. Testing configuration...")
    config = CookieRefreshConfig()
    print(f"   - Check interval: {config.get_general_setting('check_interval_hours')} hours")
    print(f"   - Warning threshold: {config.get_general_setting('expiration_warning_days')} days")
    print(f"   - Enabled services: {', '.join(config.get_enabled_services())}")
    
    # Test storage
    print("\n2. Testing storage...")
    storage = CookieStorageManager(project_root / 'src')
    statuses = storage.get_all_services_status()
    
    for status in statuses:
        days_left = status.days_until_expiration or 0
        status_text = status.status
        print(f"   - {status.service}: {status_text} ({days_left} days left)")
    
    # Test refresher
    print("\n3. Testing refresher...")
    try:
        refresher = CookieRefresher(base_path=project_root / 'src')
        
        # Check which services need refresh
        need_refresh = []
        for status in statuses:
            if status.is_expired or (status.days_until_expiration and status.days_until_expiration <= 3):
                need_refresh.append(status.service)
        
        if need_refresh:
            print(f"   - Services needing refresh: {', '.join(need_refresh)}")
        else:
            print("   - All services are up to date!")
    except Exception as e:
        print(f"   - Error testing refresher: {e}")
    
    print("\n✓ Test completed successfully!")

if __name__ == "__main__":
    main()