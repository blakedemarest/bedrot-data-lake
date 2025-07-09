#!/usr/bin/env python3
"""
Production cookie status checker that works with existing cookie files.
"""
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class CookieChecker:
    """Simple cookie status checker."""
    
    def __init__(self):
        self.base_path = Path(__file__).parent / 'src'
        self.services = {
            'distrokid': {'max_days': 14, 'critical': False},
            'spotify': {'max_days': 30, 'critical': False},
            'tiktok': {'max_days': 30, 'critical': False, 'accounts': ['pig1987', 'zonea0']},
            'toolost': {'max_days': 7, 'critical': True},  # JWT expires fast!
            'linktree': {'max_days': 30, 'critical': False}
        }
    
    def check_cookie_file(self, file_path: Path) -> Tuple[bool, int, int]:
        """Check a cookie file and return (is_valid, days_remaining, expired_count)."""
        try:
            with open(file_path, 'r') as f:
                cookies = json.load(f)
            
            if not isinstance(cookies, list):
                return False, 0, 0
            
            now = datetime.now()
            min_expiry = None
            expired_count = 0
            
            for cookie in cookies:
                if isinstance(cookie, dict):
                    # Handle both field names
                    exp_field = cookie.get('expirationDate') or cookie.get('expires')
                    if exp_field:
                        try:
                            # Convert timestamp to datetime
                            if isinstance(exp_field, (int, float)):
                                exp_time = datetime.fromtimestamp(exp_field)
                            else:
                                exp_time = datetime.fromisoformat(exp_field.replace('Z', '+00:00'))
                            
                            if exp_time < now:
                                expired_count += 1
                            else:
                                # This cookie is not expired, check if it's the earliest expiration
                                if min_expiry is None or exp_time < min_expiry:
                                    min_expiry = exp_time
                        except:
                            pass
            
            # Calculate days remaining
            if min_expiry:
                delta = min_expiry - now
                days_remaining = delta.days
                # Fixed: check if cookies are actually expired, not just days remaining
                is_valid = min_expiry > now and expired_count == 0
            else:
                days_remaining = 0
                is_valid = False
            
            return is_valid, days_remaining, expired_count
            
        except Exception as e:
            return False, 0, 0
    
    def get_cookie_status(self, service: str, account: Optional[str] = None) -> Dict:
        """Get status for a specific service/account."""
        cookie_dir = self.base_path / service / 'cookies'
        
        if account:
            cookie_file = cookie_dir / f'{service}_cookies_{account}.json'
        else:
            cookie_file = cookie_dir / f'{service}_cookies.json'
        
        if not cookie_file.exists():
            return {
                'exists': False,
                'is_valid': False,
                'days_remaining': 0,
                'message': 'No cookie file found'
            }
        
        is_valid, days_remaining, expired_count = self.check_cookie_file(cookie_file)
        
        # Get file age
        mtime = datetime.fromtimestamp(cookie_file.stat().st_mtime)
        file_age_days = (datetime.now() - mtime).days
        
        return {
            'exists': True,
            'is_valid': is_valid,
            'days_remaining': days_remaining,
            'expired_count': expired_count,
            'file_age_days': file_age_days,
            'last_modified': mtime.strftime('%Y-%m-%d %H:%M'),
            'file_path': str(cookie_file),
            'message': self._get_status_message(is_valid, days_remaining, expired_count)
        }
    
    def _get_status_message(self, is_valid: bool, days_remaining: int, expired_count: int) -> str:
        """Generate status message."""
        if not is_valid:
            if expired_count > 0:
                return f"EXPIRED: {expired_count} cookies expired - refresh needed!"
            else:
                return "EXPIRED: All cookies expired - refresh needed!"
        elif days_remaining <= 3:
            return f"WARNING: Expires in {days_remaining} days - refresh soon!"
        else:
            return f"VALID: {days_remaining} days remaining"
    
    def print_status_report(self):
        """Print a comprehensive status report."""
        print("\n" + "=" * 80)
        print("BEDROT Cookie Status Report")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80 + "\n")
        
        critical_issues = []
        warnings = []
        
        for service, config in self.services.items():
            print(f"{service.upper()}")
            print("-" * 40)
            
            if 'accounts' in config:
                # Multi-account service
                for account in config['accounts']:
                    status = self.get_cookie_status(service, account)
                    self._print_service_status(f"{account}", status, config, critical_issues, warnings)
            else:
                # Single account service
                status = self.get_cookie_status(service)
                self._print_service_status(service, status, config, critical_issues, warnings)
            
            print()
        
        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        if critical_issues:
            print("\nCRITICAL ISSUES (Immediate action required):")
            for issue in critical_issues:
                print(f"  - {issue}")
        
        if warnings:
            print("\nWARNINGS (Action recommended):")
            for warning in warnings:
                print(f"  - {warning}")
        
        if not critical_issues and not warnings:
            print("\nAll cookies are healthy!")
        
        # Recommendations
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        
        if critical_issues or warnings:
            print("\nTo refresh cookies manually:")
            print("1. Run the extractor for the service:")
            print("   python src/<service>/extractors/<extractor_name>.py")
            print("\n2. Or use the cookie refresh system:")
            print("   python cookie_refresh.py --refresh <service>")
            
            if any('toolost' in issue.lower() for issue in critical_issues):
                print("\nWARNING: TOOLOST REQUIRES WEEKLY REFRESH (JWT tokens expire in 7 days)!")
    
    def _print_service_status(self, name: str, status: Dict, config: Dict, critical_issues: List, warnings: List):
        """Print status for a single service."""
        if not status['exists']:
            print(f"  {name}: No cookies found")
            if config.get('critical'):
                critical_issues.append(f"{name}: No cookies found")
            return
        
        print(f"  {name}: {status['message']}")
        print(f"  Last updated: {status['last_modified']} ({status['file_age_days']} days ago)")
        
        # Add to issues if needed
        if not status['is_valid']:
            if config.get('critical'):
                critical_issues.append(f"{name}: {status['message']}")
            else:
                warnings.append(f"{name}: {status['message']}")
        elif status['days_remaining'] <= 3:
            if config.get('critical'):
                critical_issues.append(f"{name}: {status['message']}")
            else:
                warnings.append(f"{name}: {status['message']}")

def main():
    """Run the cookie status checker."""
    checker = CookieChecker()
    checker.print_status_report()
    
    # Return exit code based on critical issues
    # (You can use this in batch files to check status)
    return 0

if __name__ == "__main__":
    exit(main())