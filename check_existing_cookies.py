#!/usr/bin/env python3
"""
Simple diagnostic script to check what cookie files actually exist.
"""
import os
import json
from pathlib import Path
from datetime import datetime

def check_cookies():
    """Check all existing cookie files."""
    print("\n" + "=" * 80)
    print("BEDROT Cookie Files Diagnostic")
    print("=" * 80 + "\n")
    
    # Define where to look for cookies
    base_path = Path(__file__).parent / 'src'
    
    services = ['distrokid', 'spotify', 'tiktok', 'toolost', 'linktree']
    
    total_found = 0
    
    for service in services:
        print(f"\n📁 {service.upper()}")
        print("-" * 40)
        
        # Check for cookie files
        cookie_dir = base_path / service / 'cookies'
        
        if not cookie_dir.exists():
            print(f"  ❌ Cookie directory not found: {cookie_dir}")
            continue
            
        # Look for cookie files
        cookie_files = list(cookie_dir.glob('*.json'))
        
        if not cookie_files:
            print(f"  ⚠️  No cookie files found in {cookie_dir}")
        else:
            for cookie_file in cookie_files:
                total_found += 1
                print(f"\n  📄 Found: {cookie_file.name}")
                
                try:
                    # Read and analyze cookie file
                    with open(cookie_file, 'r') as f:
                        cookies = json.load(f)
                    
                    if isinstance(cookies, list):
                        print(f"     Cookies: {len(cookies)} cookies")
                        
                        # Check expiration
                        expired_count = 0
                        for cookie in cookies:
                            if isinstance(cookie, dict):
                                # Handle different date formats
                                exp_field = cookie.get('expirationDate') or cookie.get('expires')
                                if exp_field:
                                    try:
                                        # Convert to datetime
                                        if isinstance(exp_field, (int, float)):
                                            exp_time = datetime.fromtimestamp(exp_field)
                                        else:
                                            exp_time = datetime.fromisoformat(exp_field.replace('Z', '+00:00'))
                                        
                                        if exp_time < datetime.now():
                                            expired_count += 1
                                    except:
                                        pass
                        
                        if expired_count > 0:
                            print(f"     ⚠️  Expired: {expired_count} cookies")
                        else:
                            print(f"     ✅ All cookies valid")
                            
                        # Show file modification time
                        mtime = datetime.fromtimestamp(cookie_file.stat().st_mtime)
                        days_old = (datetime.now() - mtime).days
                        print(f"     Last Modified: {mtime.strftime('%Y-%m-%d %H:%M')} ({days_old} days ago)")
                        
                    else:
                        print(f"     ❓ Unexpected format: {type(cookies)}")
                        
                except Exception as e:
                    print(f"     ❌ Error reading file: {e}")
    
    print("\n" + "=" * 80)
    print(f"SUMMARY: Found {total_found} cookie files")
    print("=" * 80 + "\n")
    
    if total_found == 0:
        print("⚠️  No cookie files found!")
        print("\nThis is normal if you haven't run the extractors yet.")
        print("To create initial cookies, run the extractors manually:")
        print("  - python src/spotify/extractors/spotify_audience_extractor.py")
        print("  - python src/distrokid/extractors/dk_auth.py")
        print("  - etc.")
    else:
        print("✅ Cookie files exist. The refresh system can manage these.")
        print("\nTo refresh expired cookies:")
        print("  python cookie_refresh.py --refresh SERVICE_NAME")

if __name__ == "__main__":
    check_cookies()