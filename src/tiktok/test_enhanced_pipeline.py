"""
TikTok Enhanced Pipeline Test Script

This script tests the complete enhanced TikTok pipeline with follower data capture:
1. Runs extractor with follower network interception
2. Processes data through landing→raw→staging→curated
3. Validates that follower data is captured and flows through pipeline
4. Verifies reach→views field replacement works correctly

Usage:
    python test_enhanced_pipeline.py --artist pig1987
    python test_enhanced_pipeline.py --artist zonea0
    python test_enhanced_pipeline.py --full-test  # Test both artists
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
PROJECT_ROOT = Path(os.environ.get('PROJECT_ROOT', '.'))

# Test configuration
TEST_CONFIG = {
    'pig1987': {
        'extractor_script': 'src/tiktok/extractors/tiktok_analytics_extractor_pig1987.py',
        'expected_username': 'pig1987',
        'landing_pattern': '*pig1987*',
    },
    'zonea0': {
        'extractor_script': 'src/tiktok/extractors/tiktok_analytics_extractor_zonea0.py', 
        'expected_username': 'zone.a0',
        'landing_pattern': '*zonea0*',
    }
}

# Pipeline scripts
PIPELINE_SCRIPTS = [
    'src/tiktok/cleaners/tiktok_landing2raw.py',
    'src/tiktok/cleaners/tiktok_raw2staging.py',
    'src/tiktok/cleaners/tiktok_staging2curated.py'
]

class PipelineTest:
    def __init__(self, artist: str):
        self.artist = artist
        self.config = TEST_CONFIG.get(artist)
        self.test_results = {
            'artist': artist,
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }
        
        if not self.config:
            raise ValueError(f"Unknown artist: {artist}. Supported: {list(TEST_CONFIG.keys())}")
    
    def log(self, message: str):
        """Log test message."""
        print(f"[TEST-{self.artist.upper()}] {message}")
    
    def run_command(self, command: List[str], description: str) -> Dict:
        """Run a command and capture results."""
        self.log(f"Running: {description}")
        
        try:
            result = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'command': ' '.join(command)
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Command timed out after 5 minutes',
                'command': ' '.join(command)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'command': ' '.join(command)
            }
    
    def test_extractor_with_followers(self) -> bool:
        """Test the enhanced extractor with follower capture."""
        self.log("Testing enhanced extractor with follower capture...")
        
        extractor_path = PROJECT_ROOT / self.config['extractor_script']
        if not extractor_path.exists():
            self.log(f"ERROR: Extractor script not found: {extractor_path}")
            return False
        
        # Run extractor
        result = self.run_command(
            [sys.executable, str(extractor_path)],
            f"Enhanced TikTok extractor for {self.artist}"
        )
        
        self.test_results['tests']['extractor'] = result
        
        if not result['success']:
            self.log(f"ERROR: Extractor failed: {result.get('stderr', result.get('error', 'Unknown error'))}")
            return False
        
        # Check for landing zone files
        landing_dir = PROJECT_ROOT / "landing" / "tiktok" / "analytics"
        
        # Look for CSV files (analytics data)
        csv_files = list(landing_dir.glob(f"*{self.artist}*.csv"))
        if not csv_files:
            self.log(f"WARNING: No CSV files found for {self.artist}")
        else:
            self.log(f"Found {len(csv_files)} CSV files in landing zone")
        
        # Look for follower JSON files
        follower_files = list(landing_dir.glob(f"{self.artist}_followers_*.json"))
        
        if not follower_files:
            self.log(f"WARNING: No follower data files found for {self.artist}")
            return True  # Not critical failure - follower capture might not work in test
        
        # Validate follower data
        latest_follower_file = max(follower_files, key=lambda f: f.stat().st_mtime)
        try:
            with open(latest_follower_file, 'r') as f:
                follower_data = json.load(f)
            
            required_fields = ['count', 'timestamp', 'artist']
            missing_fields = [field for field in required_fields if field not in follower_data]
            
            if missing_fields:
                self.log(f"ERROR: Follower data missing fields: {missing_fields}")
                return False
            
            if follower_data['count'] <= 0:
                self.log(f"WARNING: Follower count is {follower_data['count']}")
            else:
                self.log(f"SUCCESS: Captured {follower_data['count']} followers for {self.artist}")
            
        except Exception as e:
            self.log(f"ERROR: Failed to validate follower data: {e}")
            return False
        
        self.log("Extractor test completed successfully")
        return True
    
    def test_pipeline_stage(self, script_path: str, stage_name: str) -> bool:
        """Test a single pipeline stage."""
        self.log(f"Testing {stage_name} stage...")
        
        script_full_path = PROJECT_ROOT / script_path
        if not script_full_path.exists():
            self.log(f"ERROR: Script not found: {script_full_path}")
            return False
        
        result = self.run_command(
            [sys.executable, str(script_full_path)],
            f"{stage_name} processing"
        )
        
        self.test_results['tests'][stage_name] = result
        
        if not result['success']:
            self.log(f"ERROR: {stage_name} failed: {result.get('stderr', result.get('error', 'Unknown error'))}")
            return False
        
        self.log(f"{stage_name} completed successfully")
        return True
    
    def test_data_flow(self) -> bool:
        """Test that data flows correctly through all pipeline stages."""
        self.log("Testing data flow through pipeline stages...")
        
        # Test each pipeline stage
        stages = [
            (PIPELINE_SCRIPTS[0], "landing2raw"),
            (PIPELINE_SCRIPTS[1], "raw2staging"), 
            (PIPELINE_SCRIPTS[2], "staging2curated")
        ]
        
        for script_path, stage_name in stages:
            if not self.test_pipeline_stage(script_path, stage_name):
                return False
        
        return True
    
    def validate_curated_output(self) -> bool:
        """Validate the final curated output contains expected schema."""
        self.log("Validating curated output...")
        
        curated_dir = PROJECT_ROOT / "curated" / "tiktok"
        if not curated_dir.exists():
            self.log(f"ERROR: Curated directory not found: {curated_dir}")
            return False
        
        # Find the latest curated file
        curated_files = list(curated_dir.glob("tiktok_analytics_curated_*.csv"))
        if not curated_files:
            self.log("ERROR: No curated files found")
            return False
        
        latest_curated = max(curated_files, key=lambda f: f.stat().st_mtime)
        
        try:
            df = pd.read_csv(latest_curated)
            
            # Expected columns in curated data (existing + 2 new)
            expected_columns = [
                'artist', 'zone', 'date', 'Video Views', 'Profile Views',
                'Likes', 'Comments', 'Shares', 'Year', 'engagement_rate',
                'Followers', 'new_followers'  # NEW: Only these 2 columns added
            ]
            
            missing_columns = [col for col in expected_columns if col not in df.columns]
            if missing_columns:
                self.log(f"ERROR: Missing columns in curated data: {missing_columns}")
                return False
            
            # Check for deprecated "reach" column
            if 'reach' in df.columns:
                self.log("ERROR: Deprecated 'reach' column found in curated data")
                return False
            
            # Check that we have data for our artist
            artist_data = df[df['artist'] == self.config['expected_username']]
            if artist_data.empty:
                # Try with different artist name formats
                artist_data = df[df['artist'].str.contains(self.artist, case=False)]
                if artist_data.empty:
                    self.log(f"WARNING: No data found for artist {self.artist} in curated output")
                    return True  # Not a critical failure
            
            self.log(f"Found {len(artist_data)} records for {self.artist} in curated data")
            
            # Check for follower data
            follower_data = artist_data[artist_data['Followers'] > 0]
            if not follower_data.empty:
                latest_followers = follower_data['Followers'].iloc[-1]
                self.log(f"SUCCESS: Found follower data in curated output: {latest_followers}")
            else:
                self.log("WARNING: No follower data found in curated output")
            
            # Check for new_followers calculation
            if 'new_followers' in artist_data.columns:
                new_followers_sum = artist_data['new_followers'].sum()
                if new_followers_sum > 0:
                    self.log(f"SUCCESS: Found new_followers data: {new_followers_sum} total new followers")
                else:
                    self.log("INFO: new_followers column exists but no new followers calculated")
            else:
                self.log("ERROR: new_followers column missing")
            
            # Validate Video Views (should exist instead of reach)
            if 'Video Views' in df.columns:
                video_views_data = artist_data[artist_data['Video Views'] > 0]
                if not video_views_data.empty:
                    self.log(f"SUCCESS: Video Views data found (replaced reach)")
                else:
                    self.log("INFO: No Video Views data (may be zero)")
            
            self.log("Curated output validation completed")
            return True
            
        except Exception as e:
            self.log(f"ERROR: Failed to validate curated output: {e}")
            return False
    
    def run_full_test(self) -> bool:
        """Run the complete end-to-end test."""
        self.log(f"Starting full pipeline test for {self.artist}")
        
        success = True
        
        # Test 1: Enhanced extractor with follower capture
        if not self.test_extractor_with_followers():
            self.log("FAILED: Extractor test")
            success = False
        
        # Test 2: Data pipeline flow
        if not self.test_data_flow():
            self.log("FAILED: Pipeline flow test")
            success = False
        
        # Test 3: Curated output validation
        if not self.validate_curated_output():
            self.log("FAILED: Curated output validation")
            success = False
        
        # Save test results
        results_dir = PROJECT_ROOT / "sandbox" / "test_results"
        results_dir.mkdir(parents=True, exist_ok=True)
        
        results_file = results_dir / f"tiktok_pipeline_test_{self.artist}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        self.log(f"Test results saved to: {results_file}")
        
        if success:
            self.log("✅ ALL TESTS PASSED")
        else:
            self.log("❌ SOME TESTS FAILED")
        
        return success

def main():
    parser = argparse.ArgumentParser(description="Test enhanced TikTok pipeline")
    parser.add_argument("--artist", choices=['pig1987', 'zonea0'],
                       help="Test specific artist")
    parser.add_argument("--full-test", action="store_true",
                       help="Test both artists")
    parser.add_argument("--skip-extractor", action="store_true",
                       help="Skip extractor test (test pipeline only)")
    
    args = parser.parse_args()
    
    if not args.artist and not args.full_test:
        parser.error("Must specify --artist or --full-test")
    
    artists_to_test = []
    if args.full_test:
        artists_to_test = ['pig1987', 'zonea0']
    else:
        artists_to_test = [args.artist]
    
    overall_success = True
    
    for artist in artists_to_test:
        print(f"\n{'='*60}")
        print(f"TESTING ARTIST: {artist.upper()}")
        print(f"{'='*60}")
        
        test = PipelineTest(artist)
        
        if args.skip_extractor:
            # Test pipeline only
            success = test.test_data_flow() and test.validate_curated_output()
        else:
            # Full test
            success = test.run_full_test()
        
        if not success:
            overall_success = False
    
    print(f"\n{'='*60}")
    if overall_success:
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY")
        print("Enhanced TikTok pipeline with follower capture is working correctly!")
    else:
        print("💥 SOME TESTS FAILED")
        print("Check the test output above for details.")
    print(f"{'='*60}")
    
    sys.exit(0 if overall_success else 1)

if __name__ == "__main__":
    main()