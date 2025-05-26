import json
import re
import sys
from pathlib import Path

def is_valid_date(date_str):
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", date_str))

def validate_spotify(data):
    if not isinstance(data, dict) or "streams" not in data:
        return False, "Missing 'streams' key or not a dict"
    streams = data["streams"]
    if not isinstance(streams, list) or not streams:
        return False, "'streams' is not a non-empty list"
    for entry in streams:
        if not isinstance(entry, dict):
            return False, "Entry in 'streams' is not a dict"
        if "date" not in entry or not is_valid_date(entry["date"]):
            return False, f"Invalid or missing date: {entry.get('date')}"
        if "streams" not in entry:
            return False, "Missing 'streams' in entry"
        try:
            int(entry["streams"])
        except Exception:
            return False, f"'streams' is not an int or int-string: {entry['streams']}"
    return True, "OK"

def validate_apple(data):
    if not isinstance(data, dict) or "totalStreams" not in data:
        return False, "Missing 'totalStreams' key or not a dict"
    streams = data["totalStreams"]
    if not isinstance(streams, list) or not streams:
        return False, "'totalStreams' is not a non-empty list"
    for entry in streams:
        if not isinstance(entry, dict):
            return False, "Entry in 'totalStreams' is not a dict"
        if "date" not in entry or not is_valid_date(entry["date"]):
            return False, f"Invalid or missing date: {entry.get('date')}"
        if "streams" not in entry or not isinstance(entry["streams"], int):
            return False, f"'streams' is not an integer: {entry.get('streams')}"
    return True, "OK"

def validate_toolost_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "streams" in data:
        return validate_spotify(data)
    elif "totalStreams" in data:
        return validate_apple(data)
    else:
        return False, "Unknown TooLost JSON structure"

import glob

import shutil

def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_toolost_json.py <file1.json> [<file2.json> ...]")
        sys.exit(1)
    files = []
    for arg in sys.argv[1:]:
        files.extend(glob.glob(arg))
    if not files:
        print("No files found to validate.")
        sys.exit(1)
    promoted = []
    failed = []
    # Always resolve from the data_lake directory (project root)
    # Go up three levels: extractors -> toolost -> src -> data_lake
    project_root = Path(__file__).resolve().parents[3]
    raw_dir = project_root / "raw" / "toolost" / "streams"
    raw_dir.mkdir(parents=True, exist_ok=True)
    print(f"[DEBUG] Files will be copied to: {raw_dir}")
    for path in files:
        valid, msg = validate_toolost_json(path)
        fname = Path(path).name
        if valid:
            dest = raw_dir / fname
            shutil.copy2(path, dest)
            print(f"{fname}: VALID - promoted to raw/toolost/streams/")
            promoted.append(fname)
        else:
            print(f"{fname}: INVALID - {msg}")
            failed.append(fname)
    print("\n--- SUMMARY ---")
    print(f"Promoted to raw/toolost/streams/: {promoted if promoted else 'None'}")
    print(f"Failed validation: {failed if failed else 'None'}")

if __name__ == "__main__":
    main()
