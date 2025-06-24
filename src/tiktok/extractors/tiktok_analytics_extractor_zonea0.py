# Scrape analytics for the ZONEA0 TikTok account and save JSON dumps to the
# landing zone. Requires PROJECT_ROOT and account cookies.

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

from common.extractors.tiktok_shared import run_extraction


def process_account_manual_persistent(playwright):
    """Wrapper maintaining original API while delegating to shared logic."""
    user_data_dir = PLAYWRIGHT_SESSION_DIR
    cookies_path = os.path.join(
        PROJECT_ROOT, "src", "tiktok", "cookies", "tiktok_cookies_zonea0.json"
    )
    marker_path = os.path.join(user_data_dir, ".tiktok_cookies_zonea0_imported")
    result = run_extraction(
        playwright,
        user_data_dir=user_data_dir,
        analytics_url=ANALYTICS_URL,
        output_dir=OUTPUT_DIR,
        cookies_path=cookies_path,
        marker_path=marker_path,
        capture_followers=True,
        artist_name="zone.a0",
    )
    return result


# Only run the manual approach for now (for manual login/testing)
def main():
    with sync_playwright() as playwright:
        process_account_manual_persistent(playwright)

if __name__ == "__main__":
    main()
