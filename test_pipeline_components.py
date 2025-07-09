#!/usr/bin/env python3
"""
Test script to verify pipeline components work correctly
"""

import os
import sys
import subprocess
from pathlib import Path

# Set PROJECT_ROOT
PROJECT_ROOT = Path(__file__).parent
os.environ['PROJECT_ROOT'] = str(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

print("="*60)
print("TESTING PIPELINE COMPONENTS")
print("="*60)
print(f"PROJECT_ROOT: {PROJECT_ROOT}")
print()

# Test 1: Import health monitor
print("Test 1: Importing pipeline_health_monitor...")
try:
    from common.pipeline_health_monitor import PipelineHealthMonitor
    print("✅ Successfully imported pipeline_health_monitor")
except Exception as e:
    print(f"❌ Failed to import pipeline_health_monitor: {e}")

# Test 2: Import auth check
print("\nTest 2: Importing run_with_auth_check...")
try:
    from common.run_with_auth_check import check_cookie_freshness, AUTH_SERVICES
    print("✅ Successfully imported run_with_auth_check")
    print(f"   Services configured: {list(AUTH_SERVICES.keys())}")
except Exception as e:
    print(f"❌ Failed to import run_with_auth_check: {e}")

# Test 3: Check for required directories
print("\nTest 3: Checking required directories...")
required_dirs = ['landing', 'raw', 'staging', 'curated', 'src']
for dir_name in required_dirs:
    dir_path = PROJECT_ROOT / dir_name
    if dir_path.exists():
        print(f"✅ {dir_name}/ exists")
    else:
        print(f"❌ {dir_name}/ missing")

# Test 4: Check for service directories
print("\nTest 4: Checking service directories...")
services = ['spotify', 'tiktok', 'distrokid', 'toolost', 'linktree', 'metaads']
for service in services:
    service_dir = PROJECT_ROOT / 'src' / service
    if service_dir.exists():
        print(f"✅ src/{service}/ exists")
        # Check for subdirs
        for subdir in ['extractors', 'cleaners', 'cookies']:
            if (service_dir / subdir).exists():
                print(f"   ✅ {subdir}/ exists")
            else:
                print(f"   ❌ {subdir}/ missing")
    else:
        print(f"❌ src/{service}/ missing")

# Test 5: Test health monitor instantiation
print("\nTest 5: Testing PipelineHealthMonitor...")
try:
    monitor = PipelineHealthMonitor()
    print("✅ PipelineHealthMonitor instantiated successfully")
except Exception as e:
    print(f"❌ Failed to create PipelineHealthMonitor: {e}")

# Test 6: Test cookie check function
print("\nTest 6: Testing cookie freshness check...")
try:
    # Test with a service
    is_fresh, reason, days = check_cookie_freshness("spotify")
    print(f"✅ Cookie check completed: {reason}")
except Exception as e:
    print(f"❌ Cookie check failed: {e}")

# Test 7: Check Python version
print("\nTest 7: Python environment...")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Test 8: Check if we can run batch files
print("\nTest 8: Batch file checks...")
batch_files = [
    '6_automated_cronjob/run_pipeline_with_auth.bat',
    '6_automated_cronjob/run_bedrot_pipeline.bat'
]
for batch_file in batch_files:
    batch_path = PROJECT_ROOT / batch_file
    if batch_path.exists():
        print(f"✅ {batch_file} exists")
    else:
        print(f"❌ {batch_file} missing")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)

# Summary
print("\nTo run the pipeline:")
print("1. From Windows Command Prompt:")
print(f"   cd \"{PROJECT_ROOT}\"")
print("   6_automated_cronjob\\run_bedrot_pipeline.bat")
print("\n2. Or use the existing pipeline:")
print("   6_automated_cronjob\\run_pipeline_with_auth.bat")
print("\nFor testing individual components:")
print("   python src\\common\\pipeline_health_monitor.py")
print("   python src\\common\\run_with_auth_check.py --check-only")