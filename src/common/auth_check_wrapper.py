#!/usr/bin/env python3
"""
Authentication Check Wrapper for Semi-Manual Data Pipeline

This script provides a wrapper around extractors that:
1. Checks cookie freshness before running
2. Prompts for manual authentication when needed
3. Supports both interactive and automated modes
4. Can run specific services or all services
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import time

# Add src to Python path
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

PROJECT_ROOT = os.environ.get('PROJECT_ROOT')
if not PROJECT_ROOT:
    print("ERROR: PROJECT_ROOT environment variable must be set.")
    sys.exit(1)

PROJECT_ROOT = Path(PROJECT_ROOT)


class ServiceAuthChecker:
    """Check authentication status for various services."""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.cookie_expiry_days = {
            'spotify': 30,
            'tiktok': 30,
            'distrokid': 30,
            'toolost': 7,  # JWT token expires in 7 days
            'linktree': 30,
            'metaads': 90
        }
    
    def check_cookie_freshness(self, service: str) -> Tuple[bool, Optional[str]]:
        """Check if cookies for a service are fresh enough."""
        cookie_patterns = {
            'spotify': 'src/spotify/cookies/spotify_cookies.json',
            'tiktok': 'src/tiktok/cookies/tiktok_cookies_*.json',
            'distrokid': 'src/distrokid/cookies/distrokid_cookies.json',
            'toolost': 'src/toolost/cookies/toolost_cookies.json',
            'linktree': 'src/linktree/cookies/linktree_cookies.json',
            'metaads': 'src/metaads/cookies/metaads_cookies.json'
        }
        
        pattern = cookie_patterns.get(service)
        if not pattern:
            return True, f"No cookie check configured for {service}"
        
        # Handle wildcard patterns
        if '*' in pattern:
            cookie_dir = self.project_root / Path(pattern).parent
            pattern_name = Path(pattern).name
            if cookie_dir.exists():
                cookie_files = list(cookie_dir.glob(pattern_name))
                if not cookie_files:
                    return False, f"No cookie files found matching {pattern}"
                # Check the most recent file
                cookie_path = max(cookie_files, key=lambda p: p.stat().st_mtime)
            else:
                return False, f"Cookie directory not found: {cookie_dir}"
        else:
            cookie_path = self.project_root / pattern
            if not cookie_path.exists():
                return False, f"Cookie file not found: {pattern}"
        
        # Check file age
        file_age = datetime.now() - datetime.fromtimestamp(cookie_path.stat().st_mtime)
        max_age = self.cookie_expiry_days.get(service, 30)
        
        if file_age.days > max_age:
            return False, f"Cookies are {file_age.days} days old (max {max_age} days)"
        
        # For TooLost, check JWT token expiration
        if service == 'toolost':
            try:
                with open(cookie_path, 'r') as f:
                    cookies = json.load(f)
                    for cookie in cookies:
                        if cookie.get('name') == 'jwt_token':
                            # Check if token is expired
                            import jwt
                            try:
                                jwt.decode(cookie['value'], options={"verify_signature": False})
                            except jwt.ExpiredSignatureError:
                                return False, "JWT token has expired"
            except Exception as e:
                print(f"Warning: Could not validate JWT token: {e}")
        
        return True, f"Cookies are {file_age.days} days old"
    
    def get_extractor_script(self, service: str) -> Optional[Path]:
        """Get the manual authentication script for a service."""
        manual_scripts = {
            'spotify': 'src/spotify/extractors/spotify_audience_extractor.py',
            'tiktok': 'src/tiktok/extractors/tiktok_analytics_extractor_zonea0.py',
            'distrokid': 'src/distrokid/extractors/distrokid_scraper.py',
            'toolost': 'src/toolost/extractors/toolost_scraper.py',
            'linktree': 'src/linktree/extractors/linktree_analytics_extractor.py',
            'metaads': 'src/metaads/extractors/meta_ads_extractor.py'
        }
        
        script = manual_scripts.get(service)
        if script:
            script_path = self.project_root / script
            if script_path.exists():
                return script_path
        return None


def run_service_extractors(service: str, checker: ServiceAuthChecker, interactive: bool = True) -> bool:
    """Run extractors for a specific service."""
    print(f"\n{'='*60}")
    print(f"Checking {service.upper()} authentication...")
    print(f"{'='*60}")
    
    # Check cookie freshness
    is_fresh, message = checker.check_cookie_freshness(service)
    print(f"Cookie status: {message}")
    
    if not is_fresh:
        if not interactive:
            print(f"⚠️  WARNING: {service} authentication expired. Skipping in automated mode.")
            return False
        
        print(f"\n❗ {service} requires manual authentication!")
        extractor_script = checker.get_extractor_script(service)
        
        if extractor_script:
            print(f"Opening browser for manual login...")
            print(f"Script: {extractor_script}")
            
            # Run the extractor script with headless=False for manual auth
            env = os.environ.copy()
            env['HEADLESS'] = 'False'
            
            try:
                subprocess.run(
                    [sys.executable, str(extractor_script)],
                    env=env,
                    cwd=str(PROJECT_ROOT)
                )
                print(f"✅ {service} authentication completed!")
                return True
            except subprocess.CalledProcessError as e:
                print(f"❌ Error during {service} authentication: {e}")
                return False
        else:
            print(f"❌ No manual authentication script found for {service}")
            return False
    else:
        print(f"✅ {service} cookies are fresh. Running extractors...")
        
        # Run all extractors for this service
        extractor_dir = PROJECT_ROOT / f"src/{service}/extractors"
        if extractor_dir.exists():
            extractors = list(extractor_dir.glob("*.py"))
            extractors = [e for e in extractors if not e.name.startswith('_')]
            
            for extractor in extractors:
                print(f"\nRunning {extractor.name}...")
                try:
                    subprocess.run(
                        [sys.executable, str(extractor)],
                        cwd=str(PROJECT_ROOT),
                        check=True
                    )
                    print(f"✅ {extractor.name} completed")
                except subprocess.CalledProcessError as e:
                    print(f"❌ {extractor.name} failed: {e}")
                    if interactive:
                        response = input("Continue with other extractors? (y/n): ")
                        if response.lower() != 'y':
                            return False
        
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Run data pipeline with authentication checks"
    )
    parser.add_argument(
        '--services',
        nargs='+',
        help='Specific services to run (default: all)',
        choices=['spotify', 'tiktok', 'distrokid', 'toolost', 'linktree', 'metaads']
    )
    parser.add_argument(
        '--automated',
        action='store_true',
        help='Run in automated mode (skip manual auth prompts)'
    )
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check authentication status, don\'t run extractors'
    )
    
    args = parser.parse_args()
    
    checker = ServiceAuthChecker()
    services = args.services or ['spotify', 'tiktok', 'distrokid', 'toolost', 'linktree', 'metaads']
    interactive = not args.automated
    
    print("="*60)
    print("BEDROT Data Pipeline - Authentication Check")
    print(f"Mode: {'Interactive' if interactive else 'Automated'}")
    print(f"Services: {', '.join(services)}")
    print("="*60)
    
    if args.check_only:
        print("\nAuthentication Status Report:")
        print("-"*60)
        for service in services:
            is_fresh, message = checker.check_cookie_freshness(service)
            status = "✅ OK" if is_fresh else "❌ EXPIRED"
            print(f"{service:12} {status:10} - {message}")
        return
    
    # Run extractors for each service
    failed_services = []
    for service in services:
        success = run_service_extractors(service, checker, interactive)
        if not success:
            failed_services.append(service)
        
        # Small delay between services
        time.sleep(2)
    
    # Summary
    print("\n" + "="*60)
    print("EXTRACTION SUMMARY")
    print("="*60)
    
    successful = [s for s in services if s not in failed_services]
    if successful:
        print(f"✅ Successful: {', '.join(successful)}")
    
    if failed_services:
        print(f"❌ Failed/Skipped: {', '.join(failed_services)}")
        
        if interactive:
            print("\nTo retry failed services:")
            for service in failed_services:
                script = checker.get_extractor_script(service)
                if script:
                    print(f"  python {script.relative_to(PROJECT_ROOT)}")
    
    # Run cleaners regardless of extraction success
    print("\n" + "="*60)
    print("Running cleaners...")
    print("="*60)
    
    cleaner_script = PROJECT_ROOT / "cronjob" / "run_datalake_cron_no_extractors.bat"
    if cleaner_script.exists():
        subprocess.run([str(cleaner_script)], cwd=str(PROJECT_ROOT))
    else:
        print("⚠️  Cleaner script not found. Run manually:")
        print("  cronjob/run_datalake_cron_no_extractors.bat")


if __name__ == "__main__":
    main()