# %%
# ─── Cell 1: Setup ───────────────────────────────────────────────────────────────
# Clean raw TikTok analytics files and export standardized CSVs to the staging zone.
import os, glob, zipfile, tempfile, shutil
import pandas as pd

# 1️⃣ Load PROJECT_ROOT from your environment
PROJECT_ROOT = os.getenv("PROJECT_ROOT")
if not PROJECT_ROOT:
    raise EnvironmentError("PROJECT_ROOT is not set in environment")

# 2️⃣ Define raw and staging directories
raw_dir     = os.path.join(PROJECT_ROOT, "raw",     "tiktok")
staging_dir = os.path.join(PROJECT_ROOT, "staging")

# 3️⃣ Ensure both raw/tiktok and staging exist
os.makedirs(raw_dir, exist_ok=True)
os.makedirs(staging_dir, exist_ok=True)

print("✔ PROJECT_ROOT:", PROJECT_ROOT)
print("✔ raw_dir:", raw_dir)
print("✔ staging_dir:", staging_dir)


# %%
# ─── Cell 2: Load Existing Staging Data ─────────────────────────────────────────
staging_file = os.path.join(staging_dir, "tiktok.csv")

if os.path.exists(staging_file):
    staging_df = pd.read_csv(staging_file, parse_dates=["Date"])
    print(f"✔ Loaded existing staging ({len(staging_df)} rows)")
else:
    staging_df = pd.DataFrame(columns=["Artist","Date","Video Views","Profile Views","Likes","Comments","Shares","Year"])
    print("ℹ No existing staging file; starting fresh")


# %%
# ─── Cell 3: Load Latest Raw Snapshots per Artist ───────────────────────────────
raw_files = glob.glob(os.path.join(raw_dir, "*.csv"))
if not raw_files:
    raise FileNotFoundError(f"No CSVs found in raw directory: {raw_dir}")

# pick newest file per artist
latest_raw = {}
for fpath in raw_files:
    base   = os.path.splitext(os.path.basename(fpath))[0]
    artist = base.split("_")[-1]   # e.g. "zone.a0" or "pig1987"
    mtime  = os.path.getmtime(fpath)
    if artist not in latest_raw or mtime > latest_raw[artist][1]:
        latest_raw[artist] = (fpath, mtime)

# load each and tag
frames = []
for artist, (fpath, _) in latest_raw.items():
    df = pd.read_csv(fpath, parse_dates=["Date"])
    df["Artist"] = artist
    frames.append(df)

raw_df = pd.concat(frames, ignore_index=True)
print("✔ Loaded latest raw snapshots:")
for artist, (fpath, _) in latest_raw.items():
    print(f"   • {artist}: {os.path.basename(fpath)} ({len(pd.read_csv(fpath))} rows)")
print(f"→ Combined raw_df: {len(raw_df)} rows across {raw_df['Artist'].nunique()} artists")


# %%
# ─── Cell 4: Append New Data Without Overwriting  ────────────────────────
if staging_df.empty:
    # First run ever
    combined = raw_df.copy()
    print(f"ℹ No existing staging; using all {len(combined)} rows")
else:
    # figure out what’s new per artist
    last_dates = staging_df.groupby("Artist")["Date"].max().to_dict()
    new_list   = []
    for artist, grp in raw_df.groupby("Artist"):
        cutoff = last_dates.get(artist, pd.Timestamp.min)
        new    = grp[grp["Date"] > cutoff]
        print(f"ℹ {artist}: {len(new)} new rows since {cutoff.date()}")
        if not new.empty:
            # align to staging schema exactly
            new = new.reindex(columns=staging_df.columns)
            new_list.append(new)
    if new_list:
        new_rows = pd.concat(new_list, ignore_index=True)
        combined = pd.concat([staging_df, new_rows], ignore_index=True)
        # dedupe on (Artist, Date)
        combined = combined.drop_duplicates(subset=["Artist","Date"], keep="last")
        combined = combined.sort_values(["Artist","Date"]).reset_index(drop=True)
        print(f"✔ Appended {len(new_rows)} rows → combined now {len(combined)} total")
    else:
        combined = staging_df.copy()
        print("ℹ No new rows to append; staging unchanged")


# %%
# ─── Cell 5: Write Combined Data to Staging ─────────────────────────────────────
combined.to_csv(staging_file, index=False)
print(f"✔ Staging updated: {staging_file}")


# %%



