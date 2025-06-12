import json
import os
import time
from pathlib import Path
from typing import Optional

from playwright.sync_api import Playwright


VALID_SAMESITE = {"Strict", "Lax", "None"}


def _import_cookies(context, cookies_path: str, marker_path: str) -> None:
    """Import cookies once per user data directory."""
    if not os.path.exists(cookies_path) or os.path.exists(marker_path):
        return
    with open(cookies_path, "r") as f:
        cookies = json.load(f)
    for cookie in cookies:
        if "sameSite" in cookie and cookie["sameSite"] not in VALID_SAMESITE:
            cookie["sameSite"] = "Lax"
    context.add_cookies(cookies)
    with open(marker_path, "w") as marker:
        marker.write("imported")


def _wait_for_analytics_page(context, analytics_prefix: str, timeout: int = 300) -> Optional["Page"]:
    tracked_pages = set(context.pages)

    def on_new_page(page):
        tracked_pages.add(page)

    context.on("page", on_new_page)
    waited = 0
    found_page = None
    while waited < timeout:
        tracked_pages = {p for p in tracked_pages if not p.is_closed()}
        if not tracked_pages:
            return None
        for p in tracked_pages:
            if p.url.startswith(analytics_prefix):
                found_page = p
                break
        if found_page:
            break
        time.sleep(1)
        waited += 1
    if not found_page:
        for p in tracked_pages:
            try:
                p.wait_for_url(f"{analytics_prefix}*", timeout=timeout * 1000)
                found_page = p
                break
            except Exception:
                pass
    return found_page


def run_extraction(
    playwright: Playwright,
    user_data_dir: str,
    analytics_url: str,
    output_dir: Path,
    cookies_path: Optional[str] = None,
    marker_path: Optional[str] = None,
) -> None:
    """Run the shared TikTok analytics extraction routine."""
    os.makedirs(user_data_dir, exist_ok=True)
    context = playwright.chromium.launch_persistent_context(
        user_data_dir,
        headless=False,
        viewport={"width": 1440, "height": 900},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        args=["--disable-blink-features=AutomationControlled"],
    )

    page = context.pages[0] if context.pages else context.new_page()
    page.goto(analytics_url)
    page.wait_for_url(analytics_url, timeout=120000)

    if cookies_path and marker_path:
        _import_cookies(context, cookies_path, marker_path)

    analytics_prefix = analytics_url.split("/analytics")[0] + "/analytics"
    page = _wait_for_analytics_page(context, analytics_prefix)
    if page is None:
        context.close()
        return

    time.sleep(2)
    import random

    page.get_by_role("button", name="Last 7 days").click()
    page.wait_for_selector("text=Last 365 days", timeout=10000)
    page.locator("text=Last 365 days").click()
    time.sleep(random.uniform(1.0, 2.0))

    page.get_by_role("button", name="Download data").click()
    page.wait_for_selector("text=Download Overview data", timeout=10000)
    page.locator('input[type="radio"][value="CSV"]').check()
    with page.expect_download() as download_info:
        page.locator('button:has-text("Download")').last.click()
    download = download_info.value
    save_path = output_dir / download.suggested_filename
    download.save_as(save_path)

    if not page.is_closed():
        page.close()
    context.close()
