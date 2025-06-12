# Captures Linktree analytics via Playwright and writes JSON responses to the
# landing zone. Requires manual login on first run.

import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Patch sys.path so 'from common.cookies' works for direct execution
PROJECT_ROOT = os.environ.get('PROJECT_ROOT')
if not PROJECT_ROOT:
    raise EnvironmentError("PROJECT_ROOT environment variable must be set.")
SRC_PATH = str(Path(PROJECT_ROOT) / 'src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from common.cookies import load_cookies  # unified cookie/session helper

# Output directory
PROJECT_ROOT = os.environ.get('PROJECT_ROOT')
if not PROJECT_ROOT:
    raise EnvironmentError("PROJECT_ROOT environment variable must be set.")
OUTPUT_DIR = Path(PROJECT_ROOT) / 'landing' / 'linktree' / 'analytics'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def _click_with_retry(page, selector: str, retries: int = 3, wait_state="visible"):
    """/// Attempt to click the FIRST matching element with retries and wait
    /// for it to be ready."""
    for attempt in range(retries):
        try:
            locator = page.locator(selector).first
            locator.wait_for(state=wait_state, timeout=5000)
            locator.click(force=True)
            return
        except Exception as e:
            print(f"[WARN] Attempt {attempt + 1}/{retries} to click '{selector}' failed: {e}")
            time.sleep(1)
    raise RuntimeError(f"Failed to click '{selector}' after {retries} retries")

def main():
    print("[INFO] Starting Linktree analytics extractor...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        # Inject saved cookies for Linktree (one-time per session dir)
        load_cookies(context, "linktree")
        page = context.new_page()

        # --- GraphQL response capture setup (register early) ---
        last_save_time = time.time()
        saved_files: set[Path] = set()

        def handle_response(response):
            nonlocal last_save_time  # ensure we can rebind
            url = response.url
            if "graphql" in url:
                try:
                    body = response.body()
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                    fname = OUTPUT_DIR / f"graphql_{ts}.json"
                    with open(fname, 'wb') as f:
                        f.write(body)
                    print(f"[SAVED] {fname} <- {url}")
                    saved_files.add(fname)
                    last_save_time = time.time()
                except Exception as e:
                    print(f"[ERROR] Could not save response from {url}: {e}")

        context.on("response", handle_response)

        print("[INFO] Navigating to https://linktr.ee/admin/analytics ...")
        page.goto('https://linktr.ee/admin/analytics', wait_until="domcontentloaded")

        # Wait until either we are redirected to admin root (need login) or analytics fully loads
        try:
            page.wait_for_selector('nav[role="navigation"]', timeout=15000)  # nav bar on admin/analytics
            print("[INFO] Admin navigation bar detected → likely authenticated.")
        except PlaywrightTimeoutError:
            # Not logged in – wait for user to complete login
            print("[ACTION REQUIRED] Please log in – waiting for analytics dashboard to load...")
            try:
                # Wait indefinitely for the analytics dashboard header to appear
                page.wait_for_selector('text=Insights', timeout=0)
                print("[INFO] Logged in and analytics dashboard detected.")
            except KeyboardInterrupt:
                print("[ERROR] Interrupted while waiting for login.")
                browser.close()
                return
            # No need to re-navigate; already on /admin/analytics

        # Ensure analytics page fully loaded by waiting for date range dropdown
        try:
            page.wait_for_selector('input.input-datepicker-2', timeout=15000)
            print("[INFO] Date range dropdown detected.")
        except PlaywrightTimeoutError:
            print("[ERROR] Date range dropdown did not appear! Exiting.")
            browser.close()
            return

        # Open the date range dropdown (always pick the first one)
        datepicker = page.locator('input.input-datepicker-2').first
        datepicker.wait_for(state="visible", timeout=5000)
        print("[DEBUG] Clicking datepicker input to open dropdown…")
        datepicker.click(force=True)
        time.sleep(1)  # give dropdown time to render

        # Fallback: if radio panel not yet present, click calendar icon to open menu
        if not page.locator('label[for="last-365-days"]').first.is_visible(timeout=1000):
            print("[WARN] Radio options not visible after initial click; trying calendar icon…")
            calendar_btn = datepicker.locator('xpath=preceding-sibling::*[contains(@title, "Calendar")]').first
            if calendar_btn.count() > 0:
                calendar_btn.click(force=True)
                time.sleep(1)

        # Wait for the radio options panel, then choose Last 365 days
        try:
            page.wait_for_selector('label[for="last-365-days"]', timeout=5000)
        except PlaywrightTimeoutError:
            print("[ERROR] Last 365 days option not found in dropdown – layout changed?")
            browser.close()
            return

        print("[INFO] Selecting 'Last 365 days' timeframe...")
        _click_with_retry(page, 'label[for="last-365-days"]')

        # Click 'Daily' granularity
        print("[INFO] Selecting 'Daily' granularity...")
        _click_with_retry(page, 'button:has-text("Daily")')
        print("[INFO] Now capturing GraphQL network responses. The browser will close automatically after extraction.")

        # Wait for responses, then auto-close after 10s of inactivity
        try:
            while True:
                time.sleep(1)
                if time.time() - last_save_time > 10 and saved_files:
                    print("[INFO] No new GraphQL responses for 10 seconds. Closing browser...")
                    break
        except KeyboardInterrupt:
            print("[INFO] Interrupted by user. Closing browser...")
        finally:
            browser.close()
            print("[INFO] Browser closed. Extraction complete.")

if __name__ == "__main__":
    main()
