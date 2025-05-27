import os
import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler()]
)

SESSION_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.playwright_dk_session'))
LOGIN_URL = "https://distrokid.com/login"
DASHBOARD_URL = "https://distrokid.com/stats/?data=streams"

# Get credentials from environment variables
DK_EMAIL = os.getenv("DK_EMAIL")
DK_PASSWORD = os.getenv("DK_PASSWORD")


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
            browser = p.chromium.launch_persistent_context(
                SESSION_DIR,
                headless=False
            )
            page = browser.new_page()
            page.goto(LOGIN_URL)
            logging.info(f"Navigated to {LOGIN_URL}")

            # Check if already logged in (no login form present)
            try:
                page.wait_for_selector('input[type="email"]', timeout=5000)
                # Login form is present, fill credentials
                logging.info("Login form detected, filling credentials.")
                page.fill('input[type="email"]', DK_EMAIL)
                page.fill('input[type="password"]', DK_PASSWORD)
                page.click('button[type="submit"]')
                logging.info("Submitted login form. If 2FA is required, please complete it in the browser.")
            except PlaywrightTimeoutError:
                # Login form not present, assume already logged in
                logging.info("Login form not detected. Assuming already authenticated.")

            print("Please complete the DistroKid login and 2FA in the browser window.")
            print("Once you are on your dashboard, the script will automatically download stats pages.")
            import time
            dashboard_detected = False
            while not dashboard_detected:
                current_url = page.url
                # Adjust this check if dashboard URL changes
                if any(x in current_url for x in ["/dashboard", "/mymusic", "/stats"]):
                    logging.info(f"Dashboard detected at {current_url}. Proceeding to download stats.")
                    dashboard_detected = True
                else:
                    time.sleep(2)
            # At this point, we're on the dashboard. Proceed to download stats.
            from datetime import datetime
            output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../landing/distrokid/streams'))
            os.makedirs(output_dir, exist_ok=True)
            # Download streams stats
            stats_url = "https://distrokid.com/stats/?type=all&data=streams"
            logging.info(f"Navigating to streams stats page: {stats_url}")
            page.goto(stats_url)
            page.wait_for_selector('body', timeout=30000)
            html = page.content()
            dt_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            streams_file = os.path.join(output_dir, f'streams_stats_{dt_str}.html')
            with open(streams_file, 'w', encoding='utf-8') as f:
                f.write(html)
            logging.info(f"Streams stats page HTML saved to {streams_file}")
            # Download Apple Music stats
            am_url = "https://distrokid.com/stats/?type=all&data=applemusic"
            logging.info(f"Navigating to Apple Music stats page: {am_url}")
            page.goto(am_url)
            page.wait_for_selector('body', timeout=30000)
            am_html = page.content()
            am_file = os.path.join(output_dir, f'applemusic_stats_{dt_str}.html')
            with open(am_file, 'w', encoding='utf-8') as f:
                f.write(am_html)
            logging.info(f"Apple Music stats page HTML saved to {am_file}")
            # ---- Begin Bank TSV Download Enhancement ----
            print("Stats pages downloaded. Proceeding to download DistroKid bank TSV...")
            try:
                # Step 1: Go to bank page
                page.goto("https://distrokid.com/bank/")
                page.wait_for_selector('a[href="/bank/details/"]', timeout=10000)
                # Step 2: Click 'See Excruciating Detail' button
                page.click('a[href="/bank/details/"]')
                page.wait_for_url("https://distrokid.com/bank/details/")
                # Step 3: Wait for download button and download TSV
                from playwright.sync_api import TimeoutError
                page.wait_for_selector('div[onclick^="downloadBank"]', timeout=10000)
                import time as _time
                tsv_file = os.path.join(output_dir, f'dk_bank_details_{dt_str}.tsv')
                with page.expect_download() as download_info:
                    page.click('div[onclick^="downloadBank"]')
                download = download_info.value
                download.save_as(tsv_file)
                logging.info(f"DistroKid bank TSV downloaded to {tsv_file}")
            except Exception as bank_exc:
                logging.error(f"Failed to download DistroKid bank TSV: {bank_exc}")
            # ---- End Bank TSV Download Enhancement ----
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
