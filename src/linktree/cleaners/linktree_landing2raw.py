"""
/// linktree_landing2raw.py
/// Landing → Raw cleaner for Linktree data.
///
/// Guided by `LLM_cleaner_guidelines.md`.
"""

import os, json, argparse
from datetime import datetime
from pathlib import Path

PLATFORM = "linktree"
PROJECT_ROOT = Path(os.environ["PROJECT_ROOT"])

# Use environment variables for zone names
LANDING_ZONE = os.environ.get("LANDING_ZONE", "landing")
RAW_ZONE = os.environ.get("RAW_ZONE", "raw")

LANDING_DIR = PROJECT_ROOT / LANDING_ZONE / PLATFORM
RAW_DIR     = PROJECT_ROOT / RAW_ZONE / PLATFORM

for _dir in (LANDING_DIR, RAW_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

def transform_response(payload: dict) -> list[dict]:
    """Flatten GraphQL responses - handle multiple possible structures."""
    # Try main structure first
    try:
        ts_rows = (
            payload["data"]
                   ["getAccountAnalytics"]
                   ["overview"]
                   ["timeseries"]
        )
        print(f"[DEBUG] Found timeseries data with {len(ts_rows)} rows")
        return [{
            "date":              r.get("date"),
            "totalViews":        r.get("totalViews"),
            "uniqueViews":       r.get("uniqueViews"),
            "totalClicks":       r.get("totalClicks"),
            "uniqueClicks":      r.get("uniqueClicks"),
            "clickThroughRate":  r.get("clickThroughRate"),
            "__typename":        r.get("__typename")
        } for r in ts_rows]
    except (KeyError, TypeError) as e:
        pass
    
    # Try alternative structures or extract any data arrays found
    if "data" in payload:
        data = payload["data"]
        # Look for any arrays that might contain analytics data
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0:
                print(f"[DEBUG] Found data array '{key}' with {len(value)} items")
                # Store raw structure for further analysis
                return [{"raw_data": value, "query_type": key}]
            elif isinstance(value, dict):
                # Recurse into nested objects
                for nested_key, nested_value in value.items():
                    if isinstance(nested_value, list) and len(nested_value) > 0:
                        print(f"[DEBUG] Found nested data array '{nested_key}' with {len(nested_value)} items")
                        return [{"raw_data": nested_value, "query_type": f"{key}.{nested_key}"}]
    
    print("[WARN] No recognizable data structure found in GraphQL response")
    print(f"[DEBUG] Available keys: {list(payload.keys()) if isinstance(payload, dict) else 'Not a dict'}")
    # Store the entire payload for analysis if no structure matches
    return [{"raw_payload": payload, "needs_analysis": True}]

def process_file(in_path: Path) -> int:
    # Ensure analytics subdirectory exists in raw
    analytics_dir = RAW_DIR / "analytics"
    analytics_dir.mkdir(parents=True, exist_ok=True)
    out_path = analytics_dir / f"{in_path.stem}.ndjson"
    written  = 0
    try:
        with in_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        rows = transform_response(payload)
        if not rows:
            print(f"[WARN] No data extracted from {in_path.name}")
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
        sorted((LANDING_DIR / "analytics").glob("*.json"))
    )

    total_rows = 0
    for fp in files:
        total_rows += process_file(fp)

    if total_rows == 0:
        print("[WARN] No records processed - this may indicate a structure change in GraphQL responses.")
        print("[INFO] Check the raw JSON files in landing/ to understand the current response format.")
        # Don't abort - let the pipeline continue with existing data
        print("[INFO] Continuing with existing data in raw/ directory.")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[INFO] Completed run at {timestamp} – {total_rows} rows total.")

if __name__ == "__main__":
    main()
