# Meta Ads Daily Campaign Data - Raw to Staging Zone Cleaner
# Converts NDJSON daily campaign records to staging CSV format
# Guided by LLM_cleaner_guidelines.md

# %%
import json
import os
from datetime import datetime
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
import argparse

# %%
load_dotenv()
PROJECT_ROOT = Path(os.environ["PROJECT_ROOT"])
RAW_DIR = PROJECT_ROOT / "raw" / "metaads"
STAGING_DIR = PROJECT_ROOT / "staging" / "metaads"
STAGING_DIR.mkdir(parents=True, exist_ok=True)

# %%
def record_to_row(record: dict) -> dict:
    """Convert raw NDJSON record to staging CSV row"""
    
    # Extract metrics
    metrics = record.get('metrics', {})
    pixel_events = record.get('pixel_events', {})
    
    # Flatten pixel events to individual columns
    row = {
        'date': record.get('date'),
        'campaign_id': record.get('campaign_id'),
        'campaign_name': record.get('campaign_name'),
        'adset_id': record.get('adset_id'),
        'reach': float(metrics.get('reach', 0)),
        'cpc': float(metrics.get('cpc', 0)),
        'spend_usd': float(metrics.get('spend_usd', 0)),
        'clicks': int(metrics.get('clicks', 0)),
        'impressions': int(metrics.get('impressions', 0)),
        'is_active': bool(record.get('is_active', False)),
        'extraction_date': record.get('extraction_date'),
        'data_source': record.get('data_source'),
        'api_version': record.get('api_version')
    }
    
    # Add pixel event columns
    common_events = [
        'ViewContent', 'AddToCart', 'Purchase', 'InitiateCheckout', 
        'AddPaymentInfo', 'Lead', 'CompleteRegistration', 
        'LinkClick', 'PostEngagement', 'MessagingStarted'
    ]
    
    for event in common_events:
        row[f'pixel_{event.lower()}'] = int(pixel_events.get(event, 0))
    
    # Store full pixel events as JSON for reference
    row['pixel_events_json'] = json.dumps(pixel_events) if pixel_events else '{}'
    
    return row

# %%
def process_raw_files() -> pd.DataFrame:
    """Process all raw NDJSON files and build staging DataFrame"""
    
    ndjson_files = list(RAW_DIR.glob("metaads_campaign_daily_*_raw_*.ndjson"))
    
    if not ndjson_files:
        print(f"[STAGING] No raw NDJSON files found in {RAW_DIR}")
        return pd.DataFrame()
    
    print(f"[STAGING] Found {len(ndjson_files)} raw files to process")
    
    all_rows = []
    
    for ndjson_file in sorted(ndjson_files):
        print(f"[STAGING] Processing {ndjson_file.name}")
        
        try:
            with open(ndjson_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        record = json.loads(line.strip())
                        row = record_to_row(record)
                        all_rows.append(row)
                    except json.JSONDecodeError as e:
                        print(f"[ERROR] Invalid JSON on line {line_num} in {ndjson_file.name}: {e}")
                        continue
                    except Exception as e:
                        print(f"[ERROR] Failed to process line {line_num} in {ndjson_file.name}: {e}")
                        continue
        except Exception as e:
            print(f"[ERROR] Failed to read {ndjson_file.name}: {e}")
            continue
    
    if not all_rows:
        return pd.DataFrame()
    
    # Create DataFrame and ensure data types
    df = pd.DataFrame(all_rows)
    
    # Convert date columns
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['extraction_date'] = pd.to_datetime(df['extraction_date'], errors='coerce')
    
    # Ensure numeric columns
    numeric_cols = ['reach', 'cpc', 'spend_usd', 'clicks', 'impressions']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Ensure pixel event columns are integers
    pixel_cols = [col for col in df.columns if col.startswith('pixel_') and col != 'pixel_events_json']
    for col in pixel_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    
    # Deduplicate on key fields
    df = df.drop_duplicates(subset=['date', 'campaign_id', 'adset_id'], keep='last')
    
    print(f"[STAGING] Built DataFrame with {len(df)} records")
    return df

# %%
def main():
    """Main processing logic with CLI support"""
    parser = argparse.ArgumentParser(description='Process Meta Ads daily campaign data from raw to staging')
    parser.add_argument('--out', help='Custom output CSV path')
    args = parser.parse_args()
    
    # Process raw files
    df = process_raw_files()
    
    if df.empty:
        raise RuntimeError("No records processed - check raw NDJSON files")
    
    # Generate output filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if args.out:
        output_file = Path(args.out)
    else:
        output_file = STAGING_DIR / f"metaads_daily_campaigns_staging_{timestamp}.csv"
    
    # Write staging CSV
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"[STAGING] ✅ Wrote {len(df)} records to {output_file}")
    
    # Show summary stats
    print(f"[STAGING] Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"[STAGING] Unique campaigns: {df['campaign_id'].nunique()}")
    print(f"[STAGING] Total spend: ${df['spend_usd'].sum():.2f}")
    print(f"[STAGING] Total impressions: {df['impressions'].sum():,}")
    print(f"[STAGING] Active campaigns: {df['is_active'].sum()}")

# %%
if __name__ == "__main__":
    main()