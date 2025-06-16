"""spotify_staging2curated.py
Aggregates Spotify audience stats from the staging zone (CSV files)
and writes a curated CSV suitable for analytics dashboards.

Guided by `LLM_cleaner_guidelines.md`.

Zones:
    staging/spotify/audience -> curated/spotify/audience

Behaviours:
* Reads all CSVs in STAGING_DIR unless `--input` provided.
* Deduplicates on (`artist_id`, `date`).
* Casts column dtypes and sorts by date.
* Outputs a single CSV named
  `spotify_audience_curated_<timestamp>.csv` in CURATED_DIR.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd

# %% Imports & Constants -----------------------------------------------------
PROJECT_ROOT = Path(os.environ["PROJECT_ROOT"])

STAGING_DIR = PROJECT_ROOT / "staging" / "spotify" / "audience"
CURATED_DIR = PROJECT_ROOT / "curated" / "spotify" / "audience"
STAGING_DIR.mkdir(parents=True, exist_ok=True)
CURATED_DIR.mkdir(parents=True, exist_ok=True)

KEY_COLS = ["artist_id", "date"]

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


def curate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply business rules and return curated dataframe."""
    # Ensure columns exist
    for col in KEY_COLS:
        if col not in df.columns:
            raise RuntimeError(f"Required column '{col}' missing from staging input.")

    # Cast
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Numeric columns – attempt coercion
    for col in df.select_dtypes(include="object").columns:
        if col not in KEY_COLS:
            df[col] = pd.to_numeric(df[col], errors="ignore")

    # Deduplicate
    df = df.drop_duplicates(subset=KEY_COLS, keep="last")

    # Sort
    df = df.sort_values(["artist_id", "date"]).reset_index(drop=True)

    return df

# %% Core processing ---------------------------------------------------------

def run(input_paths: List[Path] | None = None) -> Path:
    if input_paths is None:
        input_paths = sorted(STAGING_DIR.glob("*.csv"))
    if not input_paths:
        raise RuntimeError("[STAGING] No CSV files found to process.")

    staging_df = _load_staging_files(input_paths)
    curated_df = curate_dataframe(staging_df)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = CURATED_DIR / f"spotify_audience_curated_{timestamp}.csv"
    curated_df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"[CURATED] Saved curated CSV to {out_path.relative_to(PROJECT_ROOT)}")
    return out_path

# %% CLI ---------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Spotify staging → curated cleaner")
    parser.add_argument("--input", nargs="*", type=str, help="Specific staging CSV paths to process")
    args = parser.parse_args()

    input_paths = [Path(p) for p in args.input] if args.input else None
    try:
        run(input_paths)
    except Exception as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
