#!/usr/bin/env python3
"""
Wrapper script for running extractors with authentication checks.
Handles cookie validation and prompts for manual authentication when needed.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import argparse

# Service configuration
AUTH_SERVICES = {
    "spotify": {
        "cookie_max_age_days": 30,
        "manual_script": "src/spotify/extractors/spotify_audience_extractor.py",
        "automated_scripts": [
            "src/spotify/extractors/spotify_audience_extractor.py"
        ]
    },
    "toolost": {
        "cookie_max_age_days": 7,
        "manual_script": "src/toolost/extractors/toolost_scraper.py",
        "automated_scripts": [
            "src/toolost/extractors/toolost_scraper_automated.py"
        ]
    },
    "distrokid": {
        "cookie_max_age_days": 14,
        "manual_script": "src/distrokid/extractors/dk_auth.py",
        "automated_scripts": [
            "src/distrokid/extractors/dk_auth.py"
        ]
    },
    "tiktok": {
        "cookie_max_age_days": 7,
        "manual_script": "src/tiktok/extractors/tiktok_analytics_extractor_zonea0.py",
        "automated_scripts": [
            "src/tiktok/extractors/tiktok_analytics_extractor_zonea0.py",
            "src/tiktok/extractors/tiktok_analytics_extractor_pig1987.py"
        ]
    },
    "linktree": {
        "cookie_max_age_days": 30,
        "manual_script": "src/linktree/extractors/linktree_analytics_extractor.py",
        "automated_scripts": [
            "src/linktree/extractors/linktree_analytics_extractor.py"
        ]
    },
    "metaads": {
        "cookie_max_age_days": 90,
        "manual_script": "src/metaads/extractors/meta_daily_campaigns_extractor.py",
        "automated_scripts": [
            "src/metaads/extractors/meta_daily_campaigns_extractor.py"
        ]
    }
}


def check_cookie_freshness(service: str) -> tuple[bool, str, int]:
    """
    Check if cookies for a service are fresh enough.
    Returns (is_fresh, reason, days_old)
    """
    project_root = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parents[2]))
    # Cookies are stored in each service's cookies directory
    cookie_file = project_root / "src" / service / "cookies" / f"{service}_cookies.json"
    
    # Special case for TikTok - check for multiple cookie files
    if service == "tiktok":
        cookie_dir = project_root / "src" / service / "cookies"
        if cookie_dir.exists():
            cookie_files = list(cookie_dir.glob("tiktok_cookies_*.json"))
            if cookie_files:
                # Use the most recently modified cookie file
                cookie_file = max(cookie_files, key=lambda f: f.stat().st_mtime)
    
    if not cookie_file.exists():
        return False, "Cookie file does not exist", -1
    
    try:
        # Check file age
        file_age = datetime.now() - datetime.fromtimestamp(cookie_file.stat().st_mtime)
        days_old = file_age.days
        max_age = AUTH_SERVICES[service]["cookie_max_age_days"]
        
        if days_old > max_age:
            return False, f"Cookies are {days_old} days old (max: {max_age})", days_old
        
        # Check cookie content
        with open(cookie_file) as f:
            cookies = json.load(f)
        
        if not cookies:
            return False, "Cookie file is empty", days_old
        
        # Check for expired cookies
        now = datetime.now().timestamp()
        expired_count = 0
        for cookie in cookies:
            if "expires" in cookie and cookie["expires"] > 0 and cookie["expires"] < now:
                expired_count += 1
        
        if expired_count > 0:
            return False, f"{expired_count} cookies have expired", days_old
        
        return True, f"Cookies are {days_old} days old and valid", days_old
        
    except Exception as e:
        return False, f"Error checking cookies: {e}", -1


def run_manual_auth(service: str) -> bool:
    """
    Run manual authentication for a service.
    Returns True if successful.
    """
    if service not in AUTH_SERVICES:
        print(f"[AUTH] Unknown service: {service}")
        return False
    
    manual_script = AUTH_SERVICES[service]["manual_script"]
    
    print("\n" + "="*70)
    print(f"MANUAL AUTHENTICATION REQUIRED FOR {service.upper()}")
    print("="*70)
    print(f"Running: python {manual_script}")
    print("Please complete the login process in the browser window.")
    print("="*70 + "\n")
    
    try:
        # Run the manual authentication script
        result = subprocess.run(
            f"python {manual_script}",
            shell=True,
            cwd=os.getenv("PROJECT_ROOT"),
            capture_output=False  # Allow interactive input/output
        )
        
        if result.returncode == 0:
            print(f"\n[AUTH] ✅ Manual authentication for {service} completed successfully")
            return True
        else:
            print(f"\n[AUTH] ❌ Manual authentication for {service} failed")
            return False
            
    except Exception as e:
        print(f"\n[AUTH] ❌ Error running manual authentication: {e}")
        return False


def run_automated_extractors(service: str) -> bool:
    """
    Run automated extractors for a service.
    Returns True if all successful.
    """
    if service not in AUTH_SERVICES:
        print(f"[AUTH] Unknown service: {service}")
        return False
    
    all_success = True
    
    for script in AUTH_SERVICES[service]["automated_scripts"]:
        print(f"\n[AUTH] Running automated extractor: {script}")
        
        try:
            result = subprocess.run(
                f"python {script}",
                shell=True,
                cwd=os.getenv("PROJECT_ROOT"),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"[AUTH] ✅ {script} completed successfully")
                if result.stdout:
                    print(result.stdout)
            else:
                print(f"[AUTH] ❌ {script} failed with code {result.returncode}")
                if result.stderr:
                    print("STDERR:", result.stderr)
                if result.stdout:
                    print("STDOUT:", result.stdout)
                all_success = False
                
        except Exception as e:
            print(f"[AUTH] ❌ Error running {script}: {e}")
            all_success = False
    
    return all_success


def check_and_run_service(service: str, force_manual: bool = False) -> bool:
    """
    Check authentication status and run extractors for a service.
    Returns True if successful.
    """
    print(f"\n{'='*70}")
    print(f"Processing {service.upper()}")
    print('='*70)
    
    if force_manual:
        print(f"[AUTH] Forcing manual authentication for {service}")
        if not run_manual_auth(service):
            return False
    else:
        # Check cookie freshness
        is_fresh, reason, days_old = check_cookie_freshness(service)
        
        print(f"[AUTH] Cookie status for {service}: {reason}")
        
        if not is_fresh:
            # Determine if we should prompt for manual auth
            if days_old >= 0:  # Cookies exist but are old/expired
                print(f"\n[AUTH] ⚠️  Cookies for {service} need refresh")
                
                # In automated mode, skip services with expired cookies
                if os.getenv("AUTOMATED_MODE", "false").lower() == "true":
                    print(f"[AUTH] Skipping {service} - manual authentication required")
                    return False
                
                # Otherwise, prompt for manual auth
                response = input(f"\nRun manual authentication for {service}? (y/n): ").lower()
                if response == 'y':
                    if not run_manual_auth(service):
                        return False
                else:
                    print(f"[AUTH] Skipping {service} extractors")
                    return False
            else:
                # No cookies at all
                print(f"[AUTH] No cookies found for {service}")
                if os.getenv("AUTOMATED_MODE", "false").lower() == "true":
                    print(f"[AUTH] Skipping {service} - no cookies available")
                    return False
                
                response = input(f"\nSetup authentication for {service}? (y/n): ").lower()
                if response == 'y':
                    if not run_manual_auth(service):
                        return False
                else:
                    print(f"[AUTH] Skipping {service} extractors")
                    return False
    
    # Run automated extractors
    return run_automated_extractors(service)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run extractors with authentication checks")
    parser.add_argument("services", nargs="*", 
                       help="Services to process (default: all)")
    parser.add_argument("--manual", "-m", action="store_true",
                       help="Force manual authentication for all services")
    parser.add_argument("--check-only", "-c", action="store_true",
                       help="Only check authentication status, don't run extractors")
    
    args = parser.parse_args()
    
    # Determine which services to process
    if args.services:
        services = args.services
    else:
        services = list(AUTH_SERVICES.keys())
    
    # Validate services
    invalid_services = [s for s in services if s not in AUTH_SERVICES]
    if invalid_services:
        print(f"ERROR: Unknown services: {invalid_services}")
        print(f"Valid services: {list(AUTH_SERVICES.keys())}")
        return 1
    
    if args.check_only:
        # Just check status
        print("\nAUTHENTICATION STATUS CHECK")
        print("="*70)
        
        for service in services:
            is_fresh, reason, days_old = check_cookie_freshness(service)
            status = "✅ OK" if is_fresh else "❌ NEEDS REFRESH"
            print(f"{service:12} {status:20} {reason}")
        
        return 0
    
    # Process each service
    failed_services = []
    
    for service in services:
        if not check_and_run_service(service, force_manual=args.manual):
            failed_services.append(service)
    
    # Summary
    print("\n" + "="*70)
    print("EXTRACTION SUMMARY")
    print("="*70)
    
    successful = [s for s in services if s not in failed_services]
    
    if successful:
        print(f"✅ Successful: {', '.join(successful)}")
    
    if failed_services:
        print(f"❌ Failed: {', '.join(failed_services)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())