"""spotify_staging2curated.py
Aggregates Spotify audience stats from the staging zone (CSV files)
and writes a curated CSV suitable for analytics dashboards.

Enhanced for multi-artist monitoring (zone_a0, pig1987) with archive functionality.

Guided by `LLM_cleaner_guidelines.md`.

Zones:
    staging/spotify/audience -> curated/spotify/audience

Behaviours:
* Reads all CSVs in STAGING_DIR unless `--input` provided.
* Combines data from both tracked artists (zone_a0, pig1987).
* Deduplicates on (`artist_name`, `date`) keeping most recent data.
* Archives previous curated CSV before writing new version.
* Outputs a single CSV named `spotify_audience_curated_<timestamp>.csv`.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd

# %% Imports & Constants -----------------------------------------------------
PROJECT_ROOT = Path(os.environ["PROJECT_ROOT"])

STAGING_DIR = PROJECT_ROOT / "staging" / "spotify" / "audience"
CURATED_DIR = PROJECT_ROOT / "curated"
ARCHIVE_DIR = PROJECT_ROOT / "archive" / "spotify" / "audience"

# Ensure all directories exist
for dir_path in [STAGING_DIR, CURATED_DIR, ARCHIVE_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Updated deduplication keys to use artist_name instead of artist_id
KEY_COLS = ["artist_name", "date"]

# Tracked artists
TRACKED_ARTISTS = {"zone_a0", "pig1987"}

# %% Helper functions --------------------------------------------------------

def _load_staging_files(paths: List[Path]) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for p in paths:
        try:
            print(f"[STAGING] Reading {p.relative_to(PROJECT_ROOT)} …")
            df = pd.read_csv(p)
            frames.append(df)
        except Exception as exc:
            print(f"[ERROR] Failed to read {p.name}: {exc}")
    if not frames:
        raise RuntimeError("No staging CSVs loaded – aborting.")
    return pd.concat(frames, ignore_index=True)


def archive_existing_curated() -> None:
    """Archive any existing curated CSV files before creating new one."""
    existing_files = list(CURATED_DIR.glob("spotify_audience_curated_*.csv"))
    
    if existing_files:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for file_path in existing_files:
            archive_name = f"{file_path.stem}_archived_{timestamp}.csv"
            archive_path = ARCHIVE_DIR / archive_name
            shutil.move(str(file_path), str(archive_path))
            print(f"[CURATED] Archived {file_path.name} → {archive_name}")

def curate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply business rules and return curated dataframe."""
    print(f"[CURATED] Input records: {len(df)}")
    
    # Ensure required columns exist
    required_cols = ["artist_name", "date", "listeners", "streams", "followers"]
    for col in required_cols:
        if col not in df.columns:
            raise RuntimeError(f"Required column '{col}' missing from staging input.")

    # Validate and filter for tracked artists only
    if "artist_name" in df.columns:
        tracked_data = df[df["artist_name"].isin(TRACKED_ARTISTS)]
        dropped_count = len(df) - len(tracked_data)
        if dropped_count > 0:
            print(f"[CURATED] Dropped {dropped_count} records from non-tracked artists")
        df = tracked_data

    # Cast date column
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    
    # Remove rows with invalid dates
    valid_dates = df["date"].notna()
    df = df[valid_dates]
    
    # Cast numeric columns
    numeric_cols = ["listeners", "streams", "followers"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Deduplicate on artist_name and date, keeping the most recent record
    # Sort by processed_at if available, otherwise by order in dataframe
    if "processed_at" in df.columns:
        df = df.sort_values("processed_at")
    
    df = df.drop_duplicates(subset=KEY_COLS, keep="last")

    # Final sort by artist and date
    df = df.sort_values(["artist_name", "date"]).reset_index(drop=True)
    
    print(f"[CURATED] Output records: {len(df)}")
    
    # Print summary by artist
    for artist in TRACKED_ARTISTS:
        artist_data = df[df["artist_name"] == artist]
        if len(artist_data) > 0:
            date_range = f"{artist_data['date'].min().date()} to {artist_data['date'].max().date()}"
            total_streams = artist_data['streams'].sum()
            max_listeners = artist_data['listeners'].max()
            print(f"[CURATED]   {artist}: {len(artist_data)} records, {total_streams:,} total streams, {max_listeners:,} max listeners ({date_range})")
        else:
            print(f"[CURATED]   {artist}: No data found")

    return df

# %% Core processing ---------------------------------------------------------

def run(input_paths: List[Path] | None = None) -> Path:
    """Main processing function."""
    print("[INFO] Starting Spotify staging → curated processing...")
    
    if input_paths is None:
        input_paths = sorted(STAGING_DIR.glob("*.csv"))
    if not input_paths:
        print("[ERROR] No CSV files found to process in staging directory")
        print("[INFO] Make sure spotify_raw2staging.py has been run first")
        return None

    # Archive existing curated files
    archive_existing_curated()

    # Load and process staging data
    staging_df = _load_staging_files(input_paths)
    curated_df = curate_dataframe(staging_df)
    
    if len(curated_df) == 0:
        print("[ERROR] No valid records remaining after curation")
        return None

    # Create output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = CURATED_DIR / f"spotify_audience_curated_{timestamp}.csv"
    
    # Write final curated CSV
    curated_df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"[CURATED] Saved curated CSV to {out_path.relative_to(PROJECT_ROOT)}")
    
    # Validation summary
    total_records = len(curated_df)
    unique_dates = curated_df['date'].nunique()
    date_range = f"{curated_df['date'].min().date()} to {curated_df['date'].max().date()}"
    print(f"[CURATED] Final dataset: {total_records} records, {unique_dates} unique dates ({date_range})")
    
    return out_path

# %% CLI ---------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Spotify staging → curated cleaner")
    parser.add_argument("--input", nargs="*", type=str, help="Specific staging CSV paths to process")
    args = parser.parse_args()

    input_paths = [Path(p) for p in args.input] if args.input else None
    try:
        result = run(input_paths)
        if result is None:
            sys.exit(1)
    except Exception as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
