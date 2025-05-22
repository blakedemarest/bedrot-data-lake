import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

# Shared persistent session directory
SESSION_DIR = str(Path(__file__).resolve().parent.parent.parent / ".playwright_dk_session")
# Output directory
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "landing" / "toolost"
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
        print(f"Navigating to {TOOLOST_URL} ...")
        await page.goto(TOOLOST_URL)

        # --- CLICK LOGGING ---
        LOG_FILE = Path(__file__).parent / "toolost_click_selectors.log"
        async def log_click(event):
            # Evaluate in page context to get details
            selector = await page.evaluate('el => el.outerHTML', event.target)
            tag = await page.evaluate('el => el.tagName', event.target)
            text = await page.evaluate('el => el.innerText', event.target)
            classes = await page.evaluate('el => el.className', event.target)
            el_id = await page.evaluate('el => el.id', event.target)
            log_entry = f"TAG: {tag}\nTEXT: {text}\nCLASSES: {classes}\nID: {el_id}\nOUTER_HTML: {selector}\n{'-'*40}\n"
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_entry)
            print(f"[CLICK LOGGED] Tag: {tag}, Text: {text}, Classes: {classes}, ID: {el_id}")
        await page.expose_binding("log_click", lambda source, event: asyncio.create_task(log_click(event)))
        await page.evaluate("""
            document.addEventListener('click', function(event) {
                window.log_click(event);
            }, true);
        """)

        # Wait for manual authentication
        print("Please log in to TooLost and complete any 2FA in the opened browser window.")
        # Wait for a known post-login element or URL
        while True:
            url = page.url
            # Detect successful login at /user-portal (not just /analytics/platform)
            if "/user-portal" in url:
                print("Login detected. Navigating to analytics dashboard...")
                await page.goto(TOOLOST_URL)
                # Now wait for dashboard
                try:
                    # Try common content selectors; fallback if not found
                    await page.wait_for_selector("main, .ant-layout-content, .analytics, .dashboard", timeout=10000)
                    print("Analytics dashboard loaded!")
                    break
                except Exception:
                    print("Dashboard selector not found, but URL is correct. Proceeding after fallback delay.")
                    await asyncio.sleep(3)
                    break
            await asyncio.sleep(2)

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
        # Click date range dropdown
        await page.click("[class*=ant-picker], [data-testid*=date], [role=button]:has-text('Last 30 Days')")
        await asyncio.sleep(1)
        # Try to click 'This Year' or 'Year' option
        try:
            await page.click("text=This Year")
        except Exception:
            try:
                await page.click("text=Year")
            except Exception:
                print("Could not find 'This Year' or 'Year' in dropdown. Please update selector if needed.")
        await asyncio.sleep(2)

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

        print("Data collection complete. You may now close the browser window to end the script.")
        # Wait for browser close
        while any(page.is_closed() is False for page in browser.pages):
            await asyncio.sleep(2)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
