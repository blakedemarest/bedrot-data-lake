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


def _wait_for_analytics_page(context, analytics_prefix: str) -> Optional["Page"]:
    tracked_pages = set(context.pages)

    def on_new_page(page):
        tracked_pages.add(page)

    context.on("page", on_new_page)
    found_page = None
    while True:
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
    page.wait_for_url(analytics_url)

    if cookies_path and marker_path:
        _import_cookies(context, cookies_path, marker_path)

    analytics_prefix = analytics_url.split("/analytics")[0] + "/analytics"
    page = _wait_for_analytics_page(context, analytics_prefix)
    if page is None:
        print("Analytics page not found. Browser remains open for manual intervention.")
        return

    time.sleep(3)
    import random

    # Try multiple strategies to click the date range button
    date_clicked = False
    
    # Strategy 1: Look for "Last 7 days" button
    for attempt in range(3):
        try:
            if page.get_by_role("button", name="Last 7 days").is_visible():
                page.get_by_role("button", name="Last 7 days").click()
                print("[INFO] Clicked 'Last 7 days' button")
                date_clicked = True
                break
        except Exception as e:
            print(f"[DEBUG] Last 7 days attempt {attempt + 1} failed: {e}")
            time.sleep(2)
    
    # Strategy 2: Look for any date range button
    if not date_clicked:
        for attempt in range(3):
            try:
                # Look for buttons containing "days" or common date patterns
                selectors = [
                    "button:has-text('7 days')",
                    "button:has-text('days')", 
                    "[role='button']:has-text('7')",
                    ".date-selector button",
                    "[data-testid*='date'] button"
                ]
                
                for selector in selectors:
                    if page.locator(selector).first.is_visible():
                        page.locator(selector).first.click()
                        print(f"[INFO] Clicked date button using selector: {selector}")
                        date_clicked = True
                        break
                
                if date_clicked:
                    break
                    
            except Exception as e:
                print(f"[DEBUG] Alternative date selector attempt {attempt + 1} failed: {e}")
                time.sleep(2)
    
    if not date_clicked:
        raise RuntimeError("Could not find or click date range selector")
    
    # Wait for dropdown and select 365 days
    time.sleep(2)
    
    # Try to find and click 365 days option
    days_365_clicked = False
    for attempt in range(3):
        try:
            if page.wait_for_selector("text=Last 365 days", timeout=5000):
                page.locator("text=Last 365 days").click()
                print("[INFO] Selected 'Last 365 days'")
                days_365_clicked = True
                break
        except Exception as e:
            print(f"[DEBUG] 365 days selection attempt {attempt + 1} failed: {e}")
            # Try alternative selectors
            try:
                alt_selectors = [
                    "text=365 days",
                    "button:has-text('365')",
                    "[role='option']:has-text('365')"
                ]
                for selector in alt_selectors:
                    if page.locator(selector).first.is_visible():
                        page.locator(selector).first.click()
                        print(f"[INFO] Selected 365 days using: {selector}")
                        days_365_clicked = True
                        break
                if days_365_clicked:
                    break
            except Exception:
                pass
            time.sleep(2)
    
    if not days_365_clicked:
        print("[WARN] Could not select 365 days, proceeding with current selection")
    
    time.sleep(random.uniform(2.0, 3.0))

    page.get_by_role("button", name="Download data").click()
    page.wait_for_selector("text=Download Overview data")
    page.locator('input[type="radio"][value="CSV"]').check()
    with page.expect_download() as download_info:
        page.locator('button:has-text("Download")').last.click()
    download = download_info.value
    save_path = output_dir / download.suggested_filename
    download.save_as(save_path)

    if not page.is_closed():
        page.close()
    context.close()
    print("Extraction complete. Browser closed automatically after data capture.")
