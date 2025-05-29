# %%
# ─── Cell 1: Imports & Environment Setup ────────────────────────────────────────
import os, json
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from IPython.display import display

load_dotenv()
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT"))
RAW     = PROJECT_ROOT / os.getenv("RAW_ZONE",     "raw")
STAGING = PROJECT_ROOT / os.getenv("STAGING_ZONE", "staging")


# %%
# ─── Cell 2: Locate Latest Spotify & Apple JSONs in RAW ─────────────────────────
raw_dir = RAW / "toolost" / "streams"
spotify_files = sorted(raw_dir.glob("toolost_spotify_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
apple_files   = sorted(raw_dir.glob("toolost_apple_*.json")  , key=lambda p: p.stat().st_mtime, reverse=True)
assert spotify_files and apple_files, "No TooLost JSON files found in raw/toolost/streams."

with spotify_files[0].open(encoding="utf-8") as f:
    spotify_data = json.load(f)
with apple_files[0].open(encoding="utf-8") as f:
    apple_data   = json.load(f)

print(f"Using Spotify file → {spotify_files[0].name}")
print(f"Using Apple   file → {apple_files [0].name}")


# %%
# ─── Cell 3: Build Daily Stream DataFrame ───────────────────────────────────────
sp_df = (pd.DataFrame(spotify_data["streams"])
           .assign(date=lambda d: pd.to_datetime(d["date"]),
                   spotify_streams=lambda d: d["streams"].astype(int))
           [["date","spotify_streams"]])

ap_df = (pd.DataFrame(apple_data["totalStreams"])
           .assign(date=lambda d: pd.to_datetime(d["date"]),
                   apple_streams=lambda d: d["streams"].astype(int))
           [["date","apple_streams"]])

df = (sp_df.merge(ap_df, on="date", how="outer")
            .fillna(0)
            .assign(combined_streams=lambda d: d["spotify_streams"] + d["apple_streams"])
            .sort_values("date")
            .reset_index(drop=True))

display(df.head())


# %%
# ─── Cell 4: Save to STAGING & Sanity-Check Totals ─────────────────────────────
STAGING.mkdir(parents=True, exist_ok=True)
out_csv = STAGING / "daily_streams_toolost.csv"
df.to_csv(out_csv, index=False)
print(f"💾 saved → {out_csv}")

assert df["combined_streams"].sum() == df["spotify_streams"].sum() + df["apple_streams"].sum(), \
       "sanity check failed: combined ≠ components"
print("✅ QC passed – totals align")


# %%



