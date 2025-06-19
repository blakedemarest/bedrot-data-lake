"""spotify_landing2staging.py
Moves Spotify audience CSV files from landing to staging directory.

Zones:
    landing/spotify/audience -> staging/spotify/audience

Behaviors:
* Reads all CSV files from landing/spotify/audience/
* Copies them to staging/spotify/audience/ with standardized naming
* Adds metadata columns for processing tracking
"""
import os
import shutil
from datetime import datetime
from pathlib import Path
import pandas as pd

# Constants
PROJECT_ROOT = Path(os.environ["PROJECT_ROOT"])
LANDING_DIR = PROJECT_ROOT / "landing" / "spotify" / "audience"
STAGING_DIR = PROJECT_ROOT / "staging" / "spotify" / "audience"

LANDING_DIR.mkdir(parents=True, exist_ok=True)
STAGING_DIR.mkdir(parents=True, exist_ok=True)

def process_csv_file(csv_path: Path) -> int:
    """Process a single CSV file from landing to staging."""
    try:
        # Read the CSV
        df = pd.read_csv(csv_path)
        
        # Extract artist_id from filename (format: spotify_audience_<artist_id>_<timestamp>.csv)
        filename_parts = csv_path.stem.split('_')
        if len(filename_parts) >= 3:
            artist_id = filename_parts[2]
        else:
            print(f"[WARN] Could not extract artist_id from {csv_path.name}, using 'unknown'")
            artist_id = 'unknown'
        
        # Add metadata columns
        df['artist_id'] = artist_id
        df['processed_at'] = datetime.now().isoformat()
        df['source_file'] = csv_path.name
        
        # Create output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"spotify_audience_{artist_id}_{timestamp}.csv"
        output_path = STAGING_DIR / output_name
        
        # Save to staging
        df.to_csv(output_path, index=False)
        print(f"[STAGING] {csv_path.name} -> {output_name} ({len(df)} rows)")
        
        return len(df)
    except Exception as e:
        print(f"[ERROR] Failed to process {csv_path.name}: {e}")
        return 0

def main():
    """Main processing function."""
    print("[INFO] Starting Spotify landing -> staging processing...")
    
    # Find all CSV files in landing
    csv_files = list(LANDING_DIR.glob("*.csv"))
    
    if not csv_files:
        print("[ERROR] [STAGING] No CSV files found to process.")
        return
    
    total_rows = 0
    processed_files = 0
    
    for csv_file in csv_files:
        rows = process_csv_file(csv_file)
        if rows > 0:
            total_rows += rows
            processed_files += 1
    
    print(f"[STAGING] Processed {processed_files} files with {total_rows} total rows")

if __name__ == "__main__":
    main()