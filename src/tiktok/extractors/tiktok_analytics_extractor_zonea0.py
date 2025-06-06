import os
import time
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
DEFAULT_SESSION_DIR = str(Path(PROJECT_ROOT) / 'src' / '.playwright_dk_session')
PLAYWRIGHT_SESSION_DIR = os.getenv('PLAYWRIGHT_SESSION_DIR', DEFAULT_SESSION_DIR)

ACCOUNTS = [
    (os.environ.get('ZONE_A0_TIKTOK_EMAIL'), os.environ.get('ZONE_A0_TIKTOK_PASSWORD')),
    (os.environ.get('PIG1987_TIKTOK_EMAIL'), os.environ.get('PIG1987_TIKTOK_PASSWORD')),
]

LOGIN_URL = 'https://www.tiktok.com/login/phone-or-email/email'
STUDIO_URL = 'https://www.tiktok.com/tiktokstudio'
ANALYTICS_URL = 'https://www.tiktok.com/tiktokstudio/analytics'


# def process_account(email, password, playwright):
#     print(f"[INFO] Starting TikTok analytics extraction for: {email}")
#     # Launch browser in incognito/private mode
#     browser = playwright.chromium.launch(headless=False)
#     context = browser.new_context(accept_downloads=True)
#     page = context.new_page()
#
#     # Clear TikTok cookies and cache before login
#     print("[ACTION] Clearing TikTok cookies and cache...")
#     context.clear_cookies()
#     page.goto("https://www.tiktok.com")
#     page.context.clear_cookies()
#     page.context.clear_permissions()
#     page.evaluate("caches.keys().then(keys => { keys.forEach(key => caches.delete(key)); });")
#     page.goto(LOGIN_URL)
#
#     # Robust login autofill
#     print("[ACTION] Waiting for login fields to appear...")
#     page.wait_for_selector('input[type="text"], input[placeholder*="email"], input[name*="email"]', timeout=15000)
#     page.fill('input[type="text"], input[placeholder*="email"], input[name*="email"]', email)
#     page.wait_for_selector('input[type="password"]', timeout=10000)
#     page.fill('input[type="password"]', password)
#     print("[ACTION] Autofilled credentials. Please manually press the login button in the browser to continue.")
#     # Do NOT click or submit the login button automatically. Wait for user action.
#
#     # Wait for 2FA or login complete
#     print("[ACTION] Complete 2FA if prompted. Waiting for TikTok Studio dashboard...")
#     page.wait_for_url(lambda url: url.startswith(STUDIO_URL), timeout=0)
#     print("[INFO] Logged in successfully.")
#
#     # Go to analytics page
#     page.goto(ANALYTICS_URL)
#     page.wait_for_load_state('networkidle')
#     time.sleep(3)
#
#     # Change date range to 'Last 365 days'
#     print("[INFO] Changing date range to 'Last 365 days'...")
#     page.get_by_role('button', name='Last 7 days').click()
#     page.get_by_role('option', name='Last 365 days').click()
#     time.sleep(2)
#
#     # Download data
#     print("[INFO] Downloading analytics data as CSV...")
#     page.get_by_role('button', name='Download data').click()
#     page.get_by_role('radio', name='CSV').check()
#     with page.expect_download() as download_info:
#         page.get_by_role('button', name='Download').click()
#     download = download_info.value
#     save_path = OUTPUT_DIR / download.suggested_filename
#     download.save_as(save_path)
#     print(f"[SAVED] {save_path}")
#
#     context.close()
#     browser.close()

import json

def process_account_manual_persistent(playwright):
    print("[INFO] Starting TikTok analytics extraction (persistent context + real browser fingerprint)")

    # Use unified persistent user data directory for all Playwright scripts (shared browser profile)
    user_data_dir = PLAYWRIGHT_SESSION_DIR
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
    analytics_url = "https://www.tiktok.com/tiktokstudio/analytics"
    page.goto(analytics_url)
    page.wait_for_url(analytics_url, timeout=120000)  # Wait up to 2 minutes for page to load

    # One-time cookie import if tiktok_cookies.json exists
    cookies_path = os.path.join(PROJECT_ROOT, 'tiktok_cookies.json')
    # Only import cookies if the marker file does NOT exist
    marker_path = os.path.join(user_data_dir, '.tiktok_cookies_imported')
    if os.path.exists(cookies_path) and not os.path.exists(marker_path):
        print("[INFO] Importing cookies from tiktok_cookies.json (one-time operation)...")
        with open(cookies_path, 'r') as f:
            cookies = json.load(f)
        # Normalize invalid sameSite values to 'Lax'
        VALID_SAMESITE = {"Strict", "Lax", "None"}
        for cookie in cookies:
            if "sameSite" in cookie and cookie["sameSite"] not in VALID_SAMESITE:
                cookie["sameSite"] = "Lax"
        context.add_cookies(cookies)
        print("[INFO] Cookies imported. Please refresh or re-navigate to TikTok if needed.")
        # Create a marker file so we only import cookies once
        with open(marker_path, 'w') as marker:
            marker.write('imported')
        # Optionally, remove the cookie file after import
        # os.remove(cookies_path)
    elif os.path.exists(marker_path):
        print("[INFO] Cookie import already completed previously. Skipping cookie import.")

    print("[ACTION] Please log in manually in the browser window if not already logged in.")
    print("[ACTION] After login, navigate to the analytics overview page:")
    print("         https://www.tiktok.com/tiktokstudio/analytics/overview?from=dropdown_button&lang=en")
    print("[ACTION] The script will wait until you reach the correct analytics page, then continue.")

    # Wait until user lands anywhere in the analytics zone (any tab)
    analytics_prefix = "https://www.tiktok.com/tiktokstudio/analytics"
    print(f"[ACTION] Waiting for you to navigate to any analytics page starting with: {analytics_prefix}")
    import time
    max_wait_seconds = 300
    waited = 0
    found_page = None
    # Track all open tabs, including new ones
    tracked_pages = set(context.pages)
    def on_new_page(page):
        print(f"[DEBUG] New tab opened: {page.url}")
        tracked_pages.add(page)
    context.on("page", on_new_page)
    try:
        while waited < max_wait_seconds:
            # Remove closed tabs from the tracked set
            tracked_pages = {p for p in tracked_pages if not p.is_closed()}
            # If all tabs are closed, exit gracefully
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
        # Also use Playwright's wait_for_url with wildcard for robustness (on all tracked tabs)
        if not found_page:
            for p in tracked_pages:
                try:
                    p.wait_for_url(f"{analytics_prefix}*", timeout=300000)  # 5 minutes
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

        # Change date range to 'Last 365 days' (add random delay for human-like behavior)
        import random
        print("[INFO] Changing date range to 'Last 365 days'...")
        time.sleep(random.uniform(1.5, 3.0))
        page.get_by_role('button', name='Last 7 days').click()
        # Wait for the dropdown to appear
        page.wait_for_selector("text=Last 365 days", timeout=10000)
        page.locator("text=Last 365 days").click()
        time.sleep(random.uniform(1.0, 2.0))

        # Download data
        print("[INFO] Downloading analytics data as CSV...")
        page.get_by_role('button', name='Download data').click()
        # Wait for the download modal to appear
        page.wait_for_selector('text=Download Overview data', timeout=10000)
        # Select CSV radio
        page.locator('input[type="radio"][value="CSV"]').check()
        # Click the correct Download button inside the modal (the last visible one)
        with page.expect_download() as download_info:
            page.locator('button:has-text("Download")').last.click()
        download = download_info.value
        save_path = OUTPUT_DIR / download.suggested_filename
        download.save_as(save_path)
        print(f"[SAVED] {save_path}")
        # Close the analytics tab if it's still open
        if not page.is_closed():
            page.close()
    finally:
        # Always close the context at the end
        try:
            context.close()
        except Exception:
            pass


# Only run the manual approach for now (for manual login/testing)
def main():
    with sync_playwright() as playwright:
        process_account_manual_persistent(playwright)

if __name__ == "__main__":
    main()
