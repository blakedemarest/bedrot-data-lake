#!/usr/bin/env python3
"""
Unified TooLost extractor that supports both manual and automated modes.
- Manual mode: Opens browser for login and saves cookies
- Automated mode: Uses saved cookies for headless extraction
- Smart mode detection based on cookie freshness
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from common.cookies import load_cookies_async, save_cookies_async

load_dotenv()

PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parents[3]))
DEFAULT_SESSION_DIR = str(PROJECT_ROOT / "src" / ".playwright_toolost_session")
SESSION_DIR = os.getenv("PLAYWRIGHT_SESSION_DIR", DEFAULT_SESSION_DIR)

# Standardize output location - always use landing/toolost/
OUTPUT_DIR = PROJECT_ROOT / "landing" / "toolost"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TOOLOST_URL = "https://toolost.com/user-portal/analytics/platform"
SPOTIFY_API = "https://toolost.com/api/portal/analytics/spotify?release=&date=thisYear"
APPLE_API = "https://toolost.com/api/portal/analytics/apple/?release=&date=thisYear"

# Cookie freshness threshold (7 days)
COOKIE_MAX_AGE_DAYS = 7


class TooLostExtractor:
    def __init__(self, force_manual=False, headless=None):
        """
        Initialize the extractor.
        
        Args:
            force_manual: Force manual mode even if cookies exist
            headless: Override headless setting (None = auto-detect)
        """
        self.force_manual = force_manual
        self.headless = headless
        self.api_results = {"spotify": None, "apple": None}
        self.responses = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    async def check_cookie_freshness(self) -> tuple[bool, str]:
        """
        Check if cookies exist and are fresh enough for automated extraction.
        Returns (is_fresh, reason)
        """
        cookie_file = PROJECT_ROOT / "src" / "common" / "cookies" / "toolost_cookies.json"
        
        if not cookie_file.exists():
            return False, "Cookie file does not exist"
        
        try:
            # Check file age
            file_age = datetime.now() - datetime.fromtimestamp(cookie_file.stat().st_mtime)
            if file_age.days > COOKIE_MAX_AGE_DAYS:
                return False, f"Cookies are {file_age.days} days old (max: {COOKIE_MAX_AGE_DAYS})"
            
            # Check cookie content
            with open(cookie_file) as f:
                cookies = json.load(f)
            
            if not cookies:
                return False, "Cookie file is empty"
            
            # Check for expired cookies
            now = datetime.now().timestamp()
            for cookie in cookies:
                if "expires" in cookie and cookie["expires"] > 0 and cookie["expires"] < now:
                    return False, "Some cookies have expired"
            
            return True, f"Cookies are {file_age.days} days old and valid"
            
        except Exception as e:
            return False, f"Error checking cookies: {e}"
    
    async def launch_browser(self, p, headless: bool):
        """Launch browser with appropriate settings."""
        os.makedirs(SESSION_DIR, exist_ok=True)
        browser = await p.chromium.launch_persistent_context(
            SESSION_DIR,
            headless=headless,
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        
        # Load cookies if they exist
        await load_cookies_async(browser, "toolost")
        
        page = browser.pages[0] if browser.pages else await browser.new_page()
        return browser, page
    
    def setup_response_capture(self, page):
        """Set up network response capturing."""
        async def handle_response(response):
            if SPOTIFY_API in response.url and response.status == 200:
                self.api_results["spotify"] = await response.json()
                print(f"[TOOLOST] Captured Spotify data")
            elif APPLE_API in response.url and response.status == 200:
                self.api_results["apple"] = await response.json()
                print(f"[TOOLOST] Captured Apple data")
            
            self.responses.append({
                "url": response.url,
                "status": response.status,
                "timestamp": datetime.now().isoformat()
            })
        
        page.on("response", handle_response)
    
    async def check_if_logged_in(self, page) -> bool:
        """Check if already logged in to TooLost."""
        try:
            await page.goto(TOOLOST_URL, wait_until="networkidle", timeout=30000)
            
            # Check for dashboard elements
            dashboard_selectors = [
                "nav", "aside", ".ant-layout-sider", 
                ".dashboard", "[data-testid*=user-menu]",
                ".analytics", "main"
            ]
            
            for selector in dashboard_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        return True
                except:
                    continue
            
            # Check if redirected to login
            if "login" in page.url.lower():
                return False
            
            return True
            
        except Exception as e:
            print(f"[TOOLOST] Error checking login status: {e}")
            return False
    
    async def manual_login(self, page):
        """Handle manual login process."""
        print("\n" + "="*60)
        print("MANUAL LOGIN REQUIRED")
        print("="*60)
        print("Please log in to TooLost in the browser window.")
        print("Complete any 2FA if required.")
        print("The script will continue automatically once logged in.")
        print("="*60 + "\n")
        
        # Navigate to login page
        await page.goto("https://toolost.com/login", wait_until="networkidle")
        
        # Wait for successful login
        while True:
            try:
                await page.wait_for_selector(
                    "nav, aside, .ant-layout-sider, .dashboard, [data-testid*=user-menu]",
                    timeout=5000
                )
                print("[TOOLOST] Login successful!")
                break
            except:
                await asyncio.sleep(2)
        
        # Save cookies after successful login
        await save_cookies_async(page.context, "toolost")
        print("[TOOLOST] Cookies saved for future automated runs")
    
    async def select_date_range(self, page):
        """Select 'This Year' date range."""
        try:
            await page.wait_for_selector("[class*=ant-picker], [data-testid*=date], [role=button]", state="visible")
            await page.click("[class*=ant-picker], [data-testid*=date], [role=button]")
            await asyncio.sleep(1)
            
            # Try to click "This Year" or "Year"
            try:
                await page.click("text=This Year", timeout=2000)
            except:
                try:
                    await page.click("text=Year", timeout=2000)
                except:
                    print("[TOOLOST] Could not find date range selector")
            
            await asyncio.sleep(2)
        except Exception as e:
            print(f"[TOOLOST] Date picker error (non-critical): {e}")
    
    async def switch_to_apple(self, page):
        """Switch platform selector to Apple."""
        try:
            # Click the platform selector
            await page.click("[role=button]:has-text('Spotify'), [data-testid*=platform], .ant-select-selector")
            await asyncio.sleep(1)
            
            # Find and click Apple option
            await page.wait_for_selector("div.d-flex.align-center.flex-row", timeout=5000)
            options = await page.query_selector_all("div.d-flex.align-center.flex-row")
            
            for option in options:
                text = (await option.inner_text()).strip()
                if text == "Apple":
                    await option.click()
                    print("[TOOLOST] Switched to Apple Music")
                    break
            
            await asyncio.sleep(2)
        except Exception as e:
            print(f"[TOOLOST] Error switching to Apple (non-critical): {e}")
    
    async def save_data(self):
        """Save captured data to files."""
        success = True
        
        # Save Spotify data
        if self.api_results["spotify"]:
            spotify_file = OUTPUT_DIR / f"toolost_spotify_{self.timestamp}.json"
            with open(spotify_file, "w") as f:
                json.dump(self.api_results["spotify"], f, indent=2)
            print(f"[TOOLOST] Saved Spotify data to: {spotify_file}")
        else:
            print("[TOOLOST] WARNING: No Spotify data captured")
            success = False
        
        # Save Apple data
        if self.api_results["apple"]:
            apple_file = OUTPUT_DIR / f"toolost_apple_{self.timestamp}.json"
            with open(apple_file, "w") as f:
                json.dump(self.api_results["apple"], f, indent=2)
            print(f"[TOOLOST] Saved Apple data to: {apple_file}")
        else:
            print("[TOOLOST] WARNING: No Apple data captured")
            success = False
        
        # Save response log for debugging
        if self.responses:
            log_file = OUTPUT_DIR / f".extraction_log_{self.timestamp}.json"
            with open(log_file, "w") as f:
                json.dump({
                    "timestamp": self.timestamp,
                    "responses": self.responses,
                    "data_captured": {
                        "spotify": bool(self.api_results["spotify"]),
                        "apple": bool(self.api_results["apple"])
                    }
                }, f, indent=2)
        
        return success
    
    async def extract(self):
        """Main extraction logic."""
        # Determine mode
        if self.force_manual:
            mode = "manual"
            reason = "Forced by --manual flag"
            headless = False
        else:
            is_fresh, reason = await self.check_cookie_freshness()
            if is_fresh:
                mode = "automated"
                headless = True if self.headless is None else self.headless
            else:
                mode = "manual"
                headless = False
        
        print(f"\n[TOOLOST] Running in {mode.upper()} mode")
        print(f"[TOOLOST] Reason: {reason}")
        print(f"[TOOLOST] Headless: {headless}\n")
        
        async with async_playwright() as p:
            browser, page = await self.launch_browser(p, headless)
            
            try:
                # Check if logged in
                is_logged_in = await self.check_if_logged_in(page)
                
                if not is_logged_in:
                    if mode == "automated":
                        print("[TOOLOST] ERROR: Not logged in and running in automated mode.")
                        print("[TOOLOST] Cookies may have expired. Switching to manual mode...")
                        await browser.close()
                        # Restart in manual mode
                        self.force_manual = True
                        return await self.extract()
                    else:
                        await self.manual_login(page)
                        # Navigate back to analytics after login
                        await page.goto(TOOLOST_URL, wait_until="networkidle")
                
                # Set up response capture
                self.setup_response_capture(page)
                
                # Select date range
                await self.select_date_range(page)
                
                # Wait for Spotify data
                print("[TOOLOST] Waiting for Spotify API response...")
                for _ in range(30):
                    if self.api_results["spotify"]:
                        break
                    await asyncio.sleep(1)
                
                # Switch to Apple
                await self.switch_to_apple(page)
                
                # Wait for Apple data
                print("[TOOLOST] Waiting for Apple Music API response...")
                for _ in range(30):
                    if self.api_results["apple"]:
                        break
                    await asyncio.sleep(1)
                
                # Save data
                success = await self.save_data()
                
                if not success:
                    print("\n[TOOLOST] WARNING: Some data was not captured")
                    print("[TOOLOST] Possible causes:")
                    print("  - Network issues")
                    print("  - API changes")
                    print("  - UI changes")
                    if mode == "automated":
                        print("  - Try running with --manual flag")
                    return 1
                
                print("\n[TOOLOST] ✅ Extraction completed successfully")
                return 0
                
            finally:
                await browser.close()


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="TooLost unified data extractor")
    parser.add_argument("--manual", "-m", action="store_true", 
                       help="Force manual mode for login")
    parser.add_argument("--headless", action="store_true",
                       help="Run in headless mode (automated only)")
    parser.add_argument("--visible", action="store_true",
                       help="Run in visible mode (automated only)")
    
    args = parser.parse_args()
    
    # Determine headless setting
    headless = None
    if args.headless:
        headless = True
    elif args.visible:
        headless = False
    
    extractor = TooLostExtractor(force_manual=args.manual, headless=headless)
    exit_code = await extractor.extract()
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)