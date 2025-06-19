"""
Spotify Raw→Staging cleaner for audience analytics data.

Processes NDJSON files from raw zone, validates data, and creates CSV format
suitable for staging analysis. Handles multiple artists and ensures proper
data types and validation.

Guided by LLM_cleaner_guidelines.md

Zones:
    raw/spotify/audience → staging/spotify/audience
"""

# %% Imports & Constants
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

PLATFORM = "spotify"
PROJECT_ROOT = Path(os.environ["PROJECT_ROOT"])
RAW_DIR = PROJECT_ROOT / "raw" / PLATFORM / "audience"
STAGING_DIR = PROJECT_ROOT / "staging" / PLATFORM / "audience"

# Ensure directories exist
STAGING_DIR.mkdir(parents=True, exist_ok=True)

# %% Helper functions

def record_to_row(record: Dict) -> Dict:
    """Convert a raw NDJSON record to a staging row."""
    return {
        "date": record.get("date"),
        "listeners": record.get("listeners", 0),
        "streams": record.get("streams", 0),
        "followers": record.get("followers", 0),
        "artist_id": record.get("artist_id", "unknown"),
        "artist_name": record.get("artist_name", "unknown"),
        "extracted_at": record.get("extracted_at"),
        "source_file": record.get("source_file"),
        "data_source": record.get("data_source", "spotify_audience"),
        "processed_at": datetime.now().isoformat()
    }

def validate_and_clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and clean the staging dataframe."""
    print(f"[STAGING] Input records: {len(df)}")
    
    # Ensure required columns exist
    required_cols = ["date", "listeners", "streams", "followers", "artist_name"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise RuntimeError(f"Missing required columns: {missing_cols}")
    
    # Clean and validate date column
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    initial_count = len(df)
    df = df.dropna(subset=["date"])
    date_dropped = initial_count - len(df)
    if date_dropped > 0:
        print(f"[STAGING] Dropped {date_dropped} records with invalid dates")
    
    # Convert numeric columns
    numeric_cols = ["listeners", "streams", "followers"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    
    # Validate artist information
    df["artist_name"] = df["artist_name"].fillna("unknown")
    df["artist_id"] = df["artist_id"].fillna("unknown")
    
    # Sort by artist and date
    df = df.sort_values(["artist_name", "date"]).reset_index(drop=True)
    
    print(f"[STAGING] Output records: {len(df)}")
    return df

def process_ndjson_file(ndjson_path: Path) -> List[Dict]:
    """Process a single NDJSON file and return list of records."""
    records = []
    try:
        print(f"[STAGING] Reading {ndjson_path.relative_to(PROJECT_ROOT)}")
        
        with open(ndjson_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    record = json.loads(line)
                    row = record_to_row(record)
                    records.append(row)
                except json.JSONDecodeError as e:
                    print(f"[ERROR] Invalid JSON on line {line_num} in {ndjson_path.name}: {e}")
                except Exception as e:
                    print(f"[ERROR] Failed to process line {line_num} in {ndjson_path.name}: {e}")
        
        print(f"[STAGING] Loaded {len(records)} records from {ndjson_path.name}")
        return records
        
    except Exception as e:
        print(f"[ERROR] Failed to read {ndjson_path.name}: {e}")
        return []

# %% Core processing

def run(output_path: Optional[Path] = None) -> Path:
    """Main processing function."""
    print("[INFO] Starting Spotify raw → staging processing...")
    
    # Find all NDJSON files in raw directory
    ndjson_files = list(RAW_DIR.glob("*.ndjson"))
    
    if not ndjson_files:
        print("[ERROR] No NDJSON files found in raw directory")
        raise RuntimeError("No NDJSON files found to process")
    
    # Process all NDJSON files
    all_records = []
    for ndjson_file in ndjson_files:
        records = process_ndjson_file(ndjson_file)
        all_records.extend(records)
    
    if not all_records:
        raise RuntimeError("No valid records were processed")
    
    # Convert to DataFrame and validate
    df = pd.DataFrame(all_records)
    df = validate_and_clean_dataframe(df)
    
    # Create output filename
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = STAGING_DIR / f"spotify_audience_staging_{timestamp}.csv"
    
    # Write to CSV
    df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"[STAGING] Saved staging CSV to {output_path.relative_to(PROJECT_ROOT)}")
    
    # Print summary by artist
    artist_summary = df.groupby('artist_name').agg({
        'date': ['min', 'max', 'count'],
        'streams': 'sum',
        'listeners': 'max'
    }).round(0)
    
    print(f"[STAGING] Artist summary:")
    for artist in df['artist_name'].unique():
        artist_data = df[df['artist_name'] == artist]
        date_range = f"{artist_data['date'].min().date()} to {artist_data['date'].max().date()}"
        print(f"[STAGING]   {artist}: {len(artist_data)} records ({date_range})")
    
    return output_path

# %% CLI

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Spotify raw → staging cleaner")
    parser.add_argument("--out", type=str, help="Custom output CSV path")
    args = parser.parse_args()
    
    output_path = Path(args.out) if args.out else None
    
    try:
        run(output_path)
    except Exception as e:
        print(f"[ERROR] {e}")
        exit(1)

if __name__ == "__main__":
    main()