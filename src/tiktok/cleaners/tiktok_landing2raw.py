# %%
# ─── Cell 1: Setup ───────────────────────────────────────────────────────────────
# Unpack and validate TikTok analytics exports from landing and organize them in
# the raw zone.
import os, glob, zipfile, tempfile, shutil
import pandas as pd

# 1️⃣ Load PROJECT_ROOT from your environment
PROJECT_ROOT = os.getenv("PROJECT_ROOT")
if not PROJECT_ROOT:
    raise EnvironmentError("PROJECT_ROOT is not set in environment")

# 2️⃣ Define landing & raw directories
landing_dir = os.path.join(PROJECT_ROOT, "landing", "tiktok", "analytics")
raw_dir     = os.path.join(PROJECT_ROOT, "raw",     "tiktok")

# 3️⃣ Ensure the raw/tiktok folder exists
os.makedirs(raw_dir, exist_ok=True)

print("✔️  PROJECT_ROOT:", PROJECT_ROOT)
print("✔️  landing_dir:", landing_dir)
print("✔️  raw_dir:", raw_dir)


# %%
# ─── Cell 2: Locate Latest ZIP per Artist ────────────────────────────────────────
all_zips = glob.glob(os.path.join(landing_dir, "*.zip"))
if not all_zips:
    raise FileNotFoundError(f"No .zip files found under {landing_dir!r}")

# Map artist → newest ZIP
latest_per_artist = {}
for zp in all_zips:
    base   = os.path.splitext(os.path.basename(zp))[0]
    artist = base.split("_")[-1]  # token after last underscore
    if (artist not in latest_per_artist
        or os.path.getmtime(zp) > os.path.getmtime(latest_per_artist[artist])):
        latest_per_artist[artist] = zp

print("Found artists:", list(latest_per_artist.keys()))
for artist, zp in latest_per_artist.items():
    print(f" • {artist}: {os.path.basename(zp)}")


# %%
# ─── Cell 3: Process & Promote Each Artist’s Latest ZIP with Year Rollover ─────
processed = []
START_YEAR = 2024

for artist, latest_zip in latest_per_artist.items():
    print(f"\n➡️  Processing artist: {artist!r}")

    # a) Extract ZIP to temp
    temp_dir = tempfile.mkdtemp(prefix=f"tiktok_{artist}_")
    with zipfile.ZipFile(latest_zip, "r") as z:
        z.extractall(temp_dir)

    # b) Identify & load the single CSV
    csvs = glob.glob(os.path.join(temp_dir, "*.csv"))
    if len(csvs) != 1:
        print(f"⚠️  Expected 1 CSV in {os.path.basename(latest_zip)}, found {len(csvs)} → skipping")
        shutil.rmtree(temp_dir)
        continue

    csv_path = csvs[0]
    print("   ▶️  Loaded:", os.path.basename(csv_path))
    df = pd.read_csv(csv_path)

    # ─── Dynamic Year Rollover ───────────────────────────────────────────────────
    dates = []
    current_year = START_YEAR
    for md in df['Date']:
        # parse month-day into a datetime of the current_year
        dt = pd.to_datetime(f"{md} {current_year}", format="%B %d %Y", errors='raise')
        # if this dt is before the previous, we've crossed into the next year
        if dates and dt <= dates[-1]:
            current_year += 1
            dt = pd.to_datetime(f"{md} {current_year}", format="%B %d %Y")
        dates.append(dt)

    df['Date'] = dates
    df['Year'] = df['Date'].dt.year
    print(f"   • Parsed 'Date' with rollover starting {START_YEAR}, max year = {df['Year'].max()}")

    # c) Validate
    print("   • Summary stats:")
    print(df.describe(include="all"))
    missing = df.isna().sum()
    missing_cols = missing[missing > 0]
    if missing_cols.empty:
        print("   ✅ No missing values.")
    else:
        print("   ⚠️  Missing values detected:")
        print(missing_cols)

    # d) Promote if clean
    if missing_cols.empty:
        zip_base  = os.path.splitext(os.path.basename(latest_zip))[0]
        dest_name = f"{zip_base}.csv"
        dest_path = os.path.join(raw_dir, dest_name)
        # write out the cleaned CSV
        df.to_csv(dest_path, index=False)
        print(f"   ✅ Written cleaned CSV to raw as {dest_name!r}")
        processed.append(artist)
    else:
        print("   ⛔ Promotion skipped due to validation errors.")

    # e) Cleanup
    shutil.rmtree(temp_dir)
    print("   🧹 Cleaned up temporary files.")

print("\n🎉 Done. Artists successfully promoted:", processed)


# %% [markdown]
# # ─── Cell 4: Idempotency Note ────────────────────────────────────────────────────
# # This flow always picks only the latest ZIP per artist in landing\tiktok\analytics.
# # To prevent overwriting an existing clean CSV in raw\tiktok, wrap the write in:
# #
# #     if not os.path.exists(dest_path):
# #         df.to_csv(dest_path, index=False)
# #     else:
# #         print(f"ℹ️  {dest_name} already exists in raw/")
# 

# %% [markdown]
# 


