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
                # Prompt user to complete login and 2FA
                print("Please complete the DistroKid login and 2FA in the browser window.")
                print("When you see your dashboard or stats page, return here and press Enter to continue.")
                while True:
                    input("Press Enter when you believe you are logged in and ready...")
                    current_url = page.url
                    print(f"Current browser URL: {current_url}")
                    if "distrokid.com/stats" in current_url or "dashboard" in current_url or "mymusic" in current_url:
                        logging.info("Login successful. Session saved for future use.")
                        break
                    else:
                        print("Login may not have succeeded. You are not on the expected page.")
                        retry = input("Would you like to try again? (y/n): ").strip().lower()
                        if retry != 'y':
                            print("Leaving the browser open. Please close it manually if you are done.")
                            return False
            except PlaywrightTimeoutError:
                # Login form not present, assume already logged in
                logging.info("Login form not detected. Assuming already authenticated.")

            # After login/auth, navigate to stats page and save HTML
            stats_url = "https://distrokid.com/stats/?data=streams"
            logging.info(f"Navigating to stats page: {stats_url}")
            page.goto(stats_url)
            page.wait_for_selector('body', timeout=30000)
            html = page.content()
            output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../landing/distrokid/streams'))
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, 'streams_stats.html')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)
            logging.info(f"Stats page HTML saved to {output_file}")
            browser.close()
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
