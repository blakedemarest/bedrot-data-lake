"""
TikTok Landing→Raw cleaner for analytics data.

Processes ZIP files containing CSV exports from TikTok analytics dashboard.
Extracts, validates, and converts CSV data to NDJSON format in raw zone.

Guided by LLM_cleaner_guidelines.md
"""

# %% Imports & Constants
import argparse
import json
import os
import zipfile
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

PLATFORM = "tiktok"
PROJECT_ROOT = Path(os.environ["PROJECT_ROOT"])
LANDING_DIR = PROJECT_ROOT / "landing" / PLATFORM / "analytics"
RAW_DIR = PROJECT_ROOT / "raw" / PLATFORM

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)

print(f"[INFO] PROJECT_ROOT: {PROJECT_ROOT}")
print(f"[INFO] LANDING_DIR: {LANDING_DIR}")
print(f"[INFO] RAW_DIR: {RAW_DIR}")

# %% Helper Functions

def find_latest_zips(landing_dir: Path) -> Dict[str, Path]:
    """Find the latest ZIP file per artist in landing directory."""
    all_zips = list(landing_dir.glob("*.zip"))
    if not all_zips:
        raise FileNotFoundError(f"No .zip files found in {landing_dir}")
    
    latest_per_artist = {}
    for zip_path in all_zips:
        base = zip_path.stem
        artist = base.split("_")[-1]  # token after last underscore
        mtime = zip_path.stat().st_mtime
        
        if artist not in latest_per_artist or mtime > latest_per_artist[artist][1]:
            latest_per_artist[artist] = (zip_path, mtime)
    
    # Return just the paths
    return {artist: path for artist, (path, _) in latest_per_artist.items()}


def load_follower_data(artist: str) -> Optional[Dict]:
    """Load the latest follower data JSON file for an artist."""
    # Look for follower JSON files in landing directory
    follower_pattern = f"{artist}_followers_*.json"
    follower_files = list(LANDING_DIR.glob(follower_pattern))
    
    if not follower_files:
        print(f"[FOLLOWER] No follower data found for {artist}")
        return None
    
    # Get the most recent follower file
    latest_follower_file = max(follower_files, key=lambda f: f.stat().st_mtime)
    
    try:
        with open(latest_follower_file, 'r') as f:
            follower_data = json.load(f)
        print(f"[FOLLOWER] Loaded follower data from {latest_follower_file.name}")
        return follower_data
    except Exception as e:
        print(f"[ERROR] Failed to load follower data from {latest_follower_file}: {e}")
        return None


def transform_csv_to_records(df: pd.DataFrame, artist: str, follower_data: Optional[Dict] = None) -> List[Dict]:
    """Transform CSV DataFrame to list of JSON records with optional follower data."""
    records = []
    
    # Extract follower count from follower_data if available
    follower_count = 0
    if follower_data and 'count' in follower_data:
        follower_count = follower_data['count']
        print(f"[TRANSFORM] Using follower count: {follower_count} for {artist}")
    
    for _, row in df.iterrows():
        record = {
            "artist": artist,
            "date": row["Date"].strftime("%Y-%m-%d"),
            "year": int(row["Year"]),
            "video_views": int(row.get("Video Views", 0)),
            "profile_views": int(row.get("Profile Views", 0)),
            "likes": int(row.get("Likes", 0)),
            "comments": int(row.get("Comments", 0)),
            "shares": int(row.get("Shares", 0)),
            "followers": follower_count,  # NEW: Current follower count
            "processed_at": datetime.now().isoformat()
        }
        records.append(record)
    return records


def process_artist_csv(csv_path: Path, artist: str, start_year: int = 2024) -> Optional[List[Dict]]:
    """Process a single artist's CSV file directly and return records."""
    print(f"[RAW] Processing artist: {artist}")
    
    # Load follower data for this artist
    follower_data = load_follower_data(artist)
    
    try:
        df = pd.read_csv(csv_path)
        print(f"[RAW] Loaded: {csv_path.name} ({len(df)} rows)")
        
        if len(df) == 0:
            print(f"[WARN] {csv_path.name} is empty")
            return None
        
        # Check if dates need processing or are already in proper format
        if 'Date' in df.columns:
            # Try to parse dates as-is first
            test_dates = pd.to_datetime(df['Date'].head(), errors='coerce')
            if not test_dates.isna().all():
                # Dates are already in proper format
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df['Year'] = df['Date'].dt.year
                print(f"[RAW] Using existing date format")
            else:
                # Apply year rollover logic for month-day format
                dates = []
                current_year = start_year
                for md in df['Date']:
                    dt = pd.to_datetime(f"{md} {current_year}", format="%B %d %Y", errors='coerce')
                    if pd.isna(dt):
                        print(f"[WARN] Failed to parse date: {md}")
                        continue
                    if dates and dt <= dates[-1]:
                        current_year += 1
                        dt = pd.to_datetime(f"{md} {current_year}", format="%B %d %Y")
                    dates.append(dt)
                
                if len(dates) != len(df):
                    print(f"[WARN] Date parsing failed for some rows, using available data")
                    # Truncate DataFrame to match parsed dates
                    df = df.head(len(dates))
                    
                df['Date'] = dates
                df['Year'] = df['Date'].dt.year
                print(f"[RAW] Date rollover: {start_year} → {df['Year'].max()}")
        
        # Validate for missing values
        missing = df.isna().sum()
        missing_cols = missing[missing > 0]
        if len(missing_cols) > 0:
            print(f"[WARN] Missing values detected: {dict(missing_cols)}")
        
        # Transform to records with follower data
        records = transform_csv_to_records(df, artist, follower_data)
        print(f"[RAW] Transformed to {len(records)} JSON records")
        
        return records
        
    except Exception as e:
        print(f"[ERROR] Failed to process {csv_path.name}: {e}")
        return None


def process_artist_zip(zip_path: Path, artist: str, start_year: int = 2024) -> Optional[List[Dict]]:
    """Process a single artist's ZIP file and return records."""
    print(f"[RAW] Processing artist: {artist}")
    
    # Load follower data for this artist
    follower_data = load_follower_data(artist)
    
    temp_dir = None
    try:
        # Extract ZIP to temp directory
        temp_dir = Path(tempfile.mkdtemp(prefix=f"tiktok_{artist}_"))
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(temp_dir)
        
        # Find and load the single CSV
        csvs = list(temp_dir.glob("*.csv"))
        if len(csvs) != 1:
            print(f"[ERROR] Expected 1 CSV in {zip_path.name}, found {len(csvs)}")
            return None
        
        csv_path = csvs[0]
        df = pd.read_csv(csv_path)
        print(f"[RAW] Loaded: {csv_path.name} ({len(df)} rows)")
        
        # Apply year rollover logic
        dates = []
        current_year = start_year
        for md in df['Date']:
            dt = pd.to_datetime(f"{md} {current_year}", format="%B %d %Y", errors='coerce')
            if pd.isna(dt):
                print(f"[ERROR] Failed to parse date: {md}")
                continue
            if dates and dt <= dates[-1]:
                current_year += 1
                dt = pd.to_datetime(f"{md} {current_year}", format="%B %d %Y")
            dates.append(dt)
        
        if len(dates) != len(df):
            print(f"[ERROR] Date parsing failed for some rows")
            return None
            
        df['Date'] = dates
        df['Year'] = df['Date'].dt.year
        print(f"[RAW] Date rollover: {start_year} → {df['Year'].max()}")
        
        # Validate for missing values
        missing = df.isna().sum()
        missing_cols = missing[missing > 0]
        if not missing_cols.empty:
            print(f"[ERROR] Missing values detected: {missing_cols.to_dict()}")
            return None
        
        # Transform to records with follower data
        records = transform_csv_to_records(df, artist, follower_data)
        print(f"[RAW] Transformed to {len(records)} JSON records")
        return records
        
    except Exception as e:
        print(f"[ERROR] Processing {zip_path.name}: {e}")
        return None
    finally:
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir)

# %% Core Processing Logic

def find_latest_files(landing_dir: Path) -> Dict[str, Path]:
    """Find the latest file (ZIP or CSV) per artist in landing directory."""
    all_files = list(landing_dir.glob("*.zip")) + list(landing_dir.glob("*.csv"))
    if not all_files:
        raise FileNotFoundError(f"No .zip or .csv files found in {landing_dir}")
    
    latest_per_artist = {}
    for file_path in all_files:
        base = file_path.stem
        artist = base.split("_")[-1]  # token after last underscore
        mtime = file_path.stat().st_mtime
        
        if artist not in latest_per_artist or mtime > latest_per_artist[artist][1]:
            latest_per_artist[artist] = (file_path, mtime)
    
    # Return just the paths
    return {artist: path for artist, (path, _) in latest_per_artist.items()}


def process_landing_files(file_path: Optional[Path] = None) -> int:
    """Process TikTok landing files and write NDJSON to raw zone."""
    if file_path:
        # Process single file
        artist = file_path.stem.split("_")[-1]
        latest_zips = {artist: file_path}
    else:
        # Find all latest files (CSV or ZIP)
        latest_zips = find_latest_files(LANDING_DIR)
    
    if not latest_zips:
        print(f"[WARN] No files found in {LANDING_DIR}")
        return 0
    
    print(f"[RAW] Found {len(latest_zips)} artists: {list(latest_zips.keys())}")
    
    processed_count = 0
    for artist, file_path in latest_zips.items():
        try:
            if file_path.suffix == '.csv':
                records = process_artist_csv(file_path, artist)
            else:  # .zip file
                records = process_artist_zip(file_path, artist)
            if records:
                # Write NDJSON output
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_name = f"{file_path.stem}_{timestamp}.ndjson"
                output_path = RAW_DIR / output_name
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    for record in records:
                        json.dump(record, f)
                        f.write('\n')
                
                print(f"[RAW] Written {len(records)} records → {output_name}")
                processed_count += 1
            
        except Exception as e:
            print(f"[ERROR] Failed to process {artist}: {e}")
            continue
    
    if processed_count == 0:
        raise RuntimeError("No files were successfully processed")
    
    print(f"[RAW] Successfully processed {processed_count} artists")
    return processed_count

# %% CLI Entry Point

def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="TikTok Landing→Raw cleaner")
    parser.add_argument("--file", type=Path, help="Process specific ZIP file")
    args = parser.parse_args()
    
    try:
        count = process_landing_files(args.file)
        print(f"[RAW] Completed: {count} artists processed")
    except Exception as e:
        print(f"[ERROR] Processing failed: {e}")
        raise


if __name__ == "__main__":
    main()