# Meta Ads Daily Campaign Data - Staging to Curated Zone Cleaner
# Creates dual CSV outputs: campaigns metadata + performance log with 28-day rolling history
# Guided by LLM_cleaner_guidelines.md

# %%
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
import argparse

# %%
load_dotenv()
PROJECT_ROOT = Path(os.environ["PROJECT_ROOT"])
STAGING_DIR = PROJECT_ROOT / "staging" / "metaads"
CURATED_DIR = PROJECT_ROOT / "curated"
ARCHIVE_DIR = PROJECT_ROOT / "archive" / "metaads"

# Ensure directories exist
CURATED_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# %%
def load_staging_data() -> pd.DataFrame:
    """Load latest staging data from metaads_daily_campaigns_staging files"""
    
    staging_files = list(STAGING_DIR.glob("metaads_daily_campaigns_staging_*.csv"))
    
    if not staging_files:
        print(f"[CURATED] No staging files found in {STAGING_DIR}")
        return pd.DataFrame()
    
    # Use most recent staging file
    latest_file = max(staging_files, key=lambda x: x.stat().st_mtime)
    print(f"[CURATED] Loading staging data from {latest_file.name}")
    
    df = pd.read_csv(latest_file, encoding='utf-8')
    
    # Ensure date column is datetime
    df['date'] = pd.to_datetime(df['date'])
    
    print(f"[CURATED] Loaded {len(df)} staging records")
    return df

# %%
def create_campaigns_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Create campaigns metadata CSV (metaads_campaigns_daily.csv)"""
    
    if df.empty:
        return pd.DataFrame()
    
    # Group by campaign for metadata summary
    metadata = df.groupby(['campaign_id', 'campaign_name']).agg({
        'date': ['min', 'max'],
        'spend_usd': 'sum',
        'impressions': 'sum', 
        'clicks': 'sum',
        'reach': 'max',  # Max reach across all days
        'is_active': 'last',  # Most recent status
        'data_source': 'last',
        'api_version': 'last'
    }).round(2)
    
    # Flatten column names
    metadata.columns = ['_'.join(col).strip() if col[1] else col[0] for col in metadata.columns]
    metadata = metadata.reset_index()
    
    # Rename columns for clarity
    column_mapping = {
        'date_min': 'first_seen_date',
        'date_max': 'last_seen_date', 
        'spend_usd_sum': 'total_spend_usd',
        'impressions_sum': 'total_impressions',
        'clicks_sum': 'total_clicks',
        'reach_max': 'max_daily_reach',
        'is_active_last': 'is_currently_active',
        'data_source_last': 'data_source',
        'api_version_last': 'api_version'
    }
    
    metadata = metadata.rename(columns=column_mapping)
    
    # Add calculated metrics
    metadata['avg_cpc'] = (metadata['total_spend_usd'] / metadata['total_clicks']).round(4)
    metadata['avg_ctr'] = (metadata['total_clicks'] / metadata['total_impressions'] * 100).round(3)
    metadata['total_days_active'] = (metadata['last_seen_date'] - metadata['first_seen_date']).dt.days + 1
    
    # Handle division by zero
    metadata['avg_cpc'] = metadata['avg_cpc'].replace([float('inf'), -float('inf')], 0)
    metadata['avg_ctr'] = metadata['avg_ctr'].replace([float('inf'), -float('inf')], 0)
    
    print(f"[CURATED] Created metadata for {len(metadata)} campaigns")
    return metadata

# %%
def create_performance_log(df: pd.DataFrame) -> pd.DataFrame:
    """Create daily performance log with 28-day rolling history"""
    
    if df.empty:
        return pd.DataFrame()
    
    # Calculate 28-day cutoff from most recent date
    max_date = df['date'].max()
    cutoff_date = max_date - timedelta(days=28)
    
    print(f"[CURATED] Filtering performance data from {cutoff_date.date()} to {max_date.date()}")
    
    # Filter to last 28 days - include all campaigns that had activity in this period
    # (not just those marked as currently active)
    performance_df = df[df['date'] >= cutoff_date].copy()
    
    if performance_df.empty:
        print("[CURATED] No campaign activity in 28-day window")
        return pd.DataFrame()
    
    # Select core performance fields
    performance_columns = [
        'date', 'campaign_id', 'campaign_name', 'reach', 'cpc', 
        'spend_usd', 'impressions', 'clicks', 'pixel_events_json'
    ]
    
    performance_log = performance_df[performance_columns].copy()
    
    # Rename for clarity
    performance_log = performance_log.rename(columns={
        'pixel_events_json': 'meta_pixel_events'
    })
    
    # Sort by date and campaign for consistency
    performance_log = performance_log.sort_values(['date', 'campaign_id'])
    
    # Round numeric columns
    numeric_columns = ['reach', 'cpc', 'spend_usd', 'impressions', 'clicks']
    for col in numeric_columns:
        if col in performance_log.columns:
            performance_log[col] = performance_log[col].round(2)
    
    print(f"[CURATED] Created performance log with {len(performance_log)} daily records")
    print(f"[CURATED] Campaigns tracked: {performance_log['campaign_id'].nunique()}")
    
    # Show currently active vs inactive campaigns
    active_campaigns = performance_df['is_active'].sum()
    total_campaigns = performance_df['campaign_id'].nunique()
    print(f"[CURATED] Campaign status: {active_campaigns} currently active, {total_campaigns - active_campaigns} inactive")
    
    return performance_log

# %%
def archive_existing_files():
    """Archive existing curated files with timestamp"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    files_to_archive = [
        'metaads_campaigns_daily.csv',
        'metaads_campaigns_performance_log.csv'
    ]
    
    for filename in files_to_archive:
        file_path = CURATED_DIR / filename
        if file_path.exists():
            archive_path = ARCHIVE_DIR / f"{file_path.stem}_{timestamp}.csv"
            file_path.rename(archive_path)
            print(f"[CURATED] Archived {filename} → {archive_path.name}")

# %%
def curate_dataframes(staging_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply business rules and create both curated datasets"""
    
    if staging_df.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    # Remove duplicates based on key fields
    staging_df = staging_df.drop_duplicates(
        subset=['date', 'campaign_id'], 
        keep='last'
    )
    
    print(f"[CURATED] Processing {len(staging_df)} unique daily records")
    
    # Create both outputs
    campaigns_metadata = create_campaigns_metadata(staging_df)
    performance_log = create_performance_log(staging_df)
    
    return campaigns_metadata, performance_log

# %%
def main():
    """Main curated processing logic"""
    parser = argparse.ArgumentParser(description='Process Meta Ads data from staging to curated')
    parser.add_argument('--input', help='Specific staging file to process')
    args = parser.parse_args()
    
    print("[CURATED] Starting Meta Ads staging→curated processing...")
    
    # Load staging data
    if args.input:
        staging_file = Path(args.input)
        if not staging_file.exists():
            staging_file = STAGING_DIR / args.input
        
        if staging_file.exists():
            staging_df = pd.read_csv(staging_file, encoding='utf-8')
            staging_df['date'] = pd.to_datetime(staging_df['date'])
            print(f"[CURATED] Loaded specific file: {staging_file.name}")
        else:
            print(f"[ERROR] File not found: {staging_file}")
            return
    else:
        staging_df = load_staging_data()
    
    if staging_df.empty:
        raise RuntimeError("No staging data available for curation")
    
    # Archive existing files
    archive_existing_files()
    
    # Create curated datasets
    campaigns_metadata, performance_log = curate_dataframes(staging_df)
    
    if campaigns_metadata.empty and performance_log.empty:
        print("[WARNING] No curated data generated")
        return
    
    # Write campaigns metadata (existing file format)
    if not campaigns_metadata.empty:
        metadata_file = CURATED_DIR / "metaads_campaigns_daily.csv"
        campaigns_metadata.to_csv(metadata_file, index=False, encoding='utf-8')
        print(f"[CURATED] ✅ Wrote campaigns metadata: {metadata_file} ({len(campaigns_metadata)} campaigns)")
    
    # Write performance log (new file format)
    if not performance_log.empty:
        performance_file = CURATED_DIR / "metaads_campaigns_performance_log.csv"
        performance_log.to_csv(performance_file, index=False, encoding='utf-8')
        print(f"[CURATED] ✅ Wrote performance log: {performance_file} ({len(performance_log)} daily records)")
        
        # Show date range
        min_date = performance_log['date'].min().date()
        max_date = performance_log['date'].max().date()
        print(f"[CURATED] Performance log covers: {min_date} to {max_date}")
    
    print("[CURATED] ✅ Dual CSV curation complete")

# %%
if __name__ == "__main__":
    main()