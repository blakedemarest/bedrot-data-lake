# Scrape analytics for the PIG1987 TikTok account and save JSON dumps to the
# landing zone. Uses account-specific cookies for authentication.

import os
import time
from common.extractors.tiktok_shared import run_extraction
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
DEFAULT_SESSION_DIR = str(Path(PROJECT_ROOT) / 'src' / '.playwright_dk_session_pig1987')
PLAYWRIGHT_SESSION_DIR = os.getenv('PLAYWRIGHT_SESSION_DIR', DEFAULT_SESSION_DIR)

LOGIN_URL = 'https://www.tiktok.com/login/phone-or-email/email'
STUDIO_URL = 'https://www.tiktok.com/tiktokstudio'
ANALYTICS_URL = 'https://www.tiktok.com/tiktokstudio/analytics'


def process_account_manual_persistent(playwright):
    """Wrapper maintaining original API while delegating to shared logic."""
    user_data_dir = PLAYWRIGHT_SESSION_DIR
    cookies_path = os.path.join(
        PROJECT_ROOT, "src", "tiktok", "cookies", "tiktok_cookies_pig1987.json"
    )
    marker_path = os.path.join(user_data_dir, ".tiktok_cookies_pig1987_imported")
    result = run_extraction(
        playwright,
        user_data_dir=user_data_dir,
        analytics_url=ANALYTICS_URL,
        output_dir=OUTPUT_DIR,
        cookies_path=cookies_path,
        marker_path=marker_path,
        capture_followers=True,
        artist_name="pig1987",
    )
    return result

def main():
    with sync_playwright() as playwright:
        process_account_manual_persistent(playwright)

if __name__ == "__main__":
    main()
