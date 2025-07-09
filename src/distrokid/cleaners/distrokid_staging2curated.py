# %%
# ─── Cell 1: Imports & Environment Setup ────────────────────────────────────────
# Merge daily DistroKid data into the curated dataset after validation.
# Relies on PROJECT_ROOT for zone folders.
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
# ─── Cell 2: Update tidy_daily_streams.csv without touching TooLost rows ────────
dk_src = STAGING / "daily_streams_distrokid.csv"
df_dk  = pd.read_csv(dk_src, parse_dates=["date"])
df_dk["source"] = "distrokid"

cur_path = CURATED / "tidy_daily_streams.csv"
if cur_path.exists():
    cur_df = pd.read_csv(cur_path, parse_dates=["date"])
    cur_df = cur_df[cur_df["source"] != "distrokid"]        # remove stale DK rows
    merged = pd.concat([cur_df, df_dk], ignore_index=True)
else:
    cur_path.parent.mkdir(parents=True, exist_ok=True)
    merged = df_dk

num_cols = [c for c in merged.columns if c not in ("date","source")]
merged[num_cols] = merged[num_cols].round().astype("int64")

order = pd.CategoricalDtype(categories=["distrokid","toolost"], ordered=True)
merged["source"] = merged["source"].astype(order)
merged = merged.sort_values(["source","date"]).reset_index(drop=True)


# %%
# ─── Cell 3: Save/Archive tidy_daily_streams.csv ────────────────────────────────
def fhash(p: Path): return hashlib.md5(p.read_bytes()).hexdigest()
def dfhash(df):     return hashlib.md5(df.to_csv(index=False).encode()).hexdigest()

if cur_path.exists() and fhash(cur_path) == dfhash(merged):
    print("↩︎ No changes – curated already up-to-date.")
else:
    if cur_path.exists():
        ts   = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
        ARCHIVE.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cur_path, ARCHIVE / f"tidy_daily_streams_{ts}.csv")
    merged.to_csv(cur_path, index=False)
    print(f"✅ Curated updated → {cur_path.relative_to(PROJECT_ROOT)}")


# %%
# ─── Cell 4: Promote Bank Details CSV & Archive ────────────────────────────────
bank_src = STAGING / "dk_bank_details.csv"
bank_dst = CURATED / "dk_bank_details.csv"

if bank_src.exists():
    if bank_dst.exists() and fhash(bank_dst) == fhash(bank_src):
        print("↩︎ Bank details unchanged.")
    else:
        if bank_dst.exists():
            ts = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
            shutil.copy2(bank_dst, ARCHIVE / f"dk_bank_details_{ts}.csv")
        shutil.copy2(bank_src, bank_dst)
        print(f"✅ Bank details promoted → {bank_dst.relative_to(PROJECT_ROOT)}")


# %%



