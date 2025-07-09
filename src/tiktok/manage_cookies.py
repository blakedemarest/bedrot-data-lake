#!/usr/bin/env python3
"""
TikTok Cookie Management Tool

This script helps manage cookies for multiple TikTok accounts, allowing you to:
1. Export cookies from a browser session
2. Share cookies between accounts (with caution)
3. Validate existing cookie files
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
import argparse
import shutil

PROJECT_ROOT = os.environ.get('PROJECT_ROOT')
if not PROJECT_ROOT:
    print("ERROR: PROJECT_ROOT environment variable must be set.")
    sys.exit(1)

COOKIE_DIR = Path(PROJECT_ROOT) / "src" / "tiktok" / "cookies"
COOKIE_DIR.mkdir(parents=True, exist_ok=True)


def list_cookie_files():
    """List all available cookie files."""
    print("\n=== Available Cookie Files ===")
    cookie_files = list(COOKIE_DIR.glob("tiktok_cookies_*.json"))
    if not cookie_files:
        print("No cookie files found.")
        return []
    
    for file in cookie_files:
        account = file.stem.replace("tiktok_cookies_", "")
        size = file.stat().st_size
        modified = datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"  - {account}: {size} bytes, modified {modified}")
    
    return cookie_files


def validate_cookies(file_path):
    """Validate a cookie file structure."""
    try:
        with open(file_path, 'r') as f:
            cookies = json.load(f)
        
        if not isinstance(cookies, list):
            print(f"ERROR: Cookie file should contain a list, found {type(cookies)}")
            return False
        
        required_cookies = ['sessionid', 'sid_guard', 'uid_tt']
        found_cookies = {c.get('name') for c in cookies if isinstance(c, dict)}
        
        missing = set(required_cookies) - found_cookies
        if missing:
            print(f"WARNING: Missing important cookies: {missing}")
        
        print(f"✓ Cookie file contains {len(cookies)} cookies")
        print(f"✓ Found cookies: {', '.join(sorted(found_cookies))}")
        
        # Check expiration
        now = datetime.now().timestamp()
        expired = 0
        for cookie in cookies:
            if isinstance(cookie, dict) and 'expirationDate' in cookie:
                if cookie['expirationDate'] < now:
                    expired += 1
        
        if expired > 0:
            print(f"WARNING: {expired} cookies have expired")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to validate cookies: {e}")
        return False


def copy_cookies(source_account, target_account):
    """Copy cookies from one account to another."""
    source_file = COOKIE_DIR / f"tiktok_cookies_{source_account}.json"
    target_file = COOKIE_DIR / f"tiktok_cookies_{target_account}.json"
    
    if not source_file.exists():
        print(f"ERROR: Source cookie file not found: {source_file}")
        return False
    
    if target_file.exists():
        backup_file = target_file.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        shutil.copy2(target_file, backup_file)
        print(f"Backed up existing cookies to: {backup_file.name}")
    
    shutil.copy2(source_file, target_file)
    print(f"✓ Copied cookies from {source_account} to {target_account}")
    
    # Clear any existing import markers
    session_dirs = [
        Path(PROJECT_ROOT) / "src" / ".playwright_dk_session",
        Path(PROJECT_ROOT) / "src" / f".playwright_dk_session_{target_account}"
    ]
    
    for session_dir in session_dirs:
        marker_file = session_dir / f".tiktok_cookies_{target_account}_imported"
        if marker_file.exists():
            marker_file.unlink()
            print(f"✓ Cleared import marker: {marker_file.name}")
    
    return True


def export_browser_cookies():
    """Instructions for exporting cookies from browser."""
    print("\n=== How to Export Cookies from Browser ===")
    print("1. Install a cookie export extension (e.g., 'Cookie-Editor' for Chrome/Firefox)")
    print("2. Log into your TikTok account")
    print("3. Navigate to https://www.tiktok.com/tiktokstudio")
    print("4. Open the cookie extension and export all cookies for .tiktok.com")
    print("5. Save the JSON file to the cookies directory")
    print(f"   Location: {COOKIE_DIR}")
    print("6. Rename the file to: tiktok_cookies_<account_name>.json")
    print("\nIMPORTANT: Make sure you're logged into the correct account before exporting!")


def main():
    parser = argparse.ArgumentParser(description="Manage TikTok cookies for multiple accounts")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List command
    subparsers.add_parser('list', help='List available cookie files')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate a cookie file')
    validate_parser.add_argument('account', help='Account name (e.g., pig1987, zonea0)')
    
    # Copy command
    copy_parser = subparsers.add_parser('copy', help='Copy cookies between accounts')
    copy_parser.add_argument('source', help='Source account name')
    copy_parser.add_argument('target', help='Target account name')
    
    # Export instructions
    subparsers.add_parser('export-help', help='Show instructions for exporting cookies')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        list_cookie_files()
        return
    
    if args.command == 'list':
        list_cookie_files()
    
    elif args.command == 'validate':
        file_path = COOKIE_DIR / f"tiktok_cookies_{args.account}.json"
        if file_path.exists():
            validate_cookies(file_path)
        else:
            print(f"ERROR: Cookie file not found for account: {args.account}")
    
    elif args.command == 'copy':
        copy_cookies(args.source, args.target)
    
    elif args.command == 'export-help':
        export_browser_cookies()


if __name__ == "__main__":
    main()