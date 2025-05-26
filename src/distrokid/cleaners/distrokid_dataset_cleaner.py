# %%
# 📦 Cell 1 – Imports
# ------------------------------------------------------------
from pathlib import Path
import re, json, pandas as pd

# %%
# 📂 Cell 2 – Source & target paths
# ------------------------------------------------------------
from glob import glob
raw_dir = Path(r"C:\Users\Earth\BEDROT PRODUCTIONS\BEDROT DATA LAKE\data_lake\raw\distrokid\streams")
# Get latest DistroKid HTML
streams_files = sorted(raw_dir.glob("streams_stats_*.html"), key=lambda p: p.stat().st_mtime, reverse=True)
apple_files = sorted(raw_dir.glob("applemusic_stats_*.html"), key=lambda p: p.stat().st_mtime, reverse=True)
if not streams_files or not apple_files:
    raise FileNotFoundError("Could not find required DistroKid or Apple Music HTML files in raw/distrokid/streams.")
distrokid_html = streams_files[0]
apple_html = apple_files[0]
print(f"Using DistroKid HTML: {distrokid_html}")
print(f"Using Apple Music HTML: {apple_html}")

curated_dir    = Path(r"C:\Users\Earth\BEDROT PRODUCTIONS\BEDROT DATA LAKE\data_lake\curated")
curated_dir.mkdir(parents=True, exist_ok=True)

out_csv        = curated_dir / "daily_streams_distrokid.csv"
print("CSV will be saved to:", out_csv)


# %%
# 🔎 Cell 3 – DistroKid daily extractor
def extract_distrokid_daily(html_path: Path) -> pd.DataFrame:
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'"id"\s*:\s*"trend365day".+?"dataProvider"\s*:\s*\[([^\]]+)\]', 
                  text, flags=re.DOTALL)
    if not m:
        raise ValueError("trend365day chart not found in DistroKid HTML.")
    arr_text = "[" + m.group(1).strip() + "]"
    arr_text = re.sub(r',\s*\]', ']', arr_text)
    data     = json.loads(arr_text)
    df = pd.DataFrame(data)
    df.rename(columns={"category": "date", "column-1": "spotify_streams"}, inplace=True)
    df["date"] = pd.to_datetime(df["date"])
    return df[["date", "spotify_streams"]]


# %%
# 🍏 Cell 4 – Apple Music daily extractor
def extract_apple_daily(html_path: Path) -> pd.DataFrame:
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    providers = []
    for m in re.finditer(r'"dataProvider"\s*:\s*\[([^\]]+)\]', text, re.DOTALL):
        array_txt = "[" + m.group(1) + "]"
        array_txt = re.sub(r',\s*\]', ']', array_txt)
        try:
            providers.append(json.loads(array_txt))
        except json.JSONDecodeError:
            continue
    if not providers:
        raise ValueError("No dataProvider arrays found in Apple Music HTML.")
    data = max(providers, key=len)           # assume longest = daily
    if len(data) < 50:
        raise ValueError("Daily data array looks too short; check HTML.")
    first      = data[0]
    date_key   = "field" if "field" in first else "category"
    value_key  = "value" if "value" in first else ("column-1" if "column-1" in first else list(first.keys())[1])
    df         = pd.DataFrame(data)
    df.rename(columns={date_key: "date", value_key: "apple_streams"}, inplace=True)
    df["date"] = pd.to_datetime(df["date"])
    return df[["date", "apple_streams"]]


# %%
# 🏗️ Cell 5 – Combine the two sources
dk_df    = extract_distrokid_daily(distrokid_html)
apple_df = extract_apple_daily(apple_html)

print(f"Most recent DistroKid (Spotify) reporting date: {dk_df['date'].max().date()}")
print(f"Most recent Apple Music reporting date: {apple_df['date'].max().date()}")

combined = (dk_df
            .merge(apple_df, on="date", how="outer")
            .sort_values("date")
            .fillna(0))

combined["spotify_streams"] = combined["spotify_streams"].astype(int)
combined["apple_streams"]   = combined["apple_streams"].astype(int)
combined["combined_streams"] = combined["spotify_streams"] + combined["apple_streams"]

combined.head()


# %%
# 💾 Cell 6 – Write CSV & confirm
combined.to_csv(out_csv, index=False)
print(f"✅  Saved merged CSV to: {out_csv}")
print(f"Rows: {len(combined)}, Date range: {combined['date'].min().date()} → {combined['date'].max().date()}")

combined.tail()


# %%
# 🔍 Cell 7 – Post-validation check (absolute path)
# ------------------------------------------------------------
from pathlib import Path
import pandas as pd

csv_to_validate = Path(r"C:\Users\Earth\BEDROT PRODUCTIONS\BEDROT DATA LAKE\data_lake\curated\daily_streams_distrokid.csv")

df = pd.read_csv(csv_to_validate)

sum_spotify  = df["spotify_streams"].sum()
sum_apple    = df["apple_streams"].sum()
sum_combined = df["combined_streams"].sum()

print(f"Spotify total  : {sum_spotify:,}")
print(f"Apple total    : {sum_apple:,}")
print(f"Combined total : {sum_combined:,}")

if (sum_spotify + sum_apple) == sum_combined:
    print("\n✅  Validation passed — sums line up.")
else:
    print("\n❌  Validation FAILED — combined total mismatch.")


# %%



