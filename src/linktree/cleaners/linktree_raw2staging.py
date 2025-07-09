"""
/// linktree_raw2staging.py
/// Raw → Staging cleaner for Linktree NDJSON data.
///
/// Guided by `LLM_cleaner_guidelines.md`.
/// • Reads every *.ndjson in raw/linktree/
/// • Cleans & deduplicates rows
/// • Writes a single UTF-8 CSV file to staging/linktree/
///
/// Run:
///     python src/linktree/cleaners/linktree_raw2staging.py
///     python src/linktree/cleaners/linktree_raw2staging.py --out /custom/path/file.csv
"""

import os
import json
import argparse
from datetime import datetime
from pathlib import Path
import pandas as pd

PLATFORM = "linktree"
PROJECT_ROOT = Path(os.environ["PROJECT_ROOT"])

# Use environment variables for zone names
RAW_ZONE = os.environ.get("RAW_ZONE", "raw")
STAGING_ZONE = os.environ.get("STAGING_ZONE", "staging")

RAW_DIR = PROJECT_ROOT / RAW_ZONE / PLATFORM / "analytics"  # ← must match landing2raw output
STAGING_DIR = PROJECT_ROOT / STAGING_ZONE / PLATFORM

for _d in (RAW_DIR, STAGING_DIR):
    _d.mkdir(parents=True, exist_ok=True)

METRIC_COLS = [
    "totalViews",
    "uniqueViews",
    "totalClicks",
    "uniqueClicks",
    "clickThroughRate",
]


def record_to_row(rec: dict) -> dict | None:
    """
    /// Validate & convert a single JSON record.
    /// Returns a dict or None (when 'date' is missing).
    """
    if "date" not in rec:
        return None
    row = {"date": pd.to_datetime(rec["date"], errors="coerce")}
    for col in METRIC_COLS:
        row[col] = pd.to_numeric(rec.get(col), errors="coerce")
    return row


def extract_timeseries_rows(obj: dict) -> list[dict]:
    """Given a JSON object from NDJSON, return a list of flattened rows.

    /// Scenarios handled:
    /// 1. Object **already** represents a flattened row (has top-level
    ///    "date"). Return [obj].
    /// 2. Object is a full GraphQL payload with structure
    ///    data→getAccountAnalytics→overview→timeseries. Return list of
    ///    flattened dicts extracted from the timeseries array.
    /// 3. Any other structure → returns empty list.
    """
    # Case 1 – already flattened
    if "date" in obj:
        return [obj]

    # Case 2 – nested payload
    try:
        ts_rows = (
            obj["data"]["getAccountAnalytics"]["overview"]["timeseries"]
        )
    except (KeyError, TypeError):
        return []

    return [
        {
            "date": r.get("date"),
            "totalViews": r.get("totalViews"),
            "uniqueViews": r.get("uniqueViews"),
            "totalClicks": r.get("totalClicks"),
            "uniqueClicks": r.get("uniqueClicks"),
            "clickThroughRate": r.get("clickThroughRate"),
        }
        for r in ts_rows
    ]


def build_dataframe(files: list[Path]) -> pd.DataFrame:
    rows: list[dict] = []
    for fp in files:
        try:
            with fp.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    for row in extract_timeseries_rows(obj):
                        rows.append(record_to_row(row))
        except Exception as e:
            print(f"[ERROR] {fp.name}: {e}")

    rows = [r for r in rows if r]  # drop Nones

    if not rows:
        raise RuntimeError("No valid rows extracted from raw NDJSON files")

    df = pd.DataFrame(rows)
    df = df.dropna(subset=["date"])  # ensure date is present
    df = df.sort_values("date").drop_duplicates()
    df.reset_index(drop=True, inplace=True)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Linktree Raw→Staging cleaner (CSV)")
    parser.add_argument("--out", help="Custom CSV output path", default=None)
    args = parser.parse_args()

    files = sorted(RAW_DIR.glob("*.ndjson"))
    if not files:
        raise RuntimeError(f"No NDJSON files found in {RAW_DIR}")

    df = build_dataframe(files)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path(args.out) if args.out else (
        STAGING_DIR / f"linktree_analytics_staging_{ts}.csv"
    )
    df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"[STAGING] Written → {out_path.name}  ({len(df)} rows)")


if __name__ == "__main__":
    main()
