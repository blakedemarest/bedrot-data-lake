"""
/// linktree_staging2curated.py
/// Staging → Curated cleaner for Linktree analytics.
///
/// Guided by `LLM_cleaner_guidelines.md`.
/// Reads **CSV** from staging, writes **CSV and Parquet** to curated.
"""

import os, argparse
from shutil import move
from datetime import datetime
from pathlib import Path
import pandas as pd

PLATFORM      = "linktree"
PROJECT_ROOT  = Path(os.environ["PROJECT_ROOT"])

# Use environment variables for zone names
STAGING_ZONE = os.environ.get("STAGING_ZONE", "staging")
CURATED_ZONE = os.environ.get("CURATED_ZONE", "curated")
ARCHIVE_ZONE = os.environ.get("ARCHIVE_ZONE", "archive")

STAGING_DIR   = PROJECT_ROOT / STAGING_ZONE / PLATFORM
CURATED_DIR   = PROJECT_ROOT / CURATED_ZONE

for _d in (STAGING_DIR, CURATED_DIR):
    _d.mkdir(parents=True, exist_ok=True)

def curate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if "__typename" in df.columns:
        df = df.drop(columns="__typename")

    # Re-calculate CTR if missing / NaN
    # Convert inf values to NaN manually instead of using deprecated option
    ctr = df["totalClicks"] / df["totalViews"].replace({0: pd.NA})
    ctr = ctr.replace([float('inf'), float('-inf')], pd.NA)
    df["clickThroughRate"] = df["clickThroughRate"].fillna(ctr)
    df["clickThroughRate"] = df["clickThroughRate"].round(4)

    # Keep last record per date
    df = (
        df.sort_values("date")
          .drop_duplicates(subset=["date"], keep="last")
          .reset_index(drop=True)
    )
    return df

def load_staging(files: list[Path]) -> pd.DataFrame:
    frames = []
    for fp in files:
        try:
            frames.append(pd.read_csv(fp, parse_dates=["date"]))
        except Exception as e:
            print(f"[ERROR] {fp.name}: {e}")
    if not frames:
        raise RuntimeError("No staging CSV files read")
    return pd.concat(frames, ignore_index=True)

def main():
    parser = argparse.ArgumentParser(description="Linktree Staging→Curated cleaner")
    parser.add_argument("--input", help="Specific staging CSV file", default=None)
    args = parser.parse_args()

    files = [Path(args.input)] if args.input else sorted(STAGING_DIR.glob("*.csv"))
    if not files:
        raise RuntimeError(f"No staging CSV files found in {STAGING_DIR}")

    df_raw = load_staging(files)
    df_cur = curate_dataframe(df_raw)

    # Archive existing file if it exists
    ARCHIVE_DIR = PROJECT_ROOT / ARCHIVE_ZONE / PLATFORM
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    
    existing_file = CURATED_DIR / "linktree_analytics.csv"
    if existing_file.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"linktree_analytics_archived_{ts}.csv"
        move(str(existing_file), ARCHIVE_DIR / archive_name)
        print(f"[ARCHIVE] Moved existing file to {ARCHIVE_DIR.relative_to(PROJECT_ROOT)}/{archive_name}")

    # Write new CSV with fixed name
    csv_path = CURATED_DIR / "linktree_analytics.csv"
    df_cur.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"[CURATED] CSV → {csv_path.name}  ({len(df_cur)} rows)")

if __name__ == "__main__":
    main()
