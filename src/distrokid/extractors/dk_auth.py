# Automates DistroKid login and downloads stats pages to the landing zone.
# Uses Playwright with credentials from environment variables.

import os
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv
from common.cookies import load_cookies  # <-- unified cookie/session utility

# Load environment variables from .env if present
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler()]
)

# Persistent session directory for Playwright
PROJECT_ROOT = os.getenv("PROJECT_ROOT", str(Path(__file__).resolve().parents[3]))
DEFAULT_SESSION_DIR = str(Path(PROJECT_ROOT) / "src" / ".playwright_dk_session")
SESSION_DIR = os.getenv("PLAYWRIGHT_SESSION_DIR", DEFAULT_SESSION_DIR)
LOGIN_URL = "https://distrokid.com/login"
DASHBOARD_URL = "https://distrokid.com/stats/?data=streams"

# Get credentials from environment variables
DK_EMAIL = os.getenv("DK_EMAIL")
DK_PASSWORD = os.getenv("DK_PASSWORD")


def _launch_context(p):
    browser = p.chromium.launch_persistent_context(SESSION_DIR, headless=False)
    load_cookies(browser, "distrokid")
    page = browser.new_page()
    return browser, page


def _perform_login(page):
    try:
        page.wait_for_selector('input[type="email"]', timeout=5000)
        logging.info("Login form detected, filling credentials.")
        page.fill('input[type="email"]', DK_EMAIL)
        page.fill('input[type="password"]', DK_PASSWORD)
        page.click('button[type="submit"]')
        logging.info("Submitted login form. If 2FA is required, please complete it in the browser.")
    except PlaywrightTimeoutError:
        logging.info("Login form not detected. Assuming already authenticated.")


def _wait_for_dashboard(page):
    print("Please complete the DistroKid login and 2FA in the browser window.")
    print("Once you are on your dashboard, the script will automatically download stats pages.")
    import time
    while True:
        if any(x in page.url for x in ["/dashboard", "/mymusic", "/stats"]):
            logging.info(f"Dashboard detected at {page.url}. Proceeding to download stats.")
            break
        time.sleep(2)


def _download_stats(page, output_dir: str, dt_str: str):
    stats_url = "https://distrokid.com/stats/?type=all&data=streams"
    logging.info(f"Navigating to streams stats page: {stats_url}")
    page.goto(stats_url)
    page.wait_for_selector('body', timeout=30000)
    html = page.content()
    streams_file = os.path.join(output_dir, f'streams_stats_{dt_str}.html')
    with open(streams_file, 'w', encoding='utf-8') as f:
        f.write(html)
    logging.info(f"Streams stats page HTML saved to {streams_file}")

    am_url = "https://distrokid.com/stats/?type=all&data=applemusic"
    logging.info(f"Navigating to Apple Music stats page: {am_url}")
    page.goto(am_url)
    page.wait_for_selector('body', timeout=30000)
    am_html = page.content()
    am_file = os.path.join(output_dir, f'applemusic_stats_{dt_str}.html')
    with open(am_file, 'w', encoding='utf-8') as f:
        f.write(am_html)
    logging.info(f"Apple Music stats page HTML saved to {am_file}")

    try:
        page.goto("https://distrokid.com/bank/")
        page.wait_for_selector('a[href="/bank/details/"]', timeout=10000)
        page.click('a[href="/bank/details/"]')
        page.wait_for_url("https://distrokid.com/bank/details/")
        page.wait_for_selector('div[onclick^="downloadBank"]', timeout=10000)
        tsv_file = os.path.join(output_dir, f'dk_bank_details_{dt_str}.tsv')
        with page.expect_download() as download_info:
            page.click('div[onclick^="downloadBank"]')
        download = download_info.value
        download.save_as(tsv_file)
        logging.info(f"DistroKid bank TSV downloaded to {tsv_file}")
    except Exception as exc:
        logging.error(f"Failed to download DistroKid bank TSV: {exc}")


def login_distrokid():
    """
    Automates login to DistroKid, including 2FA, and persists session for future use.
    Credentials are read from environment variables DK_EMAIL and DK_PASSWORD.
    If 2FA is required, user will be prompted to enter the code manually in the browser.
    """
    if not DK_EMAIL or not DK_PASSWORD:
        logging.error("DK_EMAIL and DK_PASSWORD must be set in environment variables or .env file.")
        return False

    with sync_playwright() as p:
        try:
            browser, page = _launch_context(p)
            page.goto(LOGIN_URL)
            logging.info(f"Navigated to {LOGIN_URL}")

            _perform_login(page)
            _wait_for_dashboard(page)

            from datetime import datetime
            output_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../../landing/distrokid/streams")
            )
            os.makedirs(output_dir, exist_ok=True)
            dt_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            _download_stats(page, output_dir, dt_str)

            print("All downloads complete. You may now close the browser window.")
            browser.close()
            logging.info("Browser closed automatically after all downloads. Workflow complete.")
            return True
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            return False

def test_login_distrokid():
    """
    Test to verify if the login session is valid and can access the stats page without manual intervention.
    """
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch_persistent_context(
                SESSION_DIR,
                headless=True
            )
            # Inject cookies to validate session without login
            load_cookies(browser, "distrokid")
            page = browser.new_page()
            page.goto(DASHBOARD_URL)
            page.wait_for_selector('body', timeout=10000)
            if "login" in page.url:
                logging.warning("Session is not valid, redirected to login page.")
                result = False
            else:
                logging.info(f"Successfully accessed stats page: {page.url}")
                result = True
            browser.close()
            return result
        except Exception as e:
            logging.exception(f"Test failed: {e}")
            return False

if __name__ == "__main__":
    # Run the login workflow
    if login_distrokid():
        logging.info("Login workflow completed successfully.")
        # Optionally, run the test
        if test_login_distrokid():
            logging.info("Session test passed. Ready for data extraction.")
        else:
            logging.warning("Session test failed. Please re-run login if needed.")
    else:
        logging.error("Login workflow failed. Please check credentials and try again.")
