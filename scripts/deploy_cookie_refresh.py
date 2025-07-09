#!/usr/bin/env python3
"""
Production deployment script for Cookie Refresh System.
This script validates and prepares the cookie refresh system for production use.
"""

import os
import sys
import subprocess
from pathlib import Path
import json
import yaml
from datetime import datetime
import shutil

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'

def print_status(message, status='info'):
    """Print colored status messages."""
    if status == 'success':
        print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")
    elif status == 'warning':
        print(f"{Colors.YELLOW}⚠ {message}{Colors.ENDC}")
    elif status == 'error':
        print(f"{Colors.RED}✗ {message}{Colors.ENDC}")
    elif status == 'info':
        print(f"{Colors.BLUE}ℹ {message}{Colors.ENDC}")
    else:
        print(message)

def check_environment():
    """Check environment setup."""
    print("\n1. Checking Environment Setup...")
    
    # Check PROJECT_ROOT
    project_root = os.environ.get('PROJECT_ROOT')
    if not project_root:
        # Try to determine from current location
        current_dir = Path(__file__).parent.parent
        if current_dir.name == 'data_lake':
            project_root = str(current_dir)
            os.environ['PROJECT_ROOT'] = project_root
            print_status(f"Set PROJECT_ROOT to: {project_root}", 'success')
        else:
            print_status("PROJECT_ROOT not set", 'error')
            return False
    else:
        print_status(f"PROJECT_ROOT: {project_root}", 'success')
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 8:
        print_status(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}", 'success')
    else:
        print_status(f"Python version {python_version.major}.{python_version.minor} is too old. Need 3.8+", 'error')
        return False
    
    return True

def check_dependencies():
    """Check required Python packages."""
    print("\n2. Checking Dependencies...")
    
    required_packages = [
        'playwright',
        'pyyaml',
        'pandas',
        'requests',
        'beautifulsoup4'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print_status(f"Package '{package}' installed", 'success')
        except ImportError:
            missing_packages.append(package)
            print_status(f"Package '{package}' missing", 'error')
    
    if missing_packages:
        print_status(f"\nInstall missing packages with: pip install {' '.join(missing_packages)}", 'warning')
        return False
    
    return True

def check_directory_structure():
    """Check and create required directories."""
    print("\n3. Checking Directory Structure...")
    
    project_root = Path(os.environ.get('PROJECT_ROOT', '.'))
    
    required_dirs = [
        'config',
        'logs',
        'logs/screenshots',
        'backups/cookies',
        'src/common/cookie_refresh'
    ]
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print_status(f"Created directory: {dir_path}", 'success')
        else:
            print_status(f"Directory exists: {dir_path}", 'success')
    
    return True

def check_configuration():
    """Check configuration files."""
    print("\n4. Checking Configuration...")
    
    project_root = Path(os.environ.get('PROJECT_ROOT', '.'))
    config_path = project_root / 'config' / 'cookie_refresh_config.yaml'
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            print_status("Configuration file loaded successfully", 'success')
            
            # Validate configuration structure
            required_sections = ['general', 'services', 'notifications']
            for section in required_sections:
                if section in config:
                    print_status(f"  - Section '{section}' present", 'success')
                else:
                    print_status(f"  - Section '{section}' missing", 'error')
                    return False
            
        except Exception as e:
            print_status(f"Error loading configuration: {e}", 'error')
            return False
    else:
        print_status("Configuration file not found", 'error')
        print_status("Run this script from the data_lake directory", 'warning')
        return False
    
    return True

def check_cookie_files():
    """Check existing cookie files."""
    print("\n5. Checking Cookie Files...")
    
    project_root = Path(os.environ.get('PROJECT_ROOT', '.'))
    src_path = project_root / 'src'
    
    services = ['spotify', 'distrokid', 'tiktok', 'toolost', 'linktree']
    cookie_status = {}
    
    for service in services:
        cookie_path = src_path / service / 'cookies' / 'cookies.json'
        
        # Also check for service-specific cookie files
        if service == 'spotify':
            cookie_path = src_path / service / 'cookies' / 'spotify_cookies.json'
        elif service == 'distrokid':
            cookie_path = src_path / service / 'cookies' / 'distrokid_cookies.json'
        elif service == 'linktree':
            cookie_path = src_path / service / 'cookies' / 'linktree_cookies.json'
        elif service == 'toolost':
            cookie_path = src_path / service / 'cookies' / 'toolost_cookies.json'
        
        if cookie_path.exists():
            try:
                with open(cookie_path, 'r') as f:
                    cookies = json.load(f)
                
                # Check expiration
                now = datetime.now().timestamp()
                expired = False
                for cookie in cookies:
                    if isinstance(cookie, dict) and 'expirationDate' in cookie:
                        if cookie['expirationDate'] < now:
                            expired = True
                            break
                
                if expired:
                    print_status(f"{service}: Found (EXPIRED)", 'warning')
                else:
                    print_status(f"{service}: Found (Valid)", 'success')
                
                cookie_status[service] = 'expired' if expired else 'valid'
                
            except Exception as e:
                print_status(f"{service}: Error reading cookies - {e}", 'error')
                cookie_status[service] = 'error'
        else:
            print_status(f"{service}: No cookies found", 'warning')
            cookie_status[service] = 'missing'
    
    # Check TikTok multi-account
    for account in ['pig1987', 'zone.a0']:
        cookie_path = src_path / 'tiktok' / 'cookies' / f'{account}_cookies.json'
        if cookie_path.exists():
            print_status(f"TikTok/{account}: Found", 'success')
    
    return cookie_status

def test_basic_functionality():
    """Test basic cookie refresh functionality."""
    print("\n6. Testing Basic Functionality...")
    
    try:
        # Test import
        sys.path.insert(0, os.environ.get('PROJECT_ROOT', '.'))
        sys.path.insert(0, os.path.join(os.environ.get('PROJECT_ROOT', '.'), 'src'))
        
        from common.cookie_refresh.storage import CookieStorageManager
        from common.cookie_refresh.config import CookieRefreshConfig
        
        print_status("Imports successful", 'success')
        
        # Test configuration loading
        config = CookieRefreshConfig()
        enabled_services = config.get_enabled_services()
        print_status(f"Enabled services: {', '.join(enabled_services)}", 'success')
        
        # Test storage manager
        storage = CookieStorageManager(Path(os.environ.get('PROJECT_ROOT', '.')) / 'src')
        all_status = storage.get_all_services_status()
        print_status(f"Found {len(all_status)} services with stored auth", 'success')
        
        return True
        
    except Exception as e:
        print_status(f"Error during functionality test: {e}", 'error')
        return False

def create_test_script():
    """Create a quick test script."""
    print("\n7. Creating Test Script...")
    
    project_root = Path(os.environ.get('PROJECT_ROOT', '.'))
    test_script_path = project_root / 'scripts' / 'test_cookie_refresh.py'
    
    test_script_content = '''#!/usr/bin/env python3
"""Quick test script for cookie refresh system."""

import sys
import os
from pathlib import Path

# Set up paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from common.cookie_refresh.storage import CookieStorageManager
from common.cookie_refresh.monitor import CookieRefreshMonitor
from common.cookie_refresh.config import CookieRefreshConfig

def main():
    """Run basic tests."""
    print("\\n=== Cookie Refresh System Test ===\\n")
    
    # Test configuration
    print("1. Testing configuration...")
    config = CookieRefreshConfig()
    print(f"   - Check interval: {config.get_general_setting('check_interval_hours')} hours")
    print(f"   - Warning threshold: {config.get_general_setting('expiration_warning_days')} days")
    print(f"   - Enabled services: {', '.join(config.get_enabled_services())}")
    
    # Test storage
    print("\\n2. Testing storage...")
    storage = CookieStorageManager(project_root / 'src')
    statuses = storage.get_all_services_status()
    
    for status in statuses:
        days_left = status.days_until_expiration or 0
        status_text = status.status
        print(f"   - {status.service}: {status_text} ({days_left} days left)")
    
    # Test monitor
    print("\\n3. Testing monitor...")
    monitor = CookieRefreshMonitor(config)
    services_needing_refresh = monitor.check_all_services()
    
    if services_needing_refresh:
        print(f"   - Services needing refresh: {', '.join([s['service'] for s in services_needing_refresh])}")
    else:
        print("   - All services are up to date!")
    
    print("\\n✓ Test completed successfully!")

if __name__ == "__main__":
    main()
'''
    
    # Create scripts directory if needed
    test_script_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(test_script_path, 'w') as f:
        f.write(test_script_content)
    
    print_status(f"Created test script: {test_script_path}", 'success')
    return True

def integrate_with_pipeline():
    """Update the main pipeline to include cookie refresh checks."""
    print("\n8. Integrating with Pipeline...")
    
    project_root = Path(os.environ.get('PROJECT_ROOT', '.'))
    pipeline_script = project_root / 'cronjob' / 'run_bedrot_pipeline.bat'
    
    if pipeline_script.exists():
        # Read current content
        with open(pipeline_script, 'r') as f:
            content = f.read()
        
        # Check if already integrated
        if 'refresh_cookies.bat' in content:
            print_status("Already integrated with pipeline", 'success')
        else:
            # Backup original
            backup_path = pipeline_script.with_suffix('.bat.backup')
            shutil.copy2(pipeline_script, backup_path)
            print_status(f"Backed up original to: {backup_path}", 'success')
            
            # Find where to insert cookie check (after auth check)
            lines = content.split('\n')
            insert_index = -1
            
            for i, line in enumerate(lines):
                if 'run_with_auth_check.py' in line:
                    insert_index = i + 5  # A few lines after auth check
                    break
            
            if insert_index > 0:
                # Insert cookie refresh check
                cookie_check = [
                    "",
                    "REM Check and refresh cookies if needed",
                    "echo.",
                    "echo Checking cookie expiration status...",
                    "call %~dp0refresh_cookies.bat",
                    "echo.",
                    ""
                ]
                
                for j, line in enumerate(cookie_check):
                    lines.insert(insert_index + j, line)
                
                # Write updated content
                with open(pipeline_script, 'w') as f:
                    f.write('\n'.join(lines))
                
                print_status("Integrated cookie refresh into pipeline", 'success')
            else:
                print_status("Could not find insertion point in pipeline script", 'warning')
    else:
        print_status("Pipeline script not found", 'warning')
    
    return True

def print_summary(cookie_status):
    """Print deployment summary."""
    print("\n" + "="*50)
    print("DEPLOYMENT SUMMARY")
    print("="*50)
    
    print("\n✓ Cookie Refresh System is ready for production!")
    
    print("\n📋 Next Steps:")
    print("1. Test the system:")
    print(f"   {Colors.BLUE}python scripts/test_cookie_refresh.py{Colors.ENDC}")
    
    print("\n2. Check cookie status:")
    print(f"   {Colors.BLUE}cronjob\\refresh_cookies.bat{Colors.ENDC}")
    
    print("\n3. Run full pipeline with cookie refresh:")
    print(f"   {Colors.BLUE}cronjob\\run_bedrot_pipeline.bat{Colors.ENDC}")
    
    if any(status in ['expired', 'missing'] for status in cookie_status.values()):
        print("\n⚠️  Some cookies need attention:")
        for service, status in cookie_status.items():
            if status in ['expired', 'missing']:
                print(f"   - {service}: {status}")
    
    print("\n📅 Recommended Schedule:")
    print("   - Daily: Run pipeline with cookie check")
    print("   - Weekly: Manual check for TooLost JWT refresh")
    print("   - Monthly: Review all cookie expirations")
    
    print("\n📊 Monitoring:")
    print("   - Logs: data_lake/logs/cookie_refresh.log")
    print("   - Screenshots: data_lake/logs/screenshots/")
    print("   - Backups: data_lake/backups/cookies/")

def main():
    """Main deployment function."""
    print("="*50)
    print("COOKIE REFRESH SYSTEM DEPLOYMENT")
    print("="*50)
    
    # Run all checks
    checks = [
        ("Environment", check_environment),
        ("Dependencies", check_dependencies),
        ("Directory Structure", check_directory_structure),
        ("Configuration", check_configuration),
        ("Basic Functionality", test_basic_functionality)
    ]
    
    all_passed = True
    for name, check_func in checks:
        if not check_func():
            all_passed = False
            print_status(f"\n{name} check failed. Fix issues and run again.", 'error')
            return 1
    
    # Check cookie files
    cookie_status = check_cookie_files()
    
    # Create test script
    create_test_script()
    
    # Integrate with pipeline
    integrate_with_pipeline()
    
    # Print summary
    print_summary(cookie_status)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())