#!/usr/bin/env python3
"""
Import DistroKid cookies from Brave browser
"""
import json
import browser_cookie3
from pathlib import Path
import os
from datetime import datetime

def import_distrokid_cookies():
    """Import DistroKid cookies from Brave browser"""
    print("Attempting to import DistroKid cookies from Brave browser...")
    
    try:
        # Get cookies from Brave
        cj = browser_cookie3.brave(domain_name='distrokid.com')
        
        # Convert to Playwright format
        cookies = []
        for cookie in cj:
            cookie_dict = {
                'name': cookie.name,
                'value': cookie.value,
                'domain': cookie.domain,
                'path': cookie.path,
                'httpOnly': cookie.domain.startswith('.'),
                'secure': cookie.secure if hasattr(cookie, 'secure') else True,
                'sameSite': 'Lax'
            }
            
            # Add expiry if available
            if hasattr(cookie, 'expires') and cookie.expires:
                cookie_dict['expires'] = cookie.expires
            
            cookies.append(cookie_dict)
        
        if not cookies:
            print("No DistroKid cookies found in Brave browser")
            return False
        
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
            json.dump(cookies, f, indent=2)
        
        print(f"Successfully imported {len(cookies)} cookies to {cookies_file}")
        print("\nCookie names imported:")
        for cookie in cookies:
            print(f"  - {cookie['name']}")
        
        return True
        
    except Exception as e:
        print(f"Error importing cookies: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Brave browser is closed")
        print("2. Ensure you're logged into DistroKid in Brave")
        print("3. Try running with sudo if on Linux")
        return False

if __name__ == "__main__":
    import_distrokid_cookies()