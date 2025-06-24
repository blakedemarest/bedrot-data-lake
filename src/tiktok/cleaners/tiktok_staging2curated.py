"""
TikTok Staging→Curated cleaner for analytics data.

Reads staging CSV, applies business rules and aggregation,
and outputs timestamped CSV to curated zone.

Guided by LLM_cleaner_guidelines.md
"""

# %% Imports & Constants
import argparse
import os
from shutil import move
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd

PLATFORM = "tiktok"
PROJECT_ROOT = Path(os.environ["PROJECT_ROOT"])
STAGING_DIR = PROJECT_ROOT / "staging"
CURATED_DIR = PROJECT_ROOT / "curated" / PLATFORM

# Ensure directories exist
CURATED_DIR.mkdir(parents=True, exist_ok=True)

print(f"[INFO] PROJECT_ROOT: {PROJECT_ROOT}")
print(f"[INFO] STAGING_DIR: {STAGING_DIR}")
print(f"[INFO] CURATED_DIR: {CURATED_DIR}")

# %% Helper Functions

def load_staging_data(input_file: Optional[Path] = None) -> pd.DataFrame:
    """Load staging CSV data."""
    if input_file:
        staging_file = input_file
    else:
        staging_file = STAGING_DIR / "tiktok.csv"
    
    if not staging_file.exists():
        raise FileNotFoundError(f"Staging file not found: {staging_file}")
    
    df = pd.read_csv(staging_file)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    
    print(f"[CURATED] Loaded staging: {len(df)} rows from {staging_file.name}")
    return df


def calculate_new_followers(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate new_followers column based on daily follower changes."""
    df = df.copy()
    df["new_followers"] = 0  # Initialize
    
    # Calculate new followers per artist
    for artist in df["artist"].unique():
        artist_mask = df["artist"] == artist
        artist_data = df[artist_mask].sort_values("date")
        
        if len(artist_data) > 1 and "Followers" in artist_data.columns:
            # Calculate difference between consecutive days
            follower_diff = artist_data["Followers"].diff()
            # Only count positive changes as new followers
            new_followers = follower_diff.where(follower_diff > 0, 0)
            df.loc[artist_mask, "new_followers"] = new_followers.values
    
    return df


def curate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply business rules and prepare curated dataset."""
    # Rename columns to standard format
    df = df.rename(columns={
        "Artist": "artist",
        "Date": "date"
    })
    
    # Add zone column (extract from artist name for compatibility)
    df["zone"] = df["artist"]
    
    # Convert date to date type
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    
    # Ensure required columns exist
    required = {"artist", "zone", "date"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    
    # Define grouping keys and metric columns
    group_keys = ["artist", "zone", "date"]
    metric_cols = ["Video Views", "Profile Views", "Likes", "Comments", "Shares"]
    follower_cols = ["Followers"]  # Handle followers separately
    other_cols = [c for c in df.columns if c not in group_keys + metric_cols + follower_cols]
    
    # Build aggregation dictionary
    agg_dict = {}
    
    # Sum engagement metrics
    for col in metric_cols:
        if col in df.columns:
            agg_dict[col] = "sum"
    
    # Use last value for follower count
    for col in follower_cols:
        if col in df.columns:
            agg_dict[col] = "last"
    
    # Use last value for other columns
    for col in other_cols:
        if col in df.columns:
            agg_dict[col] = "last"
    
    # Group and aggregate
    df_curated = (
        df.sort_values("date")
          .groupby(group_keys, as_index=False)
          .agg(agg_dict)
          .reset_index(drop=True)
    )
    
    # Calculate new_followers based on daily changes
    df_curated = calculate_new_followers(df_curated)
    
    # Calculate engagement rate
    df_curated["engagement_rate"] = (
        (df_curated.get("Likes", 0) + df_curated.get("Comments", 0) + df_curated.get("Shares", 0)) / 
        df_curated.get("Video Views", 1).replace(0, 1)
    ).round(4)
    
    # Ensure column order matches existing schema + new columns
    desired_order = [
        "artist", "zone", "date", "Video Views", "Profile Views", 
        "Likes", "Comments", "Shares", "Year", "engagement_rate",
        "Followers", "new_followers"  # NEW: Add these two columns
    ]
    
    # Reorder columns, keeping any extras at the end
    available_cols = [col for col in desired_order if col in df_curated.columns]
    extra_cols = [col for col in df_curated.columns if col not in desired_order]
    final_columns = available_cols + extra_cols
    
    df_curated = df_curated[final_columns]
    
    # Sort final output
    df_curated = df_curated.sort_values(["artist", "date"]).reset_index(drop=True)
    
    print(f"[CURATED] Aggregated to {len(df_curated)} rows with followers tracking")
    return df_curated

# %% Core Processing Logic

def process_staging_to_curated(input_file: Optional[Path] = None) -> int:
    """Process staging data and create curated output."""
    # Load staging data
    staging_df = load_staging_data(input_file)
    
    # Apply curation logic
    curated_df = curate_dataframe(staging_df)
    
    # Generate timestamped output filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_name = f"tiktok_analytics_curated_{timestamp}.csv"
    output_path = CURATED_DIR / output_name
    
    # Write curated CSV
    curated_df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"[CURATED] Written: {output_name} ({len(curated_df)} rows)")

    # ---- Deduplication & Archiving ----
    ARCHIVE_DIR = PROJECT_ROOT / "archive" / PLATFORM
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    for f in CURATED_DIR.glob("tiktok_analytics_curated_*.csv"):
        if f.name != output_name:
            move(str(f), ARCHIVE_DIR / f.name)
    print(f"[CLEANUP] Archived older curated files → {ARCHIVE_DIR.relative_to(PROJECT_ROOT)}")

    return len(curated_df)

# %% CLI Entry Point

def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="TikTok Staging→Curated cleaner")
    parser.add_argument("--input", type=Path, help="Specific staging file")
    args = parser.parse_args()
    
    try:
        count = process_staging_to_curated(args.input)
        print(f"[CURATED] Completed: {count} curated records")
    except Exception as e:
        print(f"[ERROR] Processing failed: {e}")
        raise


if __name__ == "__main__":
    main()
