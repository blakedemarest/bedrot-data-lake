import os
import re
import json
from pathlib import Path

LANDING_DIR = Path.cwd() / "landing" / "distrokid" / "streams"

# Validation for streams_stats HTML
STREAMS_PATTERN = re.compile(r'"trend365day".*?"dataProvider"\s*:\s*\[(.*?)\]', re.DOTALL)

# Validation for applemusic_stats HTML
CHARTDATA_PATTERN = re.compile(r'var\s+chartData\s*=\s*([\s\S]+?);\s*\n', re.MULTILINE)

def validate_streams_stats(filepath):
    with open(filepath, encoding="utf-8") as f:
        content = f.read()
    if not content.strip():
        return False, "File is empty."
    if '"trend365day"' not in content or '"dataProvider": [' not in content:
        return False, 'Missing required trend365day/dataProvider section.'
    # Try to extract and check dataProvider array
    match = STREAMS_PATTERN.search(content)
    if not match:
        return False, 'Could not extract dataProvider array.'
    data_str = '[' + match.group(1).strip().rstrip(',') + ']'
    try:
        data = json.loads(data_str)
        if not isinstance(data, list) or not data:
            return False, 'dataProvider is empty.'
    except Exception as e:
        return False, f'Failed to parse dataProvider: {e}'
    return True, "Valid."

def validate_applemusic_stats(filepath):
    with open(filepath, encoding="utf-8") as f:
        content = f.read()
    if not content.strip():
        return False, "File is empty."
    if 'var chartData =' not in content:
        return False, 'Missing chartData variable.'
    match = re.search(r'var chartData = ([\s\S]+?);', content)
    if not match:
        return False, 'Could not extract chartData.'
    try:
        data = json.loads(match.group(1))
        if not data:
            return False, 'chartData is empty.'
    except Exception as e:
        return False, f'Failed to parse chartData: {e}'
    return True, "Valid."

import shutil
RAW_DIR = Path.cwd() / "raw" / "distrokid" / "streams"

def main():
    print(f"Looking for files in: {LANDING_DIR}")
    found = False
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for file in LANDING_DIR.glob("streams_stats_*.html"):
        found = True
        print(f"Found: {file.name}")
        valid, msg = validate_streams_stats(file)
        print(f"{file.name}: {'VALID' if valid else 'INVALID'} - {msg}")
        if valid:
            dest = RAW_DIR / file.name
            shutil.copy2(file, dest)
            print(f"Copied to raw: {dest}")
    for file in LANDING_DIR.glob("applemusic_stats_*.html"):
        found = True
        print(f"Found: {file.name}")
        valid, msg = validate_applemusic_stats(file)
        print(f"{file.name}: {'VALID' if valid else 'INVALID'} - {msg}")
        if valid:
            dest = RAW_DIR / file.name
            shutil.copy2(file, dest)
            print(f"Copied to raw: {dest}")
    if not found:
        print("No matching files found for validation.")

if __name__ == "__main__":
    main()
