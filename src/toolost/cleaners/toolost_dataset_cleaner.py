# %%
# Cell 1: Imports
import os
import json
import pandas as pd
from IPython.display import display
from dotenv import load_dotenv

# %%
# Cell 2: Define file paths and load JSON
import glob
load_dotenv()
PROJECT_ROOT = os.getenv("PROJECT_ROOT")
# FIX: Use correct raw zone (PROJECT_ROOT/raw/toolost/streams), not src/raw/toolost/streams
raw_dir = os.path.join(PROJECT_ROOT, "raw", "toolost", "streams")
# Get latest Spotify JSON
spotify_files = sorted(glob.glob(os.path.join(raw_dir, "toolost_spotify_*.json")), key=os.path.getmtime, reverse=True)
apple_files = sorted(glob.glob(os.path.join(raw_dir, "toolost_apple_*.json")), key=os.path.getmtime, reverse=True)
if not spotify_files or not apple_files:
    raise FileNotFoundError("Could not find required TooLost JSON files in raw/toolost/streams.")
spotify_path = spotify_files[0]
apple_path = apple_files[0]
print(f"Using Spotify JSON: {spotify_path}")
print(f"Using Apple JSON: {apple_path}")

with open(spotify_path, "r", encoding="utf-8") as f:
    spotify_data = json.load(f)

with open(apple_path, "r", encoding="utf-8") as f:
    apple_data = json.load(f)


# %%
# Cell 3: Build DataFrames
# Spotify JSON has top-level "streams"
spotify_df = pd.DataFrame(spotify_data.get("streams", []))
spotify_df["date"] = pd.to_datetime(spotify_df["date"])
spotify_df["spotify_streams"] = spotify_df["streams"].astype(int)
spotify_df = spotify_df[["date", "spotify_streams"]]

print(f"Most recent Spotify reporting date: {spotify_df['date'].max().date()}")

# Apple JSON has top-level "totalStreams"
apple_df = pd.DataFrame(apple_data.get("totalStreams", []))
apple_df["date"] = pd.to_datetime(apple_df["date"])
apple_df["apple_streams"] = apple_df["streams"].astype(int)
apple_df = apple_df[["date", "apple_streams"]]

print(f"Most recent Apple Music reporting date: {apple_df['date'].max().date()}")


# %%
# Cell 4: Merge and compute combined streams
df = pd.merge(spotify_df, apple_df, on="date", how="outer").fillna(0)
df["combined_streams"] = (df["spotify_streams"] + df["apple_streams"]).astype(int)
df = df.sort_values("date").reset_index(drop=True)

# Quick peek
display(df.head())


# %%
# Cell 5: Save to staging CSV
staging_dir = os.path.join(PROJECT_ROOT, "staging")
os.makedirs(staging_dir, exist_ok=True)

output_csv = os.path.join(staging_dir, "daily_streams_toolost.csv")
df.to_csv(output_csv, index=False)
print(f"Saved CSV to: {output_csv}")


# %%
# Cell 6: Post-validation (using absolute path)
validate_path = os.path.join(staging_dir, "daily_streams_toolost.csv")
validate_df = pd.read_csv(validate_path)

total_spotify  = validate_df["spotify_streams"].sum()
total_apple    = validate_df["apple_streams"].sum()
total_combined = validate_df["combined_streams"].sum()

print(f"Total Spotify streams:  {total_spotify}")
print(f"Total Apple streams:    {total_apple}")
print(f"Total Combined streams: {total_combined}")

if total_spotify + total_apple == total_combined:
    print("✅ Validation passed: sum(spotify) + sum(apple) == sum(combined)")
else:
    print("❌ Validation failed: sums do not match")


# %%



