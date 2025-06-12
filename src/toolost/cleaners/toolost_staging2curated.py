# %%
# ─── Cell 1: Imports & Environment Setup ────────────────────────────────────────
# Merge TooLost daily streams into the curated dataset and archive prior versions.
import os
from pathlib import Path
import datetime, shutil
from dotenv import load_dotenv
import pandas as pd

from src.common.utils.hash_helpers import df_hash, file_hash

load_dotenv()
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT"))
STAGING = PROJECT_ROOT / os.getenv("STAGING_ZONE",  "staging")
CURATED = PROJECT_ROOT / os.getenv("CURATED_ZONE",  "curated")
ARCHIVE = PROJECT_ROOT / os.getenv("ARCHIVE_ZONE",  "archive")


# %%
# ─── Cell 2: Merge TooLost Data & Enforce Types / Order ─────────────────────────
toolost_src = STAGING / "daily_streams_toolost.csv"
df_toolost  = pd.read_csv(toolost_src, parse_dates=["date"])
df_toolost["source"] = "toolost"

curated_path = CURATED / "tidy_daily_streams.csv"
if curated_path.exists():
    df_curated = pd.read_csv(curated_path, parse_dates=["date"])
    # drop old TooLost rows
    df_curated = df_curated[df_curated["source"] != "toolost"]
    new_curated = pd.concat([df_curated, df_toolost], ignore_index=True)
else:
    curated_path.parent.mkdir(parents=True, exist_ok=True)
    new_curated = df_toolost

# convert numeric columns to int
num_cols = [c for c in new_curated.columns if c not in ("date", "source")]
new_curated[num_cols] = new_curated[num_cols].round().astype("int64")

# order: distrokid rows first, then toolost; dates ascending inside each source
source_cat = pd.CategoricalDtype(categories=["distrokid", "toolost"], ordered=True)
new_curated["source"] = new_curated["source"].astype(source_cat)
new_curated = (new_curated
               .sort_values(["source", "date"])
               .reset_index(drop=True))


# %%
# ─── Cell 3: Save & Archive if Changed ─────────────────────────────────────────

if curated_path.exists() and file_hash(curated_path) == df_hash(new_curated):
    print("↩︎ No changes – curated already up-to-date.")
else:
    if curated_path.exists():                       # archive prior version
        ts   = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
        ARCHIVE.mkdir(parents=True, exist_ok=True)
        arch = ARCHIVE / f"tidy_daily_streams_{ts}.csv"
        shutil.copy2(curated_path, arch)
        print(f"📦 Archived prior snapshot → {arch.relative_to(PROJECT_ROOT)}")

    new_curated.to_csv(curated_path, index=False)
    print(f"✅ Curated updated          → {curated_path.relative_to(PROJECT_ROOT)}")


# %%



