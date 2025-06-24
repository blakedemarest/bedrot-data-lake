"""
TikTok Network Discovery Test Script

This script explores TikTok's network traffic to identify API endpoints 
that return follower count data. It intercepts network requests and logs
relevant responses for analysis.

Usage:
    python test_follower_network_discovery.py --artist pig1987
    python test_follower_network_discovery.py --artist zonea0
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
PROJECT_ROOT = Path(os.environ.get('PROJECT_ROOT', '.'))
COOKIES_DIR = PROJECT_ROOT / 'src' / 'tiktok' / 'cookies'
OUTPUT_DIR = PROJECT_ROOT / 'sandbox' / 'tiktok_network_discovery'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Artist configuration
ARTIST_CONFIG = {
    'pig1987': {
        'profile_url': 'https://www.tiktok.com/@pig1987',
        'studio_url': 'https://www.tiktok.com/tiktokstudio',
        'cookies_file': 'tiktok_cookies_pig1987.json'
    },
    'zonea0': {
        'profile_url': 'https://www.tiktok.com/@zone.a0',
        'studio_url': 'https://www.tiktok.com/tiktokstudio', 
        'cookies_file': 'tiktok_cookies_zonea0.json'
    }
}

# API patterns to watch for
API_PATTERNS = [
    'api/user/detail',
    'api/creator',
    'api/analytics',
    'api/recommend',
    'aweme/v1/user',
    'tiktokstudio/api',
    'creator-center'
]

class NetworkDiscovery:
    def __init__(self, artist_name: str):
        self.artist_name = artist_name
        self.config = ARTIST_CONFIG.get(artist_name)
        self.captured_responses = []
        self.follower_candidates = []
        
        if not self.config:
            raise ValueError(f"Unknown artist: {artist_name}")
    
    def load_cookies(self, context):
        """Load cookies from existing JSON file."""
        cookies_path = COOKIES_DIR / self.config['cookies_file']
        if not cookies_path.exists():
            print(f"[WARN] Cookie file not found: {cookies_path}")
            return False
            
        try:
            with open(cookies_path, 'r') as f:
                cookies = json.load(f)
            
            # Clean invalid sameSite values
            for cookie in cookies:
                if "sameSite" in cookie and cookie["sameSite"] not in {"Strict", "Lax", "None"}:
                    cookie["sameSite"] = "Lax"
            
            context.add_cookies(cookies)
            print(f"[INFO] Loaded {len(cookies)} cookies for {self.artist_name}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to load cookies: {e}")
            return False
    
    async def handle_response(self, response):
        """Intercept and analyze network responses."""
        url = response.url
        
        # Check if this matches any API patterns we're interested in
        for pattern in API_PATTERNS:
            if pattern in url:
                try:
                    # Attempt to get JSON response
                    json_data = await response.json()
                    
                    # Store the response for analysis
                    capture = {
                        'url': url,
                        'status': response.status,
                        'timestamp': datetime.now().isoformat(),
                        'headers': dict(response.headers),
                        'json_data': json_data
                    }
                    
                    self.captured_responses.append(capture)
                    
                    # Look for follower-related data
                    self.analyze_for_follower_data(capture, json_data)
                    
                    print(f"[CAPTURE] {pattern} API: {response.status} - {url}")
                    
                except Exception as e:
                    # Not JSON or other error - still log the URL
                    capture = {
                        'url': url,
                        'status': response.status,
                        'timestamp': datetime.now().isoformat(),
                        'headers': dict(response.headers),
                        'error': str(e)
                    }
                    self.captured_responses.append(capture)
                    print(f"[CAPTURE] {pattern} API (non-JSON): {response.status} - {url}")
                break
    
    def analyze_for_follower_data(self, capture: Dict, json_data: Dict):
        """Analyze JSON response for potential follower count data."""
        def find_numeric_fields(obj, path=""):
            """Recursively find numeric fields that could be follower counts."""
            candidates = []
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    if isinstance(value, (int, float)) and value > 0:
                        # Look for fields that might be follower counts
                        key_lower = key.lower()
                        if any(term in key_lower for term in ['follow', 'fan', 'subscriber', 'count']):
                            candidates.append({
                                'path': current_path,
                                'value': value,
                                'key': key,
                                'confidence': 'high' if 'follow' in key_lower else 'medium'
                            })
                        elif isinstance(value, int) and 10 < value < 10000000:  # Reasonable follower range
                            candidates.append({
                                'path': current_path,
                                'value': value,
                                'key': key,
                                'confidence': 'low'
                            })
                    
                    elif isinstance(value, (dict, list)):
                        candidates.extend(find_numeric_fields(value, current_path))
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    candidates.extend(find_numeric_fields(item, f"{path}[{i}]"))
            
            return candidates
        
        candidates = find_numeric_fields(json_data)
        
        if candidates:
            follower_data = {
                'url': capture['url'],
                'timestamp': capture['timestamp'],
                'candidates': candidates
            }
            self.follower_candidates.append(follower_data)
            
            print(f"[FOLLOWER] Found {len(candidates)} potential follower fields in {capture['url']}")
            for candidate in candidates:
                print(f"    {candidate['path']}: {candidate['value']} (confidence: {candidate['confidence']})")
    
    async def discover_profile_apis(self):
        """Navigate to profile page and capture network traffic."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={"width": 1440, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            # Load cookies for authentication
            self.load_cookies(context)
            
            page = await context.new_page()
            
            # Set up response interception
            page.on('response', self.handle_response)
            
            print(f"[INFO] Navigating to {self.artist_name} profile...")
            
            # Navigate to profile page
            await page.goto(self.config['profile_url'])
            await page.wait_for_load_state('networkidle')
            
            # Wait a bit for any delayed API calls
            await asyncio.sleep(3)
            
            # Try scrolling to trigger more API calls
            await page.evaluate("window.scrollBy(0, 500)")
            await asyncio.sleep(2)
            
            print(f"[INFO] Profile navigation complete. Captured {len(self.captured_responses)} responses.")
            
            await browser.close()
    
    async def discover_studio_apis(self):
        """Navigate to TikTok Studio and capture network traffic."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={"width": 1440, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            # Load cookies for authentication
            self.load_cookies(context)
            
            page = await context.new_page()
            
            # Set up response interception
            page.on('response', self.handle_response)
            
            print(f"[INFO] Navigating to TikTok Studio...")
            
            # Navigate to TikTok Studio
            await page.goto(self.config['studio_url'])
            await page.wait_for_load_state('networkidle')
            
            # Wait for studio to load
            await asyncio.sleep(5)
            
            # Try navigating to different studio sections
            try:
                # Look for creator center or analytics links
                analytics_selectors = [
                    'a[href*="analytics"]',
                    'text=Analytics',
                    'text=Creator Center',
                    '[data-testid="analytics"]'
                ]
                
                for selector in analytics_selectors:
                    try:
                        element = page.locator(selector).first
                        if await element.is_visible(timeout=2000):
                            await element.click()
                            await asyncio.sleep(3)
                            print(f"[INFO] Clicked analytics section")
                            break
                    except:
                        continue
                        
            except Exception as e:
                print(f"[WARN] Could not navigate to analytics: {e}")
            
            print(f"[INFO] Studio navigation complete. Captured {len(self.captured_responses)} responses.")
            
            await browser.close()
    
    def save_results(self):
        """Save captured network data to files for analysis."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save all captured responses
        responses_file = OUTPUT_DIR / f"{self.artist_name}_network_capture_{timestamp}.json"
        with open(responses_file, 'w', encoding='utf-8') as f:
            json.dump(self.captured_responses, f, indent=2, default=str)
        
        # Save follower candidates
        followers_file = OUTPUT_DIR / f"{self.artist_name}_follower_candidates_{timestamp}.json"
        with open(followers_file, 'w', encoding='utf-8') as f:
            json.dump(self.follower_candidates, f, indent=2, default=str)
        
        # Generate analysis report
        report_file = OUTPUT_DIR / f"{self.artist_name}_analysis_report_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"TikTok Network Discovery Report - {self.artist_name}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Total API responses captured: {len(self.captured_responses)}\n")
            f.write(f"Potential follower data sources: {len(self.follower_candidates)}\n\n")
            
            if self.follower_candidates:
                f.write("FOLLOWER CANDIDATE ANALYSIS:\n")
                f.write("-" * 30 + "\n")
                
                for i, candidate_set in enumerate(self.follower_candidates, 1):
                    f.write(f"\n{i}. URL: {candidate_set['url']}\n")
                    f.write(f"   Time: {candidate_set['timestamp']}\n")
                    
                    for candidate in candidate_set['candidates']:
                        f.write(f"   → {candidate['path']}: {candidate['value']} (confidence: {candidate['confidence']})\n")
            
            # Summary of unique API endpoints
            f.write("\n\nUNIQUE API ENDPOINTS:\n")
            f.write("-" * 20 + "\n")
            unique_urls = set(r['url'] for r in self.captured_responses)
            for url in sorted(unique_urls):
                f.write(f"  {url}\n")
        
        print(f"[SAVE] Results saved to {OUTPUT_DIR}")
        print(f"  - Network capture: {responses_file.name}")
        print(f"  - Follower candidates: {followers_file.name}")
        print(f"  - Analysis report: {report_file.name}")

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Discover TikTok follower APIs")
    parser.add_argument("--artist", choices=['pig1987', 'zonea0'], required=True,
                       help="Artist account to analyze")
    parser.add_argument("--profile-only", action='store_true',
                       help="Only test profile page (skip TikTok Studio)")
    parser.add_argument("--studio-only", action='store_true', 
                       help="Only test TikTok Studio (skip profile)")
    
    args = parser.parse_args()
    
    discovery = NetworkDiscovery(args.artist)
    
    try:
        if not args.studio_only:
            print(f"[START] Profile API discovery for {args.artist}")
            await discovery.discover_profile_apis()
        
        if not args.profile_only:
            print(f"[START] Studio API discovery for {args.artist}")
            await discovery.discover_studio_apis()
        
        discovery.save_results()
        
        print(f"\n[COMPLETE] Network discovery finished for {args.artist}")
        print(f"Found {len(discovery.follower_candidates)} potential follower data sources")
        
    except Exception as e:
        print(f"[ERROR] Discovery failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())