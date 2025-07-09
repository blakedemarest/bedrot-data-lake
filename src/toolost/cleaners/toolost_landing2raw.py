# %%
# ─── Cell 1: Imports & Environment Setup ────────────────────────────────────────
# Move TooLost downloads from the landing zone to raw after basic validation.
import os, hashlib, shutil, json, glob
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT"))
LANDING      = PROJECT_ROOT / os.getenv("LANDING_ZONE",  "landing")
RAW          = PROJECT_ROOT / os.getenv("RAW_ZONE",      "raw")


# %%
# ─── Cell 2: TooLost JSON-Schema Validators ─────────────────────────────────────
import re

_date_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
def _is_date(s): return bool(_date_re.match(str(s)))

def validate_spotify(obj):
    if not isinstance(obj, dict) or "streams" not in obj:
        return False, "missing key 'streams'"
    for rec in obj["streams"]:
        if not (_is_date(rec.get("date")) and str(rec.get("streams")).isdigit()):
            return False, f"bad record {rec}"
    return True, "OK"

def validate_apple(obj):
    if not isinstance(obj, dict) or "totalStreams" not in obj:
        return False, "missing key 'totalStreams'"
    for rec in obj["totalStreams"]:
        if not (_is_date(rec.get("date")) and isinstance(rec.get("streams"), int)):
            return False, f"bad record {rec}"
    return True, "OK"

def validate_toolost_json(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if "streams"      in data: return validate_spotify(data)
    if "totalStreams" in data: return validate_apple(data)
    return False, "unknown schema"


# %%
# ─── Cell 3: Promote Valid Landing Files to RAW Zone ────────────────────────────
landing_dir = LANDING / "toolost" / "streams"
raw_dir     = RAW     / "toolost" / "streams"
landing_dir.mkdir(parents=True, exist_ok=True)
raw_dir.mkdir(parents=True, exist_ok=True)

promoted, skipped = [], []
for file in sorted(landing_dir.glob("*.json")):
    valid, msg = validate_toolost_json(file)
    if not valid:
        print(f"❌ {file.name:40} {msg}")
        skipped.append(file.name)
        continue

    tgt = raw_dir / file.name
    file_hash = hashlib.md5(file.read_bytes()).hexdigest()
    
    # Check if file already exists in raw
    if tgt.exists():
        existing_hash = hashlib.md5(tgt.read_bytes()).hexdigest()
        if file_hash == existing_hash:
            # Check timestamps to provide better info
            file_time = datetime.fromtimestamp(file.stat().st_mtime)
            existing_time = datetime.fromtimestamp(tgt.stat().st_mtime)
            
            print(f"↩︎ {file.name:40} already in raw (hash match)")
            print(f"   Landing file: {file_time} | Raw file: {existing_time}")
            
            # If the landing file is significantly newer, it might indicate stale data
            time_diff = file_time - existing_time
            if time_diff.days > 1:
                print(f"   ⚠️  WARNING: Landing file is {time_diff.days} days newer but content is identical")
                print(f"   This may indicate the TooLost API is returning cached/stale data")
            
            continue
        else:
            # Different hash → version it
            ts = datetime.now().strftime("%Y%m%dT%H%M%S")
            tgt = raw_dir / f"{file.stem}__{ts}{file.suffix}"
            print(f"🔄 {file.name:40} content changed, versioning as {tgt.name}")
    
    # Copy new or changed file
    shutil.copy2(file, tgt)
    print(f"✅ {file.name:40} → {tgt.name}")
    promoted.append(tgt.name)

print("\nSummary:", f"promoted={len(promoted)}, skipped/invalid={len(skipped)}")


# %%



