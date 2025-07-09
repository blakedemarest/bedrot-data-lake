#!/usr/bin/env python3
"""
Manual cookie import for DistroKid
Since we're in WSL, we'll need to manually export cookies from Brave
"""
import json
from pathlib import Path
from datetime import datetime
import sys

def convert_brave_export_to_playwright(brave_cookies_json):
    """
    Convert cookies exported from Brave DevTools to Playwright format
    
    To export cookies from Brave:
    1. Open DistroKid in Brave
    2. Press F12 to open DevTools
    3. Go to Application tab -> Storage -> Cookies
    4. Select all cookies (Ctrl+A)
    5. Copy them (Ctrl+C)
    6. Paste into a JSON file
    """
    print("Converting Brave cookies to Playwright format...")
    
    # Read the exported cookies
    with open(brave_cookies_json, 'r') as f:
        raw_cookies = json.load(f)
    
    # If it's already in the right format, just use it
    if isinstance(raw_cookies, list) and all('name' in c and 'value' in c for c in raw_cookies):
        cookies = raw_cookies
    else:
        print("ERROR: Invalid cookie format. Expected a list of cookie objects.")
        return False
    
    # Convert to Playwright format
    playwright_cookies = []
    for cookie in cookies:
        playwright_cookie = {
            'name': cookie.get('name'),
            'value': cookie.get('value'),
            'domain': cookie.get('domain', '.distrokid.com'),
            'path': cookie.get('path', '/'),
            'httpOnly': cookie.get('httpOnly', False),
            'secure': cookie.get('secure', True),
            'sameSite': cookie.get('sameSite', 'Lax')
        }
        
        # Handle expires
        if 'expirationDate' in cookie:
            playwright_cookie['expires'] = int(cookie['expirationDate'])
        elif 'expires' in cookie:
            playwright_cookie['expires'] = int(cookie['expires'])
        
        playwright_cookies.append(playwright_cookie)
    
    # Save cookies
    cookies_dir = Path(__file__).parent / 'cookies'
    cookies_dir.mkdir(exist_ok=True)
    
    cookies_file = cookies_dir / 'distrokid_cookies.json'
    
    # Backup existing cookies
    if cookies_file.exists():
        backup_file = cookies_dir / f'distrokid_cookies_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        print(f"Backing up existing cookies to {backup_file.name}")
        cookies_file.rename(backup_file)
    
    # Save new cookies
    with open(cookies_file, 'w') as f:
        json.dump(playwright_cookies, f, indent=2)
    
    print(f"Successfully converted {len(playwright_cookies)} cookies to {cookies_file}")
    print("\nCookie names imported:")
    for cookie in playwright_cookies:
        print(f"  - {cookie['name']}")
    
    return True

def main():
    print("DistroKid Cookie Import Tool")
    print("=" * 50)
    print("\nInstructions:")
    print("1. Open DistroKid in Brave browser and log in")
    print("2. Press F12 to open DevTools")
    print("3. Go to Application tab -> Storage -> Cookies -> https://distrokid.com")
    print("4. Select all cookies (click on first, Shift+click on last)")
    print("5. Right-click and select 'Copy as JSON'")
    print("6. Save to a file and provide the path below")
    print()
    
    if len(sys.argv) > 1:
        cookie_file = sys.argv[1]
    else:
        cookie_file = input("Enter path to exported cookies JSON file: ").strip()
    
    if not Path(cookie_file).exists():
        print(f"ERROR: File not found: {cookie_file}")
        return
    
    convert_brave_export_to_playwright(cookie_file)

if __name__ == "__main__":
    main()