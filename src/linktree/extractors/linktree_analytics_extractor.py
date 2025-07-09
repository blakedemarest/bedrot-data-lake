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
            locator.wait_for(state=wait_state)
            locator.click(force=True)
            return
        except Exception as e:
            print(f"[WARN] Attempt {attempt + 1}/{retries} to click '{selector}' failed: {e}")
            time.sleep(1)
    raise RuntimeError(f"Failed to click '{selector}' after {retries} retries")


def _setup_browser(p):
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    load_cookies(context, "linktree")
    page = context.new_page()
    return browser, context, page


def _await_dashboard(page):
    print("[INFO] Navigating to https://linktr.ee/admin/analytics ...")
    page.goto("https://linktr.ee/admin/analytics", wait_until="domcontentloaded")
    try:
        page.wait_for_selector('nav[role="navigation"]')
        print("[INFO] Admin navigation bar detected → likely authenticated.")
    except PlaywrightTimeoutError:
        print("[ACTION REQUIRED] Please log in – waiting for analytics dashboard to load...")
        try:
            page.wait_for_selector('text=Insights')
            print("[INFO] Logged in and analytics dashboard detected.")
        except KeyboardInterrupt:
            raise RuntimeError("Interrupted while waiting for login")


def _select_last_365_days(page):
    try:
        page.wait_for_selector('input.input-datepicker-2')
        print("[INFO] Date range dropdown detected.")
    except PlaywrightTimeoutError:
        raise RuntimeError("Date range dropdown did not appear!")

    datepicker = page.locator('input.input-datepicker-2').first
    datepicker.wait_for(state="visible")
    datepicker.click(force=True)
    time.sleep(1)
    if not page.locator('label[for="last-365-days"]').first.is_visible():
        calendar_btn = datepicker.locator('xpath=preceding-sibling::*[contains(@title, "Calendar")]').first
        if calendar_btn.count() > 0:
            calendar_btn.click(force=True)
            time.sleep(1)
    page.wait_for_selector('label[for="last-365-days"]')
    print("[INFO] Selecting 'Last 365 days' timeframe...")
    _click_with_retry(page, 'label[for="last-365-days"]')
    print("[INFO] Selecting 'Daily' granularity...")
    _click_with_retry(page, 'button:has-text("Daily")')

def main():
    print("[INFO] Starting Linktree analytics extractor...")
    with sync_playwright() as p:
        browser, context, page = _setup_browser(p)

        last_save_time = time.time()
        saved_files: set[Path] = set()

        pending_responses = set()
        
        def handle_response(response):
            nonlocal last_save_time
            if "graphql" in response.url:
                response_id = id(response)
                pending_responses.add(response_id)
                try:
                    body = response.body()
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    fname = OUTPUT_DIR / f"graphql_{ts}.json"
                    with open(fname, "wb") as f:
                        f.write(body)
                    print(f"[SAVED] {fname} <- {response.url}")
                    saved_files.add(fname)
                    last_save_time = time.time()
                except Exception as e:
                    print(f"[ERROR] Could not save response from {response.url}: {e}")
                finally:
                    pending_responses.discard(response_id)

        context.on("response", handle_response)

        try:
            _await_dashboard(page)
            _select_last_365_days(page)
            print(
                "[INFO] Now capturing GraphQL network responses. The browser will close automatically after extraction."
            )
            while True:
                time.sleep(1)
                # Wait for all pending responses to complete before considering timeout
                if len(pending_responses) == 0 and time.time() - last_save_time > 10 and saved_files:
                    print(
                        "[INFO] No new GraphQL responses for 10 seconds and all pending responses complete. Closing browser..."
                    )
                    break
        except KeyboardInterrupt:
            print("[INFO] Interrupted by user. Closing browser...")
        finally:
            # Wait for any remaining pending responses
            max_wait = 30
            wait_time = 0
            while len(pending_responses) > 0 and wait_time < max_wait:
                print(f"[INFO] Waiting for {len(pending_responses)} pending responses to complete...")
                time.sleep(1)
                wait_time += 1
            
            browser.close()
            print("[INFO] Browser closed. Extraction complete.")

if __name__ == "__main__":
    main()
