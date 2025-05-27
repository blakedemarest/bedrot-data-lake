import os
import time
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

# Output directory
PROJECT_ROOT = os.environ.get('PROJECT_ROOT')
if not PROJECT_ROOT:
    raise EnvironmentError("PROJECT_ROOT environment variable must be set.")
OUTPUT_DIR = Path(PROJECT_ROOT) / 'landing' / 'linktree' / 'analytics'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def main():
    print("[INFO] Starting Linktree analytics extractor...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Intercept and save GraphQL responses
        def handle_response(response):
            if response.url.startswith('https://graph.linktr.ee/graphql'):
                try:
                    body = response.body()
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                    fname = OUTPUT_DIR / f"graphql_{ts}.json"
                    with open(fname, 'wb') as f:
                        f.write(body)
                    print(f"[SAVED] {fname}")
                except Exception as e:
                    print(f"[ERROR] Could not save response: {e}")
        context.on("response", handle_response)

        print("[INFO] Navigating to https://linktr.ee/admin/analytics ...")
        page.goto('https://linktr.ee/admin/analytics')

        # Wait for manual login if needed
        print("[ACTION REQUIRED] If prompted, please log in and complete any authentication steps.")
        print("[INFO] Waiting for navigation to https://linktr.ee/admin ...")
        page.wait_for_url("https://linktr.ee/admin", timeout=0)

        print("[INFO] Navigating again to analytics page...")
        page.goto('https://linktr.ee/admin/analytics')
        time.sleep(3)

        # Select 'Last 365 days' radio button
        print("[INFO] Selecting 'Last 365 days'...")
        try:
            page.get_by_label("Last 365 days").check()
        except Exception:
            # Fallback: click by id
            page.locator('input#last-365-days').check()
        time.sleep(2)

        # Click 'Daily' button
        print("[INFO] Clicking 'Daily' granularity button...")
        try:
            page.get_by_role('button', name='Daily').click()
        except Exception:
            # Fallback: click by text
            page.locator('button:has-text("Daily")').click()
        print("[INFO] Now capturing GraphQL network responses. The browser will stay open until you close it.")

        # Wait until browser closed by user
        try:
            while True:
                if not browser.contexts:
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            print("[INFO] Interrupted by user. Closing browser...")
        finally:
            browser.close()
            print("[INFO] Browser closed. Extraction complete.")

if __name__ == "__main__":
    main()
