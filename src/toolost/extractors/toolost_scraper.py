import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

from dotenv import load_dotenv
load_dotenv()

# Shared persistent session directory
PROJECT_ROOT = os.getenv("PROJECT_ROOT", str(Path(__file__).resolve().parents[3]))
DEFAULT_SESSION_DIR = str(Path(PROJECT_ROOT) / "src" / ".playwright_dk_session")
SESSION_DIR = os.getenv("PLAYWRIGHT_SESSION_DIR", DEFAULT_SESSION_DIR)
# Output directory
# FIX: Use correct raw zone (PROJECT_ROOT/raw/toolost), not src/landing/toolost
PROJECT_ROOT = os.getenv("PROJECT_ROOT", PROJECT_ROOT)
OUTPUT_DIR = Path(PROJECT_ROOT) / "raw" / "toolost"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TOOLOST_URL = "https://toolost.com/user-portal/analytics/platform"
SPOTIFY_API = "https://toolost.com/api/portal/analytics/spotify?release=&date=thisYear"
APPLE_API = "https://toolost.com/api/portal/analytics/apple/?release=&date=thisYear"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            SESSION_DIR,
            headless=False,
            viewport={"width": 1280, "height": 900},
        )
        page = await browser.new_page()
        # 1. Launch Login Page
        LOGIN_URL = "https://toolost.com/login"
        print(f"[TOOLOST] Navigating to login page: {LOGIN_URL}")
        await page.goto(LOGIN_URL)


        # Wait for manual authentication
        print("[TOOLOST] Please log in to TooLost and complete any 2FA in the opened browser window.")
        # Wait for a known post-login DOM element (sidebar, dashboard, or user menu)
        while True:
            try:
                # Wait for a sidebar, dashboard header, or user menu that only appears when logged in
                await page.wait_for_selector("nav, aside, .ant-layout-sider, .dashboard, [data-testid*=user-menu]", timeout=2000)
                print("[TOOLOST] Authenticated dashboard detected!")
                break
            except Exception:
                pass
            await asyncio.sleep(2)
        # Now navigate to analytics dashboard (explicit correct URL)
        ANALYTICS_URL = "https://toolost.com/user-portal/analytics/platform"
        print(f"[TOOLOST] Navigating to analytics dashboard: {ANALYTICS_URL}")
        await page.goto(ANALYTICS_URL)
        try:
            await page.wait_for_selector("main, .ant-layout-content, .analytics, .dashboard", timeout=10000)
            print("[TOOLOST] Analytics dashboard loaded!")
        except Exception:
            print("[TOOLOST] Dashboard selector not found, but URL is correct. Proceeding after fallback delay.")
            await asyncio.sleep(3)


        # Set up response capture for timestamped filenames
        api_results = {"spotify": None, "apple": None}
        responses = {"spotify": None, "apple": None}
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        def handle_response(response):
            url = response.url
            if url.startswith(SPOTIFY_API):
                print("Captured Spotify API response.")
                api_results["spotify"] = asyncio.create_task(response.json())
            elif url.startswith(APPLE_API):
                print("Captured Apple API response.")
                api_results["apple"] = asyncio.create_task(response.json())
        page.on("response", handle_response)

        # Step 1: Automate date range selection ("This Year")
        print("Selecting date range: This Year...")
        # Wait for the date picker to be visible and enabled
        try:
            await page.wait_for_selector("[class*=ant-picker], [data-testid*=date], [role=button]", timeout=15000, state="visible")
            await asyncio.sleep(1)
            # Try a robust click sequence
            try:
                await page.click("[class*=ant-picker], [data-testid*=date], [role=button]:has-text('Last 30 Days')", timeout=5000)
            except Exception:
                # Fallback: click any available date picker
                try:
                    await page.click("[class*=ant-picker], [data-testid*=date], [role=button]", timeout=5000)
                except Exception:
                    print("[TOOLOST] Could not find a clickable date picker. Skipping date selection.")
            await asyncio.sleep(1)
            # Try to click 'This Year' or 'Year' option
            try:
                await page.click("text=This Year", timeout=3000)
            except Exception:
                try:
                    await page.click("text=Year", timeout=3000)
                except Exception:
                    print("[TOOLOST] Could not find 'This Year' or 'Year' in dropdown. Please update selector if needed.")
            await asyncio.sleep(2)
        except Exception:
            print("[TOOLOST] Date picker not found after dashboard load. Skipping date selection.")

        # Wait for Spotify API call
        print("Waiting for Spotify API call for full year...")
        for _ in range(30):
            if api_results["spotify"]:
                break
            await asyncio.sleep(1)
        if api_results["spotify"]:
            responses["spotify"] = await api_results["spotify"]
            spotify_path = OUTPUT_DIR / f"toolost_spotify_{now}.json"
            with open(spotify_path, "w", encoding="utf-8") as f:
                json.dump(responses["spotify"], f, indent=2)
            print(f"Saved Spotify analytics to {spotify_path}")
        else:
            print("Spotify API response not captured. Please check selectors or page behavior.")

        # Step 2: Switch platform to Apple Music
        print("Switching platform to Apple Music...")
        # Click platform dropdown
        try:
            await page.click("[role=button]:has-text('Spotify'), [data-testid*=platform], .ant-select-selector")
            print("Platform dropdown opened.")
            # Wait for any dropdown option to appear
            await page.wait_for_selector("div.d-flex.align-center.flex-row", timeout=5000)
            # Get all dropdown options
            option_elements = await page.query_selector_all("div.d-flex.align-center.flex-row")
            print(f"Found {len(option_elements)} dropdown options. Texts:")
            target_found = False
            for idx, option in enumerate(option_elements):
                text = (await option.inner_text()).strip()
                print(f"  Option {idx+1}: '{text}'")
                if text == "Apple":
                    await option.click()
                    print("Clicked Apple platform option.")
                    target_found = True
                    break
            if not target_found:
                print("[ERROR] No dropdown option with text 'Apple' found.")
        except Exception as e:
            print(f"Failed to click Apple platform option: {e}")
        await asyncio.sleep(2)

        # Wait for Apple API call (up to 60 seconds, log progress)
        print("Waiting for Apple Music API call for full year...")
        for i in range(60):
            if api_results["apple"]:
                break
            if i % 5 == 0:
                print(f"Still waiting for Apple Music API response... {i+1}s elapsed")
            await asyncio.sleep(1)
        if api_results["apple"]:
            responses["apple"] = await api_results["apple"]
            apple_path = OUTPUT_DIR / f"toolost_apple_{now}.json"
            with open(apple_path, "w", encoding="utf-8") as f:
                json.dump(responses["apple"], f, indent=2)
            print(f"Saved Apple analytics to {apple_path}")
        else:
            print("[WARNING] Apple Music API response not captured after 60 seconds. Please check selectors or try again.")

        # --- Now go to notifications and download latest sales report ---
        print("[TOOLOST] Navigating to notifications page...")
        NOTIFICATIONS_URL = "https://toolost.com/user-portal/notifications"
        await page.goto(NOTIFICATIONS_URL)
        try:
            await page.wait_for_selector("div.body-1.font-weight-bold.mb-1", timeout=10000)
        except Exception:
            print("[TOOLOST] Notification blocks not found after navigation. Proceeding anyway.")
        await asyncio.sleep(2)
        print("[TOOLOST] Looking for latest sales report notification...")
        import re
        retry_count = 0
        max_retries = 3
        found_report = False
        while retry_count < max_retries and not found_report:
            report_blocks = page.locator("div.body-1.font-weight-bold.mb-1")
            matching_blocks = await report_blocks.all_inner_texts()
            latest_idx = None
            for idx, text in enumerate(matching_blocks):
                if re.search(r"Your \\(\d{2}-\d{4}\\) Sales report has been generated", text):
                    latest_idx = idx
                    break
            if latest_idx is not None:
                print(f"[TOOLOST] Found sales report notification: {matching_blocks[latest_idx]}")
                # Try to find the corresponding attachment button (assume same index)
                attachment_buttons = page.locator("button:has-text('Attachment')")
                if await attachment_buttons.count() > latest_idx:
                    button = attachment_buttons.nth(latest_idx)
                    print("[TOOLOST] Downloading sales report attachment...")
                    async with page.expect_download() as download_info:
                        await button.click()
                    download = await download_info.value
                    filename = await download.suggested_filename()
                    LANDING_DIR = Path(PROJECT_ROOT) / "landing" / "toolost" / "streams"
                    LANDING_DIR.mkdir(parents=True, exist_ok=True)
                    save_path = LANDING_DIR / filename
                    await download.save_as(str(save_path))
                    print(f"[TOOLOST] Downloaded: {filename} to {save_path}")
                    found_report = True
                else:
                    print("[TOOLOST] Could not find matching attachment button for latest report.")
                    break
            else:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"[TOOLOST] No sales report notification found! Retrying in 7 seconds... (Attempt {retry_count+1}/{max_retries})")
                    await asyncio.sleep(7)
                else:
                    print("[TOOLOST] No sales report notification found after multiple attempts!")

        print("Data collection complete. You may now close the browser window to end the script.")
        await browser.close()
        print("Browser closed automatically after data collection. Workflow complete.")

if __name__ == "__main__":
    asyncio.run(main())
