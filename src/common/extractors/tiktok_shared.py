import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from playwright.sync_api import Playwright


VALID_SAMESITE = {"Strict", "Lax", "None"}

# API patterns that may contain follower data
FOLLOWER_API_PATTERNS = [
    'api/user/detail',
    'api/creator', 
    'api/analytics',
    'tiktokstudio/api',
    'aweme/v1/user'
]


def _import_cookies(context, cookies_path: str, marker_path: str) -> None:
    """Import cookies once per user data directory."""
    if not os.path.exists(cookies_path) or os.path.exists(marker_path):
        return
    with open(cookies_path, "r") as f:
        cookies = json.load(f)
    for cookie in cookies:
        if "sameSite" in cookie and cookie["sameSite"] not in VALID_SAMESITE:
            cookie["sameSite"] = "Lax"
    context.add_cookies(cookies)
    with open(marker_path, "w") as marker:
        marker.write("imported")


def _extract_follower_from_json(json_data: Dict) -> Optional[int]:
    """Extract follower count from API JSON response."""
    def search_for_follower_count(obj, path=""):
        """Recursively search for follower count in nested JSON."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                # Direct follower field matches
                key_lower = key.lower()
                if any(term in key_lower for term in ['follower', 'fan']):
                    if isinstance(value, (int, float)) and value > 0:
                        return int(value)
                
                # Common TikTok API patterns
                if key in ['followerCount', 'fans', 'follower_count']:
                    if isinstance(value, (int, float)) and value > 0:
                        return int(value)
                
                # Recurse into nested objects
                if isinstance(value, (dict, list)):
                    result = search_for_follower_count(value, current_path)
                    if result is not None:
                        return result
        
        elif isinstance(obj, list):
            for item in obj:
                result = search_for_follower_count(item, path)
                if result is not None:
                    return result
        
        return None
    
    return search_for_follower_count(json_data)


def _capture_follower_data(page, artist_name: str, output_dir: Path) -> Optional[Dict]:
    """Capture follower count via network interception."""
    follower_data = {}
    captured_responses = []
    
    def handle_response(response):
        """Handle network responses to find follower data."""
        url = response.url
        
        # Check if this response might contain follower data
        for pattern in FOLLOWER_API_PATTERNS:
            if pattern in url:
                try:
                    json_data = response.json()
                    follower_count = _extract_follower_from_json(json_data)
                    
                    if follower_count:
                        print(f"[FOLLOWER] Found count {follower_count} in {pattern} API")
                        follower_data['count'] = follower_count
                        follower_data['source_url'] = url
                        follower_data['timestamp'] = datetime.now().isoformat()
                        follower_data['artist'] = artist_name
                    
                    # Store response for debugging
                    captured_responses.append({
                        'url': url,
                        'pattern': pattern,
                        'follower_count': follower_count,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    print(f"[DEBUG] Failed to parse {pattern} response: {e}")
                break
    
    # Set up response interception
    page.on('response', handle_response)
    
    # Navigate to profile to trigger API calls
    profile_url = f"https://www.tiktok.com/@{artist_name}"
    try:
        print(f"[FOLLOWER] Navigating to {profile_url} for follower data...")
        page.goto(profile_url)
        page.wait_for_load_state('networkidle', timeout=10000)
        
        # Wait for API calls to complete
        time.sleep(3)
        
        # Try scrolling to trigger more API calls
        page.evaluate("window.scrollBy(0, 300)")
        time.sleep(2)
        
    except Exception as e:
        print(f"[WARN] Profile navigation failed: {e}")
    
    # Save captured data for debugging
    if captured_responses:
        debug_file = output_dir / f"follower_debug_{artist_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(debug_file, 'w') as f:
            json.dump(captured_responses, f, indent=2)
        print(f"[DEBUG] Saved follower debug data to {debug_file.name}")
    
    # Validate follower count against page display
    if follower_data.get('count'):
        try:
            # Look for follower count displayed on page
            follower_selectors = [
                '[data-e2e="followers-count"]',
                'strong:has-text("Followers")',
                '.follower-count',
                '[class*="follower"]'
            ]
            
            for selector in follower_selectors:
                try:
                    element = page.locator(selector).first
                    if element.is_visible(timeout=2000):
                        page_text = element.inner_text()
                        print(f"[VALIDATION] Page shows follower text: {page_text}")
                        break
                except:
                    continue
                    
        except Exception as e:
            print(f"[DEBUG] Page validation failed: {e}")
    
    return follower_data if follower_data.get('count') else None


def _wait_for_analytics_page(context, analytics_prefix: str) -> Optional["Page"]:
    tracked_pages = set(context.pages)

    def on_new_page(page):
        tracked_pages.add(page)

    context.on("page", on_new_page)
    found_page = None
    while True:
        tracked_pages = {p for p in tracked_pages if not p.is_closed()}
        if not tracked_pages:
            return None
        for p in tracked_pages:
            if p.url.startswith(analytics_prefix):
                found_page = p
                break
        if found_page:
            break
        time.sleep(1)
    return found_page


def run_extraction(
    playwright: Playwright,
    user_data_dir: str,
    analytics_url: str,
    output_dir: Path,
    cookies_path: Optional[str] = None,
    marker_path: Optional[str] = None,
    capture_followers: bool = True,
    artist_name: Optional[str] = None,
) -> Dict:
    """Run the shared TikTok analytics extraction routine with follower capture."""
    os.makedirs(user_data_dir, exist_ok=True)
    context = playwright.chromium.launch_persistent_context(
        user_data_dir,
        headless=False,
        viewport={"width": 1440, "height": 900},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        args=["--disable-blink-features=AutomationControlled"],
    )

    page = context.pages[0] if context.pages else context.new_page()
    
    # Initialize result dictionary
    extraction_result = {
        'csv_downloaded': False,
        'csv_path': None,
        'follower_data': None,
        'timestamp': datetime.now().isoformat()
    }

    if cookies_path and marker_path:
        _import_cookies(context, cookies_path, marker_path)

    # Step 1: Capture follower data if requested
    follower_data = None
    if capture_followers and artist_name:
        print(f"[INFO] Capturing follower data for {artist_name}...")
        follower_data = _capture_follower_data(page, artist_name, output_dir)
        extraction_result['follower_data'] = follower_data
        
        if follower_data:
            print(f"[SUCCESS] Captured follower count: {follower_data['count']}")
            # Save follower data to JSON file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            follower_file = output_dir / f"{artist_name}_followers_{timestamp}.json"
            with open(follower_file, 'w') as f:
                json.dump(follower_data, f, indent=2)
            print(f"[FOLLOWER] Saved to {follower_file.name}")
        else:
            print(f"[WARN] Could not capture follower data for {artist_name}")

    # Step 2: Navigate to analytics for CSV download
    page.goto(analytics_url)
    page.wait_for_url(analytics_url)

    analytics_prefix = analytics_url.split("/analytics")[0] + "/analytics"
    page = _wait_for_analytics_page(context, analytics_prefix)
    if page is None:
        print("Analytics page not found. Browser remains open for manual intervention.")
        return extraction_result

    time.sleep(3)
    import random

    # Try multiple strategies to click the date range button
    date_clicked = False
    
    # Strategy 1: Look for "Last 7 days" button
    for attempt in range(3):
        try:
            if page.get_by_role("button", name="Last 7 days").is_visible():
                page.get_by_role("button", name="Last 7 days").click()
                print("[INFO] Clicked 'Last 7 days' button")
                date_clicked = True
                break
        except Exception as e:
            print(f"[DEBUG] Last 7 days attempt {attempt + 1} failed: {e}")
            time.sleep(2)
    
    # Strategy 2: Look for any date range button
    if not date_clicked:
        for attempt in range(3):
            try:
                # Look for buttons containing "days" or common date patterns
                selectors = [
                    "button:has-text('7 days')",
                    "button:has-text('days')", 
                    "[role='button']:has-text('7')",
                    ".date-selector button",
                    "[data-testid*='date'] button"
                ]
                
                for selector in selectors:
                    if page.locator(selector).first.is_visible():
                        page.locator(selector).first.click()
                        print(f"[INFO] Clicked date button using selector: {selector}")
                        date_clicked = True
                        break
                
                if date_clicked:
                    break
                    
            except Exception as e:
                print(f"[DEBUG] Alternative date selector attempt {attempt + 1} failed: {e}")
                time.sleep(2)
    
    if not date_clicked:
        raise RuntimeError("Could not find or click date range selector")
    
    # Wait for dropdown and select 365 days
    time.sleep(2)
    
    # Try to find and click 365 days option
    days_365_clicked = False
    for attempt in range(3):
        try:
            if page.wait_for_selector("text=Last 365 days", timeout=5000):
                page.locator("text=Last 365 days").click()
                print("[INFO] Selected 'Last 365 days'")
                days_365_clicked = True
                break
        except Exception as e:
            print(f"[DEBUG] 365 days selection attempt {attempt + 1} failed: {e}")
            # Try alternative selectors
            try:
                alt_selectors = [
                    "text=365 days",
                    "button:has-text('365')",
                    "[role='option']:has-text('365')"
                ]
                for selector in alt_selectors:
                    if page.locator(selector).first.is_visible():
                        page.locator(selector).first.click()
                        print(f"[INFO] Selected 365 days using: {selector}")
                        days_365_clicked = True
                        break
                if days_365_clicked:
                    break
            except Exception:
                pass
            time.sleep(2)
    
    if not days_365_clicked:
        print("[WARN] Could not select 365 days, proceeding with current selection")
    
    time.sleep(random.uniform(2.0, 3.0))

    page.get_by_role("button", name="Download data").click()
    page.wait_for_selector("text=Download Overview data")
    page.locator('input[type="radio"][value="CSV"]').check()
    with page.expect_download() as download_info:
        page.locator('button:has-text("Download")').last.click()
    download = download_info.value
    save_path = output_dir / download.suggested_filename
    download.save_as(save_path)
    
    # Update extraction result
    extraction_result['csv_downloaded'] = True
    extraction_result['csv_path'] = str(save_path)

    if not page.is_closed():
        page.close()
    context.close()
    
    print("Extraction complete. Browser closed automatically after data capture.")
    print(f"[RESULT] CSV: {extraction_result['csv_downloaded']}, Followers: {extraction_result['follower_data'] is not None}")
    
    return extraction_result
