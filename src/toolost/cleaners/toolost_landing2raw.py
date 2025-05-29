# %%
# ─── Cell 1: Imports & Environment Setup ────────────────────────────────────────
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
    if tgt.exists() and hashlib.md5(tgt.read_bytes()).hexdigest() == hashlib.md5(file.read_bytes()).hexdigest():
        print(f"↩︎ {file.name:40} already in raw (hash match)")
        continue

    if tgt.exists():  # name clash but different hash → version it
        ts  = datetime.now().strftime("%Y%m%dT%H%M%S")
        tgt = raw_dir / f"{file.stem}__{ts}{file.suffix}"

    shutil.copy2(file, tgt)
    print(f"✅ {file.name:40} → {tgt.name}")
    promoted.append(tgt.name)

print("\nSummary:", f"promoted={len(promoted)}, skipped/invalid={len(skipped)}")


# %%



