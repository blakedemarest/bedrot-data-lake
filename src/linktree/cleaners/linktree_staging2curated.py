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
STAGING_DIR   = PROJECT_ROOT / "staging" / PLATFORM
CURATED_DIR   = PROJECT_ROOT / "curated" / PLATFORM

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

    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = f"linktree_analytics_curated_{ts}"

    # CSV
    csv_path = CURATED_DIR / f"{stem}.csv"
    df_cur.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"[CURATED] CSV → {csv_path.name}  ({len(df_cur)} rows)")

    # Parquet (optional)
    pq_path = CURATED_DIR / f"{stem}.parquet"
    try:
        pq_path = CURATED_DIR / f"{stem}.parquet"
        df_cur.to_parquet(pq_path, index=False)
        print(f"[CURATED] Parquet → {pq_path.name}")
    except Exception as e:
        print(f"[ERROR] Parquet write failed: {e} (CSV still produced)")

    # ---- Deduplication & Archiving ----
    ARCHIVE_DIR = PROJECT_ROOT / "archive" / PLATFORM
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    # Move older CSV files
    for f in CURATED_DIR.glob("linktree_analytics_curated_*.csv"):
        if f.name != csv_path.name:
            move(str(f), ARCHIVE_DIR / f.name)

    # Move older Parquet files
    for f in CURATED_DIR.glob("linktree_analytics_curated_*.parquet"):
        if pq_path.exists() and f.name != pq_path.name:
            move(str(f), ARCHIVE_DIR / f.name)

    print(f"[CLEANUP] Archived older curated files → {ARCHIVE_DIR.relative_to(PROJECT_ROOT)}")

if __name__ == "__main__":
    main()
