import os
import time
import json
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load environment variables
load_dotenv()
PROJECT_ROOT = os.environ.get('PROJECT_ROOT')
if not PROJECT_ROOT:
    raise EnvironmentError("PROJECT_ROOT environment variable must be set.")
OUTPUT_DIR = Path(PROJECT_ROOT) / 'landing' / 'tiktok' / 'analytics'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LOGIN_URL = 'https://www.tiktok.com/login/phone-or-email/email'
STUDIO_URL = 'https://www.tiktok.com/tiktokstudio'
ANALYTICS_URL = 'https://www.tiktok.com/tiktokstudio/analytics'


def process_account_manual_persistent(playwright):
    print("[INFO] Starting TikTok analytics extraction for PIG1987 (persistent context + real browser fingerprint)")

    # Use a unique persistent user data directory for PIG1987
    user_data_dir = r"c:/Users/Earth/BEDROT PRODUCTIONS/BEDROT DATA LAKE/data_lake/src/.playwright_dk_session_pig1987"
    os.makedirs(user_data_dir, exist_ok=True)
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    # Launch browser with persistent context
    context = playwright.chromium.launch_persistent_context(
        user_data_dir,
        headless=False,
        viewport={"width": 1440, "height": 900},
        user_agent=user_agent,
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = context.pages[0] if context.pages else context.new_page()

    # Automatically navigate the tab to TikTok analytics
    analytics_url = ANALYTICS_URL
    page.goto(analytics_url)
    page.wait_for_url(analytics_url, timeout=120000)  # Wait up to 2 minutes for page to load

    # One-time cookie import if tiktok_cookies_pig1987.json exists
    cookies_path = os.path.join(PROJECT_ROOT, 'src', 'tiktok', 'cookies', 'tiktok_cookies_pig1987.json')
    marker_path = os.path.join(user_data_dir, '.tiktok_cookies_pig1987_imported')
    if os.path.exists(cookies_path) and not os.path.exists(marker_path):
        print("[INFO] Importing cookies from tiktok_cookies_pig1987.json (one-time operation)...")
        with open(cookies_path, 'r') as f:
            cookies = json.load(f)
        VALID_SAMESITE = {"Strict", "Lax", "None"}
        for cookie in cookies:
            if "sameSite" in cookie and cookie["sameSite"] not in VALID_SAMESITE:
                cookie["sameSite"] = "Lax"
        context.add_cookies(cookies)
        print("[INFO] Cookies imported. Please refresh or re-navigate to TikTok if needed.")
        with open(marker_path, 'w') as marker:
            marker.write('imported')

    analytics_prefix = "https://www.tiktok.com/tiktokstudio/analytics"
    print(f"[ACTION] Waiting for you to navigate to any analytics page starting with: {analytics_prefix}")
    max_wait_seconds = 300
    waited = 0
    found_page = None
    tracked_pages = set(context.pages)
    def on_new_page(page):
        print(f"[DEBUG] New tab opened: {page.url}")
        tracked_pages.add(page)
    context.on("page", on_new_page)
    try:
        while waited < max_wait_seconds:
            tracked_pages = {p for p in tracked_pages if not p.is_closed()}
            if len(tracked_pages) == 0:
                print("[INFO] All browser tabs are closed. Exiting script.")
                return
            found = False
            for p in tracked_pages:
                print(f"[DEBUG] Tracked tab url: {p.url}")
                if p.url.startswith(analytics_prefix):
                    found = True
                    found_page = p
                    break
            if found:
                print("[INFO] Detected TikTok analytics page in one of the tracked tabs. Proceeding...")
                break
            time.sleep(1)
            waited += 1
        else:
            print(f"[ERROR] Waited {max_wait_seconds} seconds but never saw analytics page in any tracked tab.")
        if not found_page:
            for p in tracked_pages:
                try:
                    p.wait_for_url(f"{analytics_prefix}*", timeout=300000)
                    print("[INFO] Detected TikTok analytics page via wait_for_url in tracked tab. Proceeding...")
                    found_page = p
                    break
                except Exception as e:
                    print(f"[ERROR] wait_for_url did not trigger in tracked tab: {e}")
        if not found_page:
            print("[FATAL] Could not find analytics page in any tracked tab. Aborting.")
            return
        page = found_page
        time.sleep(2)

        import random
        print("[INFO] Changing date range to 'Last 365 days'...")
        time.sleep(random.uniform(1.5, 3.0))
        page.get_by_role('button', name='Last 7 days').click()
        page.wait_for_selector("text=Last 365 days", timeout=10000)
        page.locator("text=Last 365 days").click()
        time.sleep(random.uniform(1.0, 2.0))

        print("[INFO] Downloading analytics data as CSV...")
        page.get_by_role('button', name='Download data').click()
        page.wait_for_selector('text=Download Overview data', timeout=10000)
        page.locator('input[type="radio"][value="CSV"]').check()
        with page.expect_download() as download_info:
            page.locator('button:has-text("Download")').last.click()
        download = download_info.value
        save_path = OUTPUT_DIR / download.suggested_filename
        download.save_as(save_path)
        print(f"[SAVED] {save_path}")
        if not page.is_closed():
            page.close()
    finally:
        try:
            context.close()
        except Exception:
            pass

def main():
    with sync_playwright() as playwright:
        process_account_manual_persistent(playwright)

if __name__ == "__main__":
    main()
