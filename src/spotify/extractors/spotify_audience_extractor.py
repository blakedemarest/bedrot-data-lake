"""spotify_audience_extractor.py
Automates Spotify for Artists Audience stats CSV download via Playwright.

Workflow:
1. Navigate to the artist homepage (https://artists.spotify.com/c/en/artist/<ARTIST_ID>).  
2. Detect whether login is required; if so, waits for the user (and 2-FA) to finish.  
3. Click the **Audience** navigation item.  
4. Open **Filters** → choose **12 months** → click **Done**.  
5. Click the CSV **download** button, capture the download, and write it to
   ``landing/spotify/audience`` with a timestamped filename.

Script follows the conventions in ``LLM_cleaner_guidelines.md`` and is modelled
on ``linktree_analytics_extractor.py``.

Usage
-----
$ python spotify_audience_extractor.py                            # default artist
$ python spotify_audience_extractor.py --artist 1Eu67EqPy2NutiM0lqCarw
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# Ensure PROJECT_ROOT is set and src/ is on sys.path for direct execution.
PROJECT_ROOT = os.environ.get("PROJECT_ROOT")
if not PROJECT_ROOT:
    raise EnvironmentError("PROJECT_ROOT environment variable must be set.")
SRC_PATH = str(Path(PROJECT_ROOT) / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from common.cookies import load_cookies  # noqa: E402

# ---------------------------------------------------------------------------
# Constants & helpers
# ---------------------------------------------------------------------------
DEFAULT_ARTIST_IDS = [
    "62owJQCD2XzVB2o19CVsFM",  # a0
    "1Eu67EqPy2NutiM0lqCarw",  # pig1987
]
LANDING_DIR = Path(PROJECT_ROOT) / "landing" / "spotify" / "audience"
LANDING_DIR.mkdir(parents=True, exist_ok=True)

AUDIENCE_NAV_SELECTOR = "a#navigation-link-audience"
FILTER_CHIP_SELECTOR = "button[data-encore-id='chipFilter']"
# Try both explicit for="1year" label or any element containing the text
FILTER_12M_LABEL = "label[for='1year'], :text('12 months')"
FILTER_DONE_SELECTOR = "button:has-text('Done'), span:has-text('Done')"
CSV_DOWNLOAD_BUTTON = "button[data-testid='csv-download']"


def _click(page, selector: str, desc: str | None = None, retries: int = 3) -> None:
    """Click the first element matching *selector* with basic retry."""
    for attempt in range(1, retries + 1):
        try:
            locator = page.locator(selector).first
            # Wait for element to be both attached and visible
            locator.wait_for(state="attached")
            locator.wait_for(state="visible")
            # Scroll into view if needed
            locator.scroll_into_view_if_needed()
            # Small delay for any animations
            time.sleep(0.5)
            locator.click(force=True)
            if desc:
                print(f"[INFO] Clicked {desc} → {selector}")
            return
        except Exception as exc:
            print(f"[WARN] Attempt {attempt}/{retries} to click {selector} failed: {exc}")
            time.sleep(2)  # Longer wait between retries
    raise RuntimeError(f"Failed to click element: {selector}")


def _wait_for_audience_nav(page):
    """Ensure the Audience nav link is present – indicates authenticated state."""
    try:
        page.wait_for_selector(AUDIENCE_NAV_SELECTOR)
        print("[INFO] Audience nav link detected – authentication complete.")
    except PWTimeout:
        raise RuntimeError("Audience nav link not found – are you logged in?")


def _login_if_needed(page, artist_url: str) -> None:
    """Navigate to *artist_url* and wait for login (incl. 2FA) if necessary."""
    print(f"[INFO] Navigating to {artist_url} …")
    page.goto(artist_url, wait_until="domcontentloaded")

    try:
        _wait_for_audience_nav(page)
    except RuntimeError:
        print("[ACTION REQUIRED] Please log in to Spotify for Artists (2-FA if prompted)…")
        # Poll until Audience nav becomes visible or user aborts.
        try:
            _wait_for_audience_nav(page)
        except RuntimeError:
            raise RuntimeError("Login not completed within timeout.")


def _apply_12_month_filter(page):
    """Open the filter chip, pick 12-month option, click Done."""
    print("[INFO] Opening filter chip…")
    _click(page, FILTER_CHIP_SELECTOR, desc="Filters chip")

    # Wait for the option to appear (attached first, then visible)
    page.wait_for_selector(FILTER_12M_LABEL, state="attached")
    # Give time for animations
    time.sleep(2)
    
    # Some times the option becomes visible slightly later
    _click(page, FILTER_12M_LABEL, desc="12-month label", retries=5)
    
    # Wait for page state to update after selection
    time.sleep(2)
    
    # Try multiple strategies for the Done button
    done_clicked = False
    
    # Strategy 1: Look for exact Done button
    for attempt in range(3):
        try:
            if page.locator("button:has-text('Done')").first.is_visible():
                page.locator("button:has-text('Done')").first.click()
                print("[INFO] Clicked Done button (strategy 1)")
                done_clicked = True
                break
        except Exception as e:
            print(f"[DEBUG] Done button strategy 1 attempt {attempt + 1} failed: {e}")
            time.sleep(1)
    
    # Strategy 2: Look for span with Done text
    if not done_clicked:
        for attempt in range(3):
            try:
                if page.locator("span:has-text('Done')").first.is_visible():
                    page.locator("span:has-text('Done')").first.click()
                    print("[INFO] Clicked Done button (strategy 2)")
                    done_clicked = True
                    break
            except Exception as e:
                print(f"[DEBUG] Done button strategy 2 attempt {attempt + 1} failed: {e}")
                time.sleep(1)
    
    # Strategy 3: Press Escape key to close dialog
    if not done_clicked:
        try:
            page.keyboard.press("Escape")
            print("[INFO] Pressed Escape to close filter dialog")
            done_clicked = True
        except Exception as e:
            print(f"[DEBUG] Escape key strategy failed: {e}")
    
    if not done_clicked:
        print("[WARN] Could not close filter dialog, but proceeding to check for CSV button")
    
    # Wait for filter to be applied and CSV button to be available
    for attempt in range(10):
        try:
            if page.locator(CSV_DOWNLOAD_BUTTON).first.is_visible():
                print("[INFO] CSV download button is visible - filter likely applied")
                break
        except Exception:
            pass
        time.sleep(1)
        print(f"[DEBUG] Waiting for CSV button, attempt {attempt + 1}/10")
    
    # Final check
    page.wait_for_selector(CSV_DOWNLOAD_BUTTON)
    print("[INFO] 12-month filter applied (CSV button visible).")


def _download_csv(page, artist_id: str) -> Path:
    """Trigger CSV download and return path of saved file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suggested_name = f"spotify_audience_{artist_id}_{timestamp}.csv"
    dest_path = LANDING_DIR / suggested_name

    with page.expect_download() as dl_info:
        _click(page, CSV_DOWNLOAD_BUTTON, desc="CSV download button")
    download = dl_info.value
    download.save_as(dest_path)
    print(f"[SAVED] CSV → {dest_path.relative_to(PROJECT_ROOT)}")
    return dest_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Spotify Audience extractor")
    parser.add_argument("--artists", nargs="*", default=DEFAULT_ARTIST_IDS, help="Space-separated list of Spotify Artist IDs")
    args = parser.parse_args()
    artist_ids: list[str] = args.artists

    print(f"[INFO] Starting Spotify Audience extractor for {len(artist_ids)} artist(s)…")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        load_cookies(context, "spotify")
        page = context.new_page()

        try:
            for aid in artist_ids:
                artist_url = f"https://artists.spotify.com/c/en/artist/{aid}"
                _login_if_needed(page, artist_url)
                _click(page, AUDIENCE_NAV_SELECTOR, desc="Audience nav link")
                page.wait_for_load_state("domcontentloaded")
                print(f"[INFO] Audience page loaded for {aid}.")
                _apply_12_month_filter(page)
                _download_csv(page, aid)
                # Navigate back to generic home between iterations to reset state
                page.goto("https://artists.spotify.com/home", wait_until="domcontentloaded")
        except KeyboardInterrupt:
            print("[INFO] Interrupted by user.")
        except Exception as exc:
            print(f"[ERROR] Extraction failed: {exc}")
            raise
            print("[INFO] Interrupted by user.")
        finally:
            try:
                browser.close()
            except Exception:
                pass
            print("[INFO] Browser closed. Extraction complete.")


if __name__ == "__main__":
    main()
