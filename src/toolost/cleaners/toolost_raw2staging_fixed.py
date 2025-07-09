#!/usr/bin/env python3
"""
Fixed TooLost raw2staging cleaner that handles files in both locations:
- raw/toolost/streams/
- raw/toolost/
"""

import os
import json
from pathlib import Path
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parents[3]))
RAW = PROJECT_ROOT / os.getenv("RAW_ZONE", "raw")
STAGING = PROJECT_ROOT / os.getenv("STAGING_ZONE", "staging")


def find_latest_toolost_files():
    """
    Find the latest Spotify and Apple files from both possible locations.
    Returns the most recent files regardless of which directory they're in.
    """
    # Check both locations
    locations = [
        RAW / "toolost" / "streams",  # Original location
        RAW / "toolost"                # New location
    ]
    
    all_spotify_files = []
    all_apple_files = []
    
    for location in locations:
        if location.exists():
            # Find Spotify files
            spotify_files = list(location.glob("toolost_spotify_*.json"))
            all_spotify_files.extend(spotify_files)
            
            # Find Apple files
            apple_files = list(location.glob("toolost_apple_*.json"))
            all_apple_files.extend(apple_files)
    
    if not all_spotify_files:
        raise FileNotFoundError(f"No TooLost Spotify files found in {locations}")
    if not all_apple_files:
        raise FileNotFoundError(f"No TooLost Apple files found in {locations}")
    
    # Sort by modification time and get the most recent
    latest_spotify = max(all_spotify_files, key=lambda p: p.stat().st_mtime)
    latest_apple = max(all_apple_files, key=lambda p: p.stat().st_mtime)
    
    print(f"[TOOLOST] Found {len(all_spotify_files)} Spotify files across locations")
    print(f"[TOOLOST] Found {len(all_apple_files)} Apple files across locations")
    print(f"[TOOLOST] Using latest Spotify file: {latest_spotify}")
    print(f"[TOOLOST] Using latest Apple file: {latest_apple}")
    
    return latest_spotify, latest_apple


def validate_data(data, platform):
    """Validate the structure of TooLost data."""
    if not isinstance(data, dict):
        raise ValueError(f"{platform} data is not a dictionary")
    
    if platform == "spotify":
        if "streams" not in data:
            raise ValueError("Spotify data missing 'streams' key")
        if not isinstance(data["streams"], list):
            raise ValueError("Spotify streams is not a list")
    elif platform == "apple":
        if "totalStreams" not in data:
            raise ValueError("Apple data missing 'totalStreams' key")
        if not isinstance(data["totalStreams"], list):
            raise ValueError("Apple totalStreams is not a list")
    
    return True


def process_toolost_data():
    """Process TooLost data from raw to staging."""
    print("[TOOLOST] Starting raw2staging processing...")
    
    try:
        # Find latest files from both locations
        spotify_file, apple_file = find_latest_toolost_files()
        
        # Load data
        with spotify_file.open(encoding="utf-8") as f:
            spotify_data = json.load(f)
        
        with apple_file.open(encoding="utf-8") as f:
            apple_data = json.load(f)
        
        # Validate data structure
        validate_data(spotify_data, "spotify")
        validate_data(apple_data, "apple")
        
        # Process Spotify data
        if spotify_data["streams"]:
            sp_df = pd.DataFrame(spotify_data["streams"])
            sp_df["date"] = pd.to_datetime(sp_df["date"])
            sp_df["spotify_streams"] = sp_df["streams"].astype(int)
            sp_df = sp_df[["date", "spotify_streams"]]
        else:
            print("[TOOLOST] Warning: No Spotify stream data found")
            sp_df = pd.DataFrame(columns=["date", "spotify_streams"])
        
        # Process Apple data
        if apple_data["totalStreams"]:
            ap_df = pd.DataFrame(apple_data["totalStreams"])
            ap_df["date"] = pd.to_datetime(ap_df["date"])
            ap_df["apple_streams"] = ap_df["streams"].astype(int)
            ap_df = ap_df[["date", "apple_streams"]]
        else:
            print("[TOOLOST] Warning: No Apple stream data found")
            ap_df = pd.DataFrame(columns=["date", "apple_streams"])
        
        # Merge data
        if not sp_df.empty or not ap_df.empty:
            if sp_df.empty:
                df = ap_df.copy()
                df["spotify_streams"] = 0
            elif ap_df.empty:
                df = sp_df.copy()
                df["apple_streams"] = 0
            else:
                df = sp_df.merge(ap_df, on="date", how="outer")
            
            df = df.fillna(0)
            df["combined_streams"] = df["spotify_streams"] + df["apple_streams"]
            df = df.sort_values("date").reset_index(drop=True)
            
            print(f"[TOOLOST] Processed {len(df)} days of streaming data")
            print(f"[TOOLOST] Date range: {df['date'].min()} to {df['date'].max()}")
            print(f"[TOOLOST] Total Spotify streams: {df['spotify_streams'].sum():,}")
            print(f"[TOOLOST] Total Apple streams: {df['apple_streams'].sum():,}")
            print(f"[TOOLOST] Total combined streams: {df['combined_streams'].sum():,}")
            
            # Save to staging
            STAGING.mkdir(parents=True, exist_ok=True)
            output_file = STAGING / "daily_streams_toolost.csv"
            df.to_csv(output_file, index=False)
            print(f"[TOOLOST] Saved to: {output_file}")
            
            # Quality check
            assert df["combined_streams"].sum() == df["spotify_streams"].sum() + df["apple_streams"].sum(), \
                   "Quality check failed: combined != components"
            print("[TOOLOST] ✅ Quality check passed - totals align")
            
            # Log file locations for debugging
            log_info = {
                "timestamp": datetime.now().isoformat(),
                "spotify_source": str(spotify_file.relative_to(PROJECT_ROOT)),
                "apple_source": str(apple_file.relative_to(PROJECT_ROOT)),
                "output": str(output_file.relative_to(PROJECT_ROOT)),
                "records": len(df),
                "date_range": f"{df['date'].min()} to {df['date'].max()}"
            }
            
            log_file = STAGING / ".toolost_processing_log.json"
            with open(log_file, "w") as f:
                json.dump(log_info, f, indent=2, default=str)
            
        else:
            print("[TOOLOST] ERROR: No data found in either Spotify or Apple files")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"[TOOLOST] ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = process_toolost_data()
    exit(exit_code)