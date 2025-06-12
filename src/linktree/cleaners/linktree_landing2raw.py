"""
linktree_landing2raw.py
Landing → Raw cleaner for Linktree data.

Guided by `LLM_cleaner_guidelines.md`.
"""

import os, json, argparse
from datetime import datetime
from pathlib import Path

PLATFORM = "linktree"
PROJECT_ROOT = Path(os.environ["PROJECT_ROOT"])

LANDING_DIR = PROJECT_ROOT / "landing" / PLATFORM
RAW_DIR     = PROJECT_ROOT / "raw"      / PLATFORM

for _dir in (LANDING_DIR, RAW_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

def transform_response(payload: dict) -> list[dict]:
    """Flatten GraphQL `getAccountAnalytics` → `overview` → `timeseries`."""
    try:
        ts_rows = (
            payload["data"]
                   ["getAccountAnalytics"]
                   ["overview"]
                   ["timeseries"]
        )
    except (KeyError, TypeError):
        print("[ERROR] Unexpected GraphQL structure.")
        return []

    return [{
        "date":              r.get("date"),
        "totalViews":        r.get("totalViews"),
        "uniqueViews":       r.get("uniqueViews"),
        "totalClicks":       r.get("totalClicks"),
        "uniqueClicks":      r.get("uniqueClicks"),
        "clickThroughRate":  r.get("clickThroughRate"),
        "__typename":        r.get("__typename")
    } for r in ts_rows]

def process_file(in_path: Path) -> int:
    out_path = RAW_DIR / f"{in_path.stem}.ndjson"
    written  = 0
    try:
        with in_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        rows = transform_response(payload)
        if not rows:
            return 0
        with out_path.open("w", encoding="utf-8") as out_f:
            for row in rows:
                json.dump(row, out_f, ensure_ascii=False)
                out_f.write("\n")
                written += 1
        print(f"[RAW]  {in_path.name} → {out_path.name} ({written} rows)")
        return written
    except Exception as e:
        print(f"[ERROR] {in_path.name}: {e}")
        return 0

def main():
    parser = argparse.ArgumentParser(description="Linktree Landing→Raw cleaner")
    parser.add_argument(
        "--file", help="Process a single landing JSON file", default=None
    )
    args = parser.parse_args()

    files = (
        [Path(args.file)]
        if args.file else
        sorted(LANDING_DIR.glob("*.json"))
    )

    total_rows = 0
    for fp in files:
        total_rows += process_file(fp)

    if total_rows == 0:
        raise RuntimeError("No records processed; aborting.")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[INFO] Completed run at {timestamp} – {total_rows} rows total.")

if __name__ == "__main__":
    main()
