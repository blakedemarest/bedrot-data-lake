# %%
# ─── Cell 1: Imports & Environment Setup ────────────────────────────────────────
# Convert raw DistroKid HTML and TSV files into cleaned CSVs in the staging zone.
# Uses PROJECT_ROOT for zone paths.
import os, re, json
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from IPython.display import display

load_dotenv()
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT"))
RAW      = PROJECT_ROOT / os.getenv("RAW_ZONE",     "raw")
STAGING  = PROJECT_ROOT / os.getenv("STAGING_ZONE", "staging")


# %%
# ─── Cell 2: Locate Latest HTML & Helpers ───────────────────────────────────────
raw_dir = RAW / "distrokid" / "streams"
dk_html   = sorted(raw_dir.glob("streams_stats_*.html"), key=lambda p: p.stat().st_mtime, reverse=True)[0]
apple_html= sorted(raw_dir.glob("applemusic_stats_*.html"), key=lambda p: p.stat().st_mtime, reverse=True)[0]

streams_re = re.compile(r'"id"\s*:\s*"trend365day".+?"dataProvider"\s*:\s*\[([^\]]+)\]', re.DOTALL)
apple_re   = re.compile(r'"dataProvider"\s*:\s*\[([^\]]+)\]', re.DOTALL)


# %%
# ─── Cell 3: Extract Daily Streams from DistroKid HTML ──────────────────────────
text = dk_html.read_text(encoding="utf-8", errors="ignore")
arr   = "[" + streams_re.search(text).group(1) + "]"
arr   = re.sub(r',\s*\]', ']', arr)
dk_df = (pd.DataFrame(json.loads(arr))
           .rename(columns={"category":"date","column-1":"spotify_streams"})
           .assign(date=lambda d: pd.to_datetime(d["date"]),
                   spotify_streams=lambda d: d["spotify_streams"].astype(int))
           [["date","spotify_streams"]])


# %%
# ─── Cell 4: Extract Daily Streams from Apple Music HTML ────────────────────────
providers = []
for m in apple_re.finditer(apple_html.read_text(encoding="utf-8", errors="ignore")):
    block = "[" + m.group(1) + "]"
    block = re.sub(r',\s*\]', ']', block)
    try: providers.append(json.loads(block))
    except: pass
data = max(providers, key=len)
date_key  = "field" if "field" in data[0] else "category"
value_key = "value" if "value" in data[0] else ("column-1" if "column-1" in data[0] else list(data[0].keys())[1])

apple_df = (pd.DataFrame(data)
            .rename(columns={date_key:"date", value_key:"apple_streams"})
            .assign(date=lambda d: pd.to_datetime(d["date"]),
                    apple_streams=lambda d: d["apple_streams"].astype(int))
            [["date","apple_streams"]])


# %%
# ─── Cell 5: Merge, QC, Save to STAGING ─────────────────────────────────────────
merged = (dk_df.merge(apple_df, on="date", how="outer")
                .fillna(0)
                .astype({"spotify_streams":"int64","apple_streams":"int64"}))
merged["combined_streams"] = merged["spotify_streams"] + merged["apple_streams"]

STAGING.mkdir(parents=True, exist_ok=True)
out_csv = STAGING / "daily_streams_distrokid.csv"
merged.to_csv(out_csv, index=False)
display(merged.head())
print(f"💾 saved → {out_csv}")


# %%
# ─── Cell 6: Copy Bank Details CSV to STAGING ───────────────────────────────────
finance_dir = RAW / "distrokid" / "finance"
csvs = sorted(finance_dir.glob("dk_bank_details_*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
if csvs:
    bank_dst = STAGING / "dk_bank_details.csv"
    bank_dst.write_bytes(csvs[0].read_bytes())
    print(f"💾 bank details copied → {bank_dst}")


# %%



