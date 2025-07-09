#!/usr/bin/env python3
"""
Automated TooLost scraper that works with saved cookies for unattended execution.
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from common.cookies import load_cookies_async

load_dotenv()

PROJECT_ROOT = os.getenv("PROJECT_ROOT", str(Path(__file__).resolve().parents[3]))
DEFAULT_SESSION_DIR = str(Path(PROJECT_ROOT) / "src" / ".playwright_toolost_session")
SESSION_DIR = os.getenv("PLAYWRIGHT_SESSION_DIR", DEFAULT_SESSION_DIR)
OUTPUT_DIR = Path(PROJECT_ROOT) / "landing" / "toolost" / "streams"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TOOLOST_URL = "https://toolost.com/user-portal/analytics/platform"
SPOTIFY_API = "https://toolost.com/api/portal/analytics/spotify?release=&date=thisYear"
APPLE_API = "https://toolost.com/api/portal/analytics/apple/?release=&date=thisYear"


async def _launch_browser(p):
    """Launch browser with persistent context."""
    os.makedirs(SESSION_DIR, exist_ok=True)
    browser = await p.chromium.launch_persistent_context(
        SESSION_DIR,
        headless=True,  # Run headless for automation
        viewport={"width": 1280, "height": 900},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    )
    # Load cookies if not already imported
    await load_cookies_async(browser, "toolost")
    page = browser.pages[0] if browser.pages else await browser.new_page()
    return browser, page


async def _check_if_logged_in(page):
    """Check if already logged in to TooLost."""
    try:
        # Navigate to a protected page
        await page.goto(TOOLOST_URL, wait_until="networkidle", timeout=30000)
        
        # Check for dashboard elements
        dashboard_selectors = [
            "nav", "aside", ".ant-layout-sider", 
            ".dashboard", "[data-testid*=user-menu]",
            ".analytics", "main"
        ]
        
        for selector in dashboard_selectors:
            try:
                element = await page.wait_for_selector(selector, timeout=5000)
                if element:
                    print(f"[TOOLOST] Already logged in - found {selector}")
                    return True
            except:
                continue
        
        # Check if redirected to login
        if "login" in page.url.lower():
            print("[TOOLOST] Not logged in - at login page")
            return False
            
        return True
        
    except Exception as e:
        print(f"[TOOLOST] Error checking login status: {e}")
        return False


def _setup_response_capture(page):
    """Set up network response capturing."""
    api_results = {"spotify": None, "apple": None}
    responses = []
    now = datetime.now().strftime("%Y%m%d_%H%M%S")

    async def handle_response(response):
        if SPOTIFY_API in response.url and response.status == 200:
            api_results["spotify"] = await response.json()
        elif APPLE_API in response.url and response.status == 200:
            api_results["apple"] = await response.json()
        responses.append({
            "url": response.url,
            "status": response.status,
            "timestamp": datetime.now().isoformat()
        })

    page.on("response", handle_response)
    return api_results, responses, now


async def _save_if_available(platform, api_results, responses, path):
    """Save API results if available."""
    if api_results[platform]:
        with open(path, "w") as f:
            json.dump(api_results[platform], f, indent=2)
        print(f"[TOOLOST] Saved {platform} data to {path}")
    else:
        print(f"[TOOLOST] No {platform} data captured")


async def _select_this_year(page):
    """Select 'This Year' date range."""
    try:
        await page.wait_for_selector("[class*=ant-picker], [data-testid*=date], [role=button]", state="visible")
        await page.click("[class*=ant-picker], [data-testid*=date], [role=button]")
        await asyncio.sleep(1)
        try:
            await page.click("text=This Year")
        except Exception:
            await page.click("text=Year")
        await asyncio.sleep(2)
    except Exception:
        print("[TOOLOST] Date picker not found.")


async def _switch_to_apple(page):
    """Switch platform selector to Apple."""
    try:
        await page.click("[role=button]:has-text('Spotify'), [data-testid*=platform], .ant-select-selector")
        await page.wait_for_selector("div.d-flex.align-center.flex-row")
        for option in await page.query_selector_all("div.d-flex.align-center.flex-row"):
            if (await option.inner_text()).strip() == "Apple":
                await option.click()
                break
    except Exception as e:
        print(f"Failed to click Apple platform option: {e}")
    await asyncio.sleep(2)


async def main():
    """Main extraction routine."""
    async with async_playwright() as p:
        browser, page = await _launch_browser(p)
        
        # Check if logged in
        if not await _check_if_logged_in(page):
            print("[TOOLOST] ERROR: Not logged in and running in automated mode.")
            print("[TOOLOST] Please run the interactive scraper first to log in:")
            print("[TOOLOST]   python src/toolost/extractors/toolost_scraper.py")
            await browser.close()
            return 1
        
        # Navigate to analytics
        await page.goto(TOOLOST_URL, wait_until="networkidle")
        
        # Set up response capture
        api_results, responses, now = _setup_response_capture(page)
        
        # Select date range
        await _select_this_year(page)
        
        # Capture Spotify data
        print("[TOOLOST] Waiting for Spotify API call...")
        for _ in range(30):
            if api_results["spotify"]:
                break
            await asyncio.sleep(1)
        
        spotify_file = OUTPUT_DIR / f"toolost_spotify_{now}.json"
        await _save_if_available("spotify", api_results, responses, spotify_file)
        
        # Switch to Apple and capture data
        await _switch_to_apple(page)
        print("[TOOLOST] Waiting for Apple Music API call...")
        for _ in range(30):
            if api_results["apple"]:
                break
            await asyncio.sleep(1)
        
        apple_file = OUTPUT_DIR / f"toolost_apple_{now}.json"
        await _save_if_available("apple", api_results, responses, apple_file)
        
        # Check if we got any data
        if not api_results["spotify"] and not api_results["apple"]:
            print("[TOOLOST] WARNING: No data captured. Possible issues:")
            print("[TOOLOST]   - Cookies may have expired")
            print("[TOOLOST]   - API endpoints may have changed")
            print("[TOOLOST]   - Network issues")
            await browser.close()
            return 1
        
        print("[TOOLOST] Data collection complete.")
        await browser.close()
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)