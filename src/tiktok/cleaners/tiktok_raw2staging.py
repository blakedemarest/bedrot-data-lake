"""
TikTok Raw→Staging cleaner for analytics data.

Reads NDJSON files from raw zone, normalizes schema, and outputs
consolidated CSV to staging zone with incremental loading.

Guided by LLM_cleaner_guidelines.md
"""

# %% Imports & Constants
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

PLATFORM = "tiktok"
PROJECT_ROOT = Path(os.environ["PROJECT_ROOT"])
RAW_DIR = PROJECT_ROOT / "raw" / PLATFORM
STAGING_DIR = PROJECT_ROOT / "staging"

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
STAGING_DIR.mkdir(parents=True, exist_ok=True)

print(f"[INFO] PROJECT_ROOT: {PROJECT_ROOT}")
print(f"[INFO] RAW_DIR: {RAW_DIR}")
print(f"[INFO] STAGING_DIR: {STAGING_DIR}")

# %% Helper Functions

def load_ndjson_files() -> Dict[str, Path]:
    """Find the latest NDJSON file per artist in raw directory."""
    ndjson_files = list(RAW_DIR.glob("*.ndjson"))
    if not ndjson_files:
        raise FileNotFoundError(f"No NDJSON files found in {RAW_DIR}")
    
    latest_per_artist = {}
    for file_path in ndjson_files:
        # Extract artist from different filename patterns
        filename = file_path.stem
        artist = None
        
        # Pattern 1: enhanced_test_pig1987_20250624_test.ndjson
        if "enhanced_test" in filename:
            parts = filename.split("_")
            for i, part in enumerate(parts):
                if part in ["pig1987", "zonea0"]:
                    artist = part
                    break
        
        # Pattern 2: Overview_2024-06-17_1750084991_pig1987_20250618_074423.ndjson
        elif "Overview" in filename:
            parts = filename.split("_")
            for part in parts:
                if part in ["pig1987", "zonea0"]:
                    artist = part
                    break
        
        # Pattern 3: Other patterns - look for known artist names
        if not artist:
            parts = filename.split("_")
            for part in parts:
                if part.lower() in ["pig1987", "zonea0", "zone.a0"]:
                    artist = part.lower()
                    break
        
        # Normalize artist name
        if artist:
            if artist.lower() == "zonea0":
                artist = "zone.a0"
            elif artist.lower() == "pig1987":
                artist = "pig1987"
            
            mtime = file_path.stat().st_mtime
            
            if artist not in latest_per_artist or mtime > latest_per_artist[artist][1]:
                latest_per_artist[artist] = (file_path, mtime)
    
    return {artist: path for artist, (path, _) in latest_per_artist.items()}


def record_to_row(record: Dict) -> Dict:
    """Convert raw JSON record to staging row format."""
    return {
        "Artist": record.get("artist", ""),
        "Date": pd.to_datetime(record.get("date"), errors="coerce").date(),
        "Video Views": pd.to_numeric(record.get("video_views", 0), errors="coerce"),
        "Profile Views": pd.to_numeric(record.get("profile_views", 0), errors="coerce"),
        "Likes": pd.to_numeric(record.get("likes", 0), errors="coerce"),
        "Comments": pd.to_numeric(record.get("comments", 0), errors="coerce"),
        "Shares": pd.to_numeric(record.get("shares", 0), errors="coerce"),
        "Year": pd.to_numeric(record.get("year"), errors="coerce"),
        "Followers": pd.to_numeric(record.get("followers", 0), errors="coerce")  # NEW: Current follower count
    }


def load_raw_data(files: Dict[str, Path]) -> pd.DataFrame:
    """Load and process NDJSON files into DataFrame."""
    all_rows = []
    
    for artist, file_path in files.items():
        print(f"[STAGING] Loading {artist}: {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        record = json.loads(line.strip())
                        row = record_to_row(record)
                        all_rows.append(row)
                    except json.JSONDecodeError as e:
                        print(f"[ERROR] {file_path.name}:{line_num}: Invalid JSON - {e}")
                        continue
                    except Exception as e:
                        print(f"[ERROR] {file_path.name}:{line_num}: Processing error - {e}")
                        continue
            
            print(f"[STAGING] Processed {artist}: {len([r for r in all_rows if r['Artist'] == artist])} records")
            
        except Exception as e:
            print(f"[ERROR] Failed to load {file_path.name}: {e}")
            continue
    
    if not all_rows:
        raise RuntimeError("No valid records loaded from raw files")
    
    df = pd.DataFrame(all_rows)
    
    # Ensure proper data types
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    numeric_cols = ["Video Views", "Profile Views", "Likes", "Comments", "Shares", "Year", "Followers"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    
    print(f"[STAGING] Total loaded: {len(df)} rows across {df['Artist'].nunique()} artists")
    return df


def load_existing_staging() -> pd.DataFrame:
    """Load existing staging CSV if it exists."""
    staging_file = STAGING_DIR / "tiktok.csv"
    
    if staging_file.exists():
        df = pd.read_csv(staging_file)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        print(f"[STAGING] Loaded existing staging: {len(df)} rows")
        return df
    else:
        print("[STAGING] No existing staging file found")
        return pd.DataFrame(columns=["Artist", "Date", "Video Views", "Profile Views", "Likes", "Comments", "Shares", "Year", "Followers"])

# %% Core Processing Logic

def process_raw_to_staging(output_path: Optional[Path] = None) -> int:
    """Process raw NDJSON files and create/update staging CSV."""
    # Load raw data
    raw_files = load_ndjson_files() 
    raw_df = load_raw_data(raw_files)
    
    # Load existing staging data
    staging_df = load_existing_staging()
    
    if staging_df.empty:
        # First run - use all raw data
        combined_df = raw_df.copy()
        print(f"[STAGING] First run: using all {len(combined_df)} raw records")
    else:
        # Incremental update - find new records per artist
        last_dates = staging_df.groupby("Artist")["Date"].max().to_dict()
        new_rows = []
        
        for artist, group in raw_df.groupby("Artist"):
            cutoff = last_dates.get(artist, pd.Timestamp.min)
            new_records = group[group["Date"] > cutoff]
            
            if not new_records.empty:
                print(f"[STAGING] {artist}: {len(new_records)} new records since {cutoff.date()}")
                new_rows.append(new_records)
            else:
                print(f"[STAGING] {artist}: no new records")
        
        if new_rows:
            new_df = pd.concat(new_rows, ignore_index=True)
            combined_df = pd.concat([staging_df, new_df], ignore_index=True)
            
            # Remove duplicates and sort
            combined_df = combined_df.drop_duplicates(subset=["Artist", "Date"], keep="last")
            combined_df = combined_df.sort_values(["Artist", "Date"]).reset_index(drop=True)
            
            print(f"[STAGING] Added {len(new_df)} new records → {len(combined_df)} total")
        else:
            combined_df = staging_df.copy()
            print("[STAGING] No new records to add")
    
    # Write staging file
    staging_file = output_path or (STAGING_DIR / "tiktok.csv")
    combined_df.to_csv(staging_file, index=False, encoding="utf-8")
    print(f"[STAGING] Written to: {staging_file}")
    
    return len(combined_df)

# %% CLI Entry Point

def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="TikTok Raw→Staging cleaner")
    parser.add_argument("--out", type=Path, help="Custom output CSV path")
    args = parser.parse_args()
    
    try:
        count = process_raw_to_staging(args.out)
        print(f"[STAGING] Completed: {count} records in staging")
    except Exception as e:
        print(f"[ERROR] Processing failed: {e}")
        raise


if __name__ == "__main__":
    main()