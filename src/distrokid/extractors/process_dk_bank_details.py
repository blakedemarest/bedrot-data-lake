import os
import shutil
from pathlib import Path
import pandas as pd

# Use PROJECT_ROOT from environment
PROJECT_ROOT = os.environ.get('PROJECT_ROOT')
if not PROJECT_ROOT:
    raise EnvironmentError("PROJECT_ROOT environment variable must be set.")
PROJECT_ROOT = Path(PROJECT_ROOT)

LANDING_DIR = PROJECT_ROOT / 'landing' / 'distrokid' / 'streams'
RAW_DIR = PROJECT_ROOT / 'raw' / 'distrokid' / 'streams'
STAGED_DIR = PROJECT_ROOT / 'staged'
CURATED_DIR = PROJECT_ROOT / 'curated'

# Step 1: Find most recent TSV in landing
landing_tsvs = sorted(LANDING_DIR.glob('dk_bank_details_*.tsv'), key=os.path.getmtime, reverse=True)
if not landing_tsvs:
    raise FileNotFoundError(f"No dk_bank_details_*.tsv files found in {LANDING_DIR}")
latest_tsv = landing_tsvs[0]

# Step 2: Validate and convert to CSV, move to raw
try:
    df = pd.read_csv(latest_tsv, sep='\t')
except Exception as e:
    raise ValueError(f"Failed to read TSV file {latest_tsv}: {e}")

RAW_DIR.mkdir(parents=True, exist_ok=True)
csv_name = latest_tsv.with_suffix('.csv').name
raw_csv = RAW_DIR / csv_name
df.to_csv(raw_csv, index=False)
print(f"Converted {latest_tsv} to {raw_csv}")

# Step 3: Find most recent CSV in raw
raw_csvs = sorted(RAW_DIR.glob('dk_bank_details_*.csv'), key=os.path.getmtime, reverse=True)
if not raw_csvs:
    raise FileNotFoundError(f"No dk_bank_details_*.csv files found in {RAW_DIR}")
latest_csv = raw_csvs[0]

# Step 4: Push to staged as distrokid_earned_streams.csv and dk_bank_details.csv
STAGED_DIR.mkdir(parents=True, exist_ok=True)
staged_csv1 = STAGED_DIR / 'distrokid_earned_streams.csv'
staged_csv2 = STAGED_DIR / 'dk_bank_details.csv'
shutil.copy2(latest_csv, staged_csv1)
print(f"Copied {latest_csv} to {staged_csv1}")
shutil.copy2(latest_csv, staged_csv2)
print(f"Copied {latest_csv} to {staged_csv2}")

# Step 5: Copy to curated as dk_bank_details.csv (no timestamp)
CURATED_DIR.mkdir(parents=True, exist_ok=True)
curated_csv = CURATED_DIR / 'dk_bank_details.csv'
shutil.copy2(latest_csv, curated_csv)
print(f"Copied {latest_csv} to {curated_csv}")
