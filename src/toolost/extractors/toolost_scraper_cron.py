#!/usr/bin/env python3
"""
Cron-friendly TooLost extractor that gracefully handles authentication issues.
Designed for automated pipeline execution without manual intervention.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import traceback

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parents[2]))

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("[TOOLOST] Playwright not available, skipping extraction")
    sys.exit(0)

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parents[3]))
OUTPUT_DIR = PROJECT_ROOT / "landing" / "toolost"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# TooLost endpoints
TOOLOST_PORTAL_URL = "https://toolost.com/user-portal/analytics/platform"
SPOTIFY_API = "https://toolost.com/api/portal/analytics/spotify?release=&date=thisYear"
APPLE_API = "https://toolost.com/api/portal/analytics/apple/?release=&date=thisYear"

# Cookie settings
COOKIE_MAX_AGE_DAYS = 7
COOKIE_FILE = PROJECT_ROOT / "src" / "toolost" / "cookies" / "toolost_cookies.json"


class CronTooLostExtractor:
    """TooLost extractor optimized for cron job execution."""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.api_results = {"spotify": None, "apple": None}
        self.extraction_successful = False
        
    def check_cookie_status(self) -> tuple[bool, str, Optional[datetime]]:
        """
        Check cookie file status.
        Returns (exists, status_message, last_modified)
        """
        if not COOKIE_FILE.exists():
            return False, "No cookie file found", None
            
        try:
            # Check file age
            last_modified = datetime.fromtimestamp(COOKIE_FILE.stat().st_mtime)
            file_age = datetime.now() - last_modified
            
            if file_age.days > COOKIE_MAX_AGE_DAYS:
                return False, f"Cookies expired ({file_age.days} days old, max: {COOKIE_MAX_AGE_DAYS})", last_modified
            
            # Check cookie content
            with open(COOKIE_FILE) as f:
                cookies = json.load(f)
            
            if not cookies:
                return False, "Cookie file is empty", last_modified
            
            return True, f"Cookies valid ({file_age.days} days old)", last_modified
            
        except Exception as e:
            return False, f"Error reading cookies: {e}", None
    
    async def load_cookies_to_context(self, context):
        """Load cookies into browser context."""
        try:
            with open(COOKIE_FILE) as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
            return True
        except Exception as e:
            print(f"[TOOLOST] Failed to load cookies: {e}")
            return False
    
    async def test_authentication(self, page) -> bool:
        """Test if current authentication works."""
        try:
            print("[TOOLOST] Testing authentication...")
            await page.goto(TOOLOST_PORTAL_URL, wait_until="networkidle", timeout=30000)
            
            # Check for dashboard elements indicating successful login
            dashboard_selectors = [
                "nav", "aside", ".ant-layout-sider", 
                ".dashboard", "[data-testid*=user-menu]",
                ".analytics", "main"
            ]
            
            for selector in dashboard_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        print("[TOOLOST] Authentication successful")
                        return True
                except:
                    continue
            
            # Check if redirected to login page
            if "login" in page.url.lower():
                print("[TOOLOST] Redirected to login - authentication failed")
                return False
            
            print("[TOOLOST] Could not verify authentication status")
            return False
            
        except Exception as e:
            print(f"[TOOLOST] Authentication test failed: {e}")
            return False
    
    async def extract_api_data(self, page) -> bool:
        """Extract data from TooLost APIs."""
        try:
            print("[TOOLOST] Extracting API data...")
            
            # Set up response capture
            api_data_captured = {"spotify": False, "apple": False}
            
            async def handle_response(response):
                try:
                    if SPOTIFY_API in response.url and response.status == 200:
                        self.api_results["spotify"] = await response.json()
                        api_data_captured["spotify"] = True
                        print("[TOOLOST] Captured Spotify data")
                    elif APPLE_API in response.url and response.status == 200:
                        self.api_results["apple"] = await response.json()
                        api_data_captured["apple"] = True
                        print("[TOOLOST] Captured Apple data")
                except Exception as e:
                    print(f"[TOOLOST] Error capturing response: {e}")
            
            page.on("response", handle_response)
            
            # Navigate to analytics page and trigger API calls
            await page.goto(TOOLOST_PORTAL_URL, wait_until="networkidle")
            
            # Wait a bit for API calls to complete
            await asyncio.sleep(5)
            
            # Try to trigger additional API calls by interacting with the page
            try:
                # Look for date picker or refresh button
                date_selectors = [
                    "[class*=ant-picker]", "[data-testid*=date]", 
                    "[role=button]", ".ant-btn", "button"
                ]
                
                for selector in date_selectors:
                    try:
                        await page.click(selector, timeout=2000)
                        await asyncio.sleep(1)
                        break
                    except:
                        continue
                
                # Wait for any additional API calls
                await asyncio.sleep(3)
                
            except Exception as e:
                print(f"[TOOLOST] Could not interact with date controls: {e}")
            
            return api_data_captured["spotify"] or api_data_captured["apple"]
            
        except Exception as e:
            print(f"[TOOLOST] API extraction failed: {e}")
            return False
    
    def save_extraction_results(self) -> bool:
        """Save extracted data to files."""
        try:
            saved_files = []
            
            # Save Spotify data
            if self.api_results["spotify"]:
                spotify_file = OUTPUT_DIR / f"spotify_analytics_{self.timestamp}.json"
                with open(spotify_file, 'w') as f:
                    json.dump({
                        "timestamp": self.timestamp,
                        "source": "toolost_api",
                        "platform": "spotify",
                        "data": self.api_results["spotify"]
                    }, f, indent=2)
                saved_files.append(str(spotify_file))
                print(f"[TOOLOST] Saved Spotify data to {spotify_file}")
            
            # Save Apple data
            if self.api_results["apple"]:
                apple_file = OUTPUT_DIR / f"apple_analytics_{self.timestamp}.json"
                with open(apple_file, 'w') as f:
                    json.dump({
                        "timestamp": self.timestamp,
                        "source": "toolost_api", 
                        "platform": "apple",
                        "data": self.api_results["apple"]
                    }, f, indent=2)
                saved_files.append(str(apple_file))
                print(f"[TOOLOST] Saved Apple data to {apple_file}")
            
            if saved_files:
                # Save extraction log
                log_file = OUTPUT_DIR / f"extraction_log_{self.timestamp}.json"
                with open(log_file, 'w') as f:
                    json.dump({
                        "timestamp": self.timestamp,
                        "extractor": "toolost_scraper_cron",
                        "status": "success",
                        "files_saved": saved_files,
                        "extraction_time": datetime.now().isoformat()
                    }, f, indent=2)
                
                return True
            else:
                print("[TOOLOST] No data was extracted")
                return False
                
        except Exception as e:
            print(f"[TOOLOST] Failed to save results: {e}")
            return False
    
    def create_failure_log(self, reason: str, cookie_status: str):
        """Create a log file documenting extraction failure."""
        try:
            failure_log = OUTPUT_DIR / f"extraction_failure_{self.timestamp}.json"
            with open(failure_log, 'w') as f:
                json.dump({
                    "timestamp": self.timestamp,
                    "extractor": "toolost_scraper_cron",
                    "status": "failed",
                    "reason": reason,
                    "cookie_status": cookie_status,
                    "recommendation": "Manual cookie refresh required",
                    "failure_time": datetime.now().isoformat()
                }, f, indent=2)
            print(f"[TOOLOST] Failure log saved to {failure_log}")
        except Exception as e:
            print(f"[TOOLOST] Could not save failure log: {e}")
    
    async def run_extraction(self) -> bool:
        """Run the extraction process."""
        print("[TOOLOST] Starting cron-friendly extraction...")
        
        # Check cookie status first
        cookie_valid, cookie_message, last_modified = self.check_cookie_status()
        print(f"[TOOLOST] Cookie status: {cookie_message}")
        
        if not cookie_valid:
            print(f"[TOOLOST] Cannot extract - {cookie_message}")
            self.create_failure_log("Invalid cookies", cookie_message)
            return False
        
        try:
            async with async_playwright() as p:
                # Launch browser in headless mode for cron
                browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                
                # Load cookies
                if not await self.load_cookies_to_context(context):
                    await browser.close()
                    self.create_failure_log("Failed to load cookies", cookie_message)
                    return False
                
                page = await context.new_page()
                
                # Test authentication
                if not await self.test_authentication(page):
                    await browser.close()
                    self.create_failure_log("Authentication failed", cookie_message)
                    return False
                
                # Extract data
                extraction_success = await self.extract_api_data(page)
                
                await browser.close()
                
                if extraction_success:
                    return self.save_extraction_results()
                else:
                    self.create_failure_log("No data extracted", cookie_message)
                    return False
                    
        except Exception as e:
            print(f"[TOOLOST] Extraction failed: {e}")
            print(f"[TOOLOST] Error details: {traceback.format_exc()}")
            self.create_failure_log(f"Exception: {str(e)}", cookie_message)
            return False


async def main():
    """Main entry point for cron execution."""
    print("="*60)
    print("TooLost Cron Extractor")
    print("="*60)
    
    extractor = CronTooLostExtractor()
    success = await extractor.run_extraction()
    
    if success:
        print("[TOOLOST] ✓ Extraction completed successfully")
        sys.exit(0)
    else:
        print("[TOOLOST] ⚠ Extraction failed - check logs for details")
        print("[TOOLOST] Pipeline will continue with other extractors")
        sys.exit(0)  # Don't fail the entire pipeline


if __name__ == "__main__":
    asyncio.run(main()) 