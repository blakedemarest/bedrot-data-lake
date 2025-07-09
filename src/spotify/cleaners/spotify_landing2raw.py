"""
Spotify Landing→Raw cleaner for audience analytics data.

Processes CSV files from Spotify audience extractor.
Validates, transforms, and converts CSV data to NDJSON format in raw zone.
Handles multiple artist IDs and maps them to friendly names.

Guided by LLM_cleaner_guidelines.md

Zones:
    landing/spotify/audience → raw/spotify/audience
"""

# %% Imports & Constants
import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

PLATFORM = "spotify"
PROJECT_ROOT = Path(os.environ["PROJECT_ROOT"])
LANDING_DIR = PROJECT_ROOT / "landing" / PLATFORM / "audience"
RAW_DIR = PROJECT_ROOT / "raw" / PLATFORM / "audience"

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Artist ID mappings
ARTIST_MAPPINGS = {
    "62owJQCD2XzVB2o19CVsFM": "zone_a0",
    "1Eu67EqPy2NutiM0lqCarw": "pig1987",
    "20250616": "zone_a0",  # Handle malformed IDs from filename parsing
}

# %% Helper functions

def extract_artist_info(filename: str) -> tuple[str, str]:
    """Extract artist ID and friendly name from filename."""
    # Try to extract artist ID from filename patterns:
    # spotify_audience_<artist_id>_<timestamp>.csv
    # spotify_audience_<timestamp>.csv (generic)
    
    parts = filename.replace('.csv', '').split('_')
    
    if len(parts) >= 3:
        # Has artist ID in filename
        artist_id = parts[2]
        if artist_id in ARTIST_MAPPINGS:
            return artist_id, ARTIST_MAPPINGS[artist_id]
        else:
            # Unknown artist ID, use as-is
            return artist_id, f"artist_{artist_id}"
    else:
        # Generic filename, assume zone_a0 for backward compatibility
        return "unknown", "zone_a0"

def transform_csv_record(row: Dict, artist_id: str, artist_name: str, source_file: str) -> Dict:
    """Transform a single CSV row into a raw record."""
    return {
        "date": row.get("date"),
        "listeners": int(row.get("listeners", 0)) if pd.notna(row.get("listeners")) else 0,
        "streams": int(row.get("streams", 0)) if pd.notna(row.get("streams")) else 0,
        "followers": int(row.get("followers", 0)) if pd.notna(row.get("followers")) else 0,
        "artist_id": artist_id,
        "artist_name": artist_name,
        "extracted_at": datetime.now().isoformat(),
        "source_file": source_file,
        "data_source": "spotify_audience"
    }

def process_csv_file(csv_path: Path) -> int:
    """Process a single CSV file from landing to raw."""
    try:
        print(f"[RAW] Processing {csv_path.relative_to(PROJECT_ROOT)}")
        
        # Extract artist info from filename
        artist_id, artist_name = extract_artist_info(csv_path.name)
        
        # Read CSV file
        df = pd.read_csv(csv_path)
        
        # Validate required columns
        required_cols = ["date", "listeners", "streams", "followers"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"[ERROR] Missing columns in {csv_path.name}: {missing_cols}")
            return 0
        
        # Create output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"spotify_audience_{artist_name}_{timestamp}.ndjson"
        output_path = RAW_DIR / output_name
        
        # Transform and write records
        record_count = 0
        with open(output_path, 'w', encoding='utf-8') as f:
            for _, row in df.iterrows():
                # Skip rows with invalid dates
                if pd.isna(row.get("date")) or row.get("date") == "":
                    continue
                    
                record = transform_csv_record(
                    row.to_dict(), 
                    artist_id, 
                    artist_name, 
                    csv_path.name
                )
                f.write(json.dumps(record) + '\n')
                record_count += 1
        
        print(f"[RAW] {csv_path.name} → {output_name} ({record_count} records)")
        return record_count
        
    except Exception as e:
        print(f"[ERROR] Failed to process {csv_path.name}: {e}")
        return 0

# %% Core processing

def run(file_path: Optional[Path] = None) -> int:
    """Main processing function."""
    print("[INFO] Starting Spotify landing → raw processing...")
    
    if file_path:
        csv_files = [file_path] if file_path.exists() else []
    else:
        csv_files = list(LANDING_DIR.glob("*.csv"))
    
    if not csv_files:
        print("[ERROR] No CSV files found to process.")
        return 0
    
    total_records = 0
    processed_files = 0
    
    for csv_file in csv_files:
        records = process_csv_file(csv_file)
        if records > 0:
            total_records += records
            processed_files += 1
    
    if total_records == 0:
        raise RuntimeError("No records were processed successfully")
    
    print(f"[RAW] Processed {processed_files} files with {total_records} total records")
    return total_records

# %% CLI

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Spotify landing → raw cleaner")
    parser.add_argument("--file", type=str, help="Specific CSV file to process")
    args = parser.parse_args()
    
    file_path = Path(args.file) if args.file else None
    
    try:
        run(file_path)
    except Exception as e:
        print(f"[ERROR] {e}")
        exit(1)

if __name__ == "__main__":
    main()