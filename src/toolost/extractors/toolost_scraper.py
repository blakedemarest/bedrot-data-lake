# Automate TooLost login and download analytics and sales reports to the raw zone.
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
DEFAULT_SESSION_DIR = str(Path(PROJECT_ROOT) / "src" / ".playwright_dk_session")
SESSION_DIR = os.getenv("PLAYWRIGHT_SESSION_DIR", DEFAULT_SESSION_DIR)
OUTPUT_DIR = Path(PROJECT_ROOT) / "raw" / "toolost"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TOOLOST_URL = "https://toolost.com/user-portal/analytics/platform"
SPOTIFY_API = "https://toolost.com/api/portal/analytics/spotify?release=&date=thisYear"
APPLE_API = "https://toolost.com/api/portal/analytics/apple/?release=&date=thisYear"


async def _launch_browser(p):
    browser = await p.chromium.launch_persistent_context(
        SESSION_DIR,
        headless=False,
        viewport={"width": 1280, "height": 900},
    )
    await load_cookies_async(browser, "toolost")
    page = await browser.new_page()
    await page.goto("https://toolost.com/login")
    return browser, page


async def _wait_for_login(page):
    print("[TOOLOST] Please log in and complete any 2FA...")
    while True:
        try:
            await page.wait_for_selector(
                "nav, aside, .ant-layout-sider, .dashboard, [data-testid*=user-menu]",
                timeout=2000,
            )
            break
        except Exception:
            await asyncio.sleep(2)
    print("[TOOLOST] Authenticated dashboard detected!")


async def _goto_analytics(page):
    await page.goto(TOOLOST_URL)
    try:
        await page.wait_for_selector("main, .ant-layout-content, .analytics, .dashboard", timeout=10000)
    except Exception:
        await asyncio.sleep(3)


def _setup_response_capture(page):
    api_results = {"spotify": None, "apple": None}
    responses = {"spotify": None, "apple": None}
    now = datetime.now().strftime("%Y%m%d_%H%M%S")

    def handle_response(response):
        if response.url.startswith(SPOTIFY_API):
            api_results["spotify"] = asyncio.create_task(response.json())
        elif response.url.startswith(APPLE_API):
            api_results["apple"] = asyncio.create_task(response.json())

    page.on("response", handle_response)
    return api_results, responses, now


async def _save_if_available(key, api_results, responses, path: Path):
    if api_results[key]:
        responses[key] = await api_results[key]
        path.write_text(json.dumps(responses[key], indent=2))
        print(f"Saved {key} analytics to {path}")
    else:
        print(f"{key.capitalize()} API response not captured.")


async def _select_this_year(page):
    try:
        await page.wait_for_selector("[class*=ant-picker], [data-testid*=date], [role=button]", timeout=15000, state="visible")
        await page.click("[class*=ant-picker], [data-testid*=date], [role=button]", timeout=5000)
        await asyncio.sleep(1)
        try:
            await page.click("text=This Year", timeout=3000)
        except Exception:
            await page.click("text=Year", timeout=3000)
        await asyncio.sleep(2)
    except Exception:
        print("[TOOLOST] Date picker not found.")


async def _switch_to_apple(page):
    try:
        await page.click("[role=button]:has-text('Spotify'), [data-testid*=platform], .ant-select-selector")
        await page.wait_for_selector("div.d-flex.align-center.flex-row", timeout=5000)
        for option in await page.query_selector_all("div.d-flex.align-center.flex-row"):
            if (await option.inner_text()).strip() == "Apple":
                await option.click()
                break
    except Exception as e:
        print(f"Failed to click Apple platform option: {e}")
    await asyncio.sleep(2)


async def _download_sales_report(page):
    await page.goto("https://toolost.com/user-portal/notifications")
    await asyncio.sleep(2)
    blocks = page.locator("div.body-1.font-weight-bold.mb-1")
    texts = await blocks.all_inner_texts()
    import re
    for idx, text in enumerate(texts):
        if re.search(r"Your \\(\d{2}-\d{4}\\) Sales report has been generated", text):
            buttons = page.locator("button:has-text('Attachment')")
            if await buttons.count() > idx:
                async with page.expect_download() as info:
                    await buttons.nth(idx).click()
                download = await info.value
                filename = await download.suggested_filename()
                dest = Path(PROJECT_ROOT) / "landing" / "toolost" / "streams"
                dest.mkdir(parents=True, exist_ok=True)
                await download.save_as(str(dest / filename))
                print(f"[TOOLOST] Downloaded: {filename}")
            break


async def main():
    async with async_playwright() as p:
        browser, page = await _launch_browser(p)
        await _wait_for_login(page)
        await _goto_analytics(page)
        api_results, responses, now = _setup_response_capture(page)
        await _select_this_year(page)

        print("Waiting for Spotify API call...")
        for _ in range(30):
            if api_results["spotify"]:
                break
            await asyncio.sleep(1)
        await _save_if_available("spotify", api_results, responses, OUTPUT_DIR / f"toolost_spotify_{now}.json")

        await _switch_to_apple(page)
        print("Waiting for Apple Music API call...")
        for _ in range(60):
            if api_results["apple"]:
                break
            await asyncio.sleep(1)
        await _save_if_available("apple", api_results, responses, OUTPUT_DIR / f"toolost_apple_{now}.json")

        await _download_sales_report(page)
        print("Data collection complete. You may now close the browser window.")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
