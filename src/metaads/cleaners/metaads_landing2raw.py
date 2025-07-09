# %%
# ─── Cell 1: Imports & Environment Setup ────────────────────────────────────────
# Validate Meta Ads dumps in the landing zone and move complete folders to raw.
import os, shutil, hashlib, json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT"))
LANDING      = PROJECT_ROOT / os.getenv("LANDING_ZONE", "landing")
RAW          = PROJECT_ROOT / os.getenv("RAW_ZONE",     "raw")


# %%
# ─── Cell 2: Validate and Promote Dump Folders ──────────────────────────────────
meta_landing = LANDING / "metaads"
raw_meta     = RAW / "metaads"
raw_meta.mkdir(parents=True, exist_ok=True)
required = {"ads.json","adsets.json","campaigns.json","insights.json"}

def folder_hash(folder: Path) -> str:
    h = hashlib.md5()
    for f in sorted(folder.glob("*.json")):
        h.update(hashlib.md5(f.read_bytes()).digest())
    return h.hexdigest()

def is_valid(folder: Path) -> bool:
    if not required.issubset({f.name for f in folder.glob("*.json")}):
        return False
    try:
        for f in required: json.loads((folder / f).read_text())
        return True
    except Exception:      return False

promoted = []
for dump in sorted(meta_landing.iterdir()):
    if not dump.is_dir() or not is_valid(dump): continue
    dest = raw_meta / dump.name
    if dest.exists() and folder_hash(dest) == folder_hash(dump):
        print(f"↩︎ {dump.name} already in RAW")
        continue
    if dest.exists():  # version duplicate
        dest = raw_meta / f"{dump.name}__{datetime.utcnow():%Y%m%dT%H%M%S}"
    shutil.copytree(dump, dest)
    promoted.append(dest.name)
    print(f"✅ promoted {dest.name}")

print(f"Summary: {len(promoted)} new dump(s) promoted.")


# %%



