# Meta Ads Daily Campaign Data - Landing to Raw Zone Cleaner
# Processes daily campaign performance CSV files from the enhanced extractor
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
LANDING_DIR = PROJECT_ROOT / "landing" / "metaads"
RAW_DIR = PROJECT_ROOT / "raw" / "metaads"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# %%
def transform_daily_campaign_record(row: pd.Series) -> dict:
    """Transform daily campaign CSV row to standardized raw format"""
    
    # Parse pixel events JSON safely
    try:
        pixel_events = json.loads(row.get('meta_pixel_events', '{}'))
    except (json.JSONDecodeError, TypeError):
        pixel_events = {}
    
    # Standardize record structure
    record = {
        'extraction_date': datetime.now().isoformat(),
        'date': row.get('date'),
        'campaign_id': str(row.get('campaign_id', '')),
        'campaign_name': str(row.get('campaign_name', '')),
        'adset_id': str(row.get('adset_id', '')) if pd.notna(row.get('adset_id')) else None,
        'metrics': {
            'reach': float(row.get('reach', 0)),
            'cpc': float(row.get('cpc', 0)),
            'spend_usd': float(row.get('spend_usd', 0)),
            'clicks': int(row.get('clicks', 0)),
            'impressions': int(row.get('impressions', 0))
        },
        'pixel_events': pixel_events,
        'is_active': bool(row.get('is_active', False)),
        'data_source': 'meta_daily_campaigns_extractor',
        'api_version': 'v18.0'
    }
    
    return record

# %%
def process_daily_campaign_file(file_path: Path) -> int:
    """Process single daily campaign CSV file"""
    print(f"[RAW] Processing {file_path.name}")
    
    try:
        # Read CSV
        df = pd.read_csv(file_path, encoding='utf-8')
        
        if df.empty:
            print(f"[RAW] Empty file: {file_path.name}")
            return 0
        
        # Generate output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        stem = file_path.stem
        output_file = RAW_DIR / f"{stem}_raw_{timestamp}.ndjson"
        
        # Transform and write records
        records_written = 0
        with open(output_file, 'w', encoding='utf-8') as f:
            for _, row in df.iterrows():
                try:
                    record = transform_daily_campaign_record(row)
                    f.write(json.dumps(record) + '\n')
                    records_written += 1
                except Exception as e:
                    print(f"[ERROR] Failed to transform row: {e}")
                    continue
        
        print(f"[RAW] Wrote {records_written} records to {output_file.name}")
        return records_written
        
    except Exception as e:
        print(f"[ERROR] Failed to process {file_path.name}: {e}")
        return 0

# %%
def main():
    """Main processing logic with CLI support"""
    parser = argparse.ArgumentParser(description='Process Meta Ads daily campaign data from landing to raw')
    parser.add_argument('--file', help='Process specific file')
    args = parser.parse_args()
    
    total_records = 0
    
    if args.file:
        # Process single file
        file_path = Path(args.file)
        if not file_path.exists():
            file_path = LANDING_DIR / args.file
        
        if file_path.exists() and file_path.suffix == '.csv':
            total_records += process_daily_campaign_file(file_path)
        else:
            print(f"[ERROR] File not found or not CSV: {file_path}")
    else:
        # Process all daily campaign CSV files in landing
        csv_files = list(LANDING_DIR.glob("metaads_campaign_daily_*.csv"))
        
        if not csv_files:
            print(f"[INFO] No daily campaign CSV files found in {LANDING_DIR}")
            return
        
        print(f"[RAW] Found {len(csv_files)} daily campaign files to process")
        
        for csv_file in sorted(csv_files):
            total_records += process_daily_campaign_file(csv_file)
    
    if total_records == 0:
        raise RuntimeError("No records processed - check input files")
    
    print(f"[RAW] ✅ Daily campaign processing complete: {total_records} total records")

# %%
if __name__ == "__main__":
    main()