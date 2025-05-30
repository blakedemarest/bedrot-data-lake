# %%
# ─── Cell 1: Imports & Environment Setup ────────────────────────────────────────
import os, hashlib, datetime, shutil
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT"))
STAGING = PROJECT_ROOT / os.getenv("STAGING_ZONE",  "staging")
CURATED = PROJECT_ROOT / os.getenv("CURATED_ZONE",  "curated")
ARCHIVE = PROJECT_ROOT / os.getenv("ARCHIVE_ZONE",  "archive")


# %%
# ─── Cell 2: Append ONLY brand-new (date_start, ad_id) rows ────────────────────
src = STAGING / "tidy_metaads.csv"

# 1️⃣  Load staging, drop exact dupes inside the file itself
new = (pd.read_csv(src, parse_dates=["date_start","date_stop"], low_memory=False)
         .drop_duplicates(subset=["date_start","ad_id"]))

# Build PK
new["_pk"] = new[["date_start","ad_id"]].astype(str).agg("|".join, axis=1)

cur_path = CURATED / "metaads_campaigns_daily.csv"
if cur_path.exists():
    cur = (pd.read_csv(cur_path, parse_dates=["date_start","date_stop"], low_memory=False)
             .drop_duplicates(subset=["date_start","ad_id"]))          # ensure tidy history
    cur["_pk"] = cur[["date_start","ad_id"]].astype(str).agg("|".join, axis=1)

    # 2️⃣  Keep only brand-new PKs
    append_only = new[~new["_pk"].isin(cur["_pk"])].drop(columns="_pk")
    merged = pd.concat([cur.drop(columns="_pk"), append_only], ignore_index=True)
else:
    cur_path.parent.mkdir(parents=True, exist_ok=True)
    merged = new.drop(columns="_pk")

# 3️⃣  Sort for readability
merged = merged.sort_values(["date_start","campaign_id","adset_id","ad_id"]).reset_index(drop=True)


# %%
# ─── Cell 3: Save & archive if dataset changed ─────────────────────────────────
def df_hash(df):  return hashlib.md5(df.to_csv(index=False).encode()).hexdigest()
def file_hash(p): return hashlib.md5(p.read_bytes()).hexdigest()

if cur_path.exists() and df_hash(merged) == file_hash(cur_path):
    print("↩︎ No changes – curated already up-to-date.")
else:
    if cur_path.exists():
        ARCHIVE.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
        shutil.copy2(cur_path, ARCHIVE / f"metaads_campaigns_daily_{ts}.csv")
        print("📦 Archived previous version.")
    merged.to_csv(cur_path, index=False)
    print(f"✅ Curated updated – rows: {len(merged)}")


# %%



