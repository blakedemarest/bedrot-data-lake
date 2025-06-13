"""
TikTok Staging→Curated cleaner for analytics data.

Reads staging CSV, applies business rules and aggregation,
and outputs timestamped CSV to curated zone.

Guided by LLM_cleaner_guidelines.md
"""

# %% Imports & Constants
import argparse
import os
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
    other_cols = [c for c in df.columns if c not in group_keys + metric_cols]
    
    # Build aggregation dictionary
    agg_dict = {}
    for col in metric_cols:
        if col in df.columns:
            agg_dict[col] = "sum"
    
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
    
    # Calculate derived metrics
    df_curated["engagement_rate"] = (
        (df_curated.get("Likes", 0) + df_curated.get("Comments", 0) + df_curated.get("Shares", 0)) / 
        df_curated.get("Video Views", 1).replace(0, 1)
    ).round(4)
    
    # Sort final output
    df_curated = df_curated.sort_values(["artist", "date"]).reset_index(drop=True)
    
    print(f"[CURATED] Aggregated to {len(df_curated)} rows")
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
