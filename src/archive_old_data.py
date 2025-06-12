"""
/// General Cleaner Script for Landing and Raw Zones.
///
/// Moves older copies of data files (older than 7 days) to the archive zone,
/// appending [ARCHIVED ON (datetime)] to the filename.
///
/// - Scans landing and raw zones recursively.
/// - For files with the same base identity (e.g., same prefix or matching
///   pattern), keeps the newest and archives older ones.
/// - Archive files are renamed to include the archive date.
"""
import os
import shutil
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT"))
LANDING = PROJECT_ROOT / "landing"
RAW = PROJECT_ROOT / "raw"
ARCHIVE = PROJECT_ROOT / "archive"

ARCHIVE.mkdir(parents=True, exist_ok=True)

# Helper: Get all files recursively in a zone
def get_all_files(zone):
    return [f for f in zone.rglob("*") if f.is_file()]

# Helper: Group files by base identity (prefix before timestamp or version)
def group_files(files):
    from collections import defaultdict
    import re
    groups = defaultdict(list)
    for f in files:
        # Try to extract base by splitting before first _date or version pattern
        # e.g. foo_20250526_123456.json -> foo
        match = re.match(r"(.+?)(_[0-9]{8,})(.*)", f.stem)
        base = match.group(1) if match else f.stem
        groups[base].append(f)
    return groups

# Main logic
def archive_old_copies(zone):
    now = datetime.now()
    files = get_all_files(zone)
    groups = group_files(files)
    for base, file_list in groups.items():
        if len(file_list) <= 1:
            continue  # No older copies
        # Sort by creation time, newest last
        file_list.sort(key=lambda f: f.stat().st_ctime)
        for old_file in file_list[:-1]:
            age = now - datetime.fromtimestamp(old_file.stat().st_ctime)
            if age.days > 7:
                archive_time = now.strftime("%Y-%m-%d_%H%M%S")
                new_name = f"{old_file.stem} [ARCHIVED ON {archive_time}]{old_file.suffix}"
                dest = ARCHIVE / new_name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(old_file), str(dest))
                print(f"Archived {old_file} -> {dest}")

if __name__ == "__main__":
    print("Scanning landing zone...")
    archive_old_copies(LANDING)
    print("Scanning raw zone...")
    archive_old_copies(RAW)
    print("Done.")
