# Meta Ads Data Pipeline

This module extracts and processes Meta (Facebook/Instagram) advertising data through the Facebook Marketing API.

## Extractors

### `meta_raw_dump.py` (Legacy)
- Dumps campaigns, ad sets, ads, and insights from Meta Ads API
- Creates timestamped folders in `landing/metaads/`
- Uses Facebook Marketing API v19.0
- Outputs: `campaigns.json`, `adsets.json`, `ads.json`, `insights.json`

### `meta_daily_campaigns_extractor.py` (Enhanced)
- **New daily-level performance extractor** with campaign activity tracking
- Collects daily reach, CPC, spend, clicks, impressions per campaign
- Extracts and aggregates Meta Pixel events (ViewContent, AddToCart, Purchase, etc.)
- Uses Facebook Marketing API v18.0+ with robust error handling and rate limit retry
- **Campaign Activity Management:**
  - SQLite cache tracks campaign activity status
  - Excludes campaigns inactive for 7+ consecutive days
  - Automatic activity detection and cache updates
- Outputs: `metaads_campaign_daily_YYYYMMDD_HHMMSS.csv`

## Cleaners

### Legacy Pipeline
- `metaads_landing2raw.py` - Processes JSON dumps from landing zone
- `metaads_raw2staging.py` - Consolidates raw dumps, outputs `tidy_metaads.csv` 
- `metaads_staging2curated.py` - Final curated output

### Enhanced Daily Pipeline
- `metaads_daily_landing2raw.py` - Processes daily campaign CSV to NDJSON
- `metaads_daily_raw2staging.py` - Converts to staging CSV with pixel event columns
- `metaads_daily_staging2curated.py` - Creates dual CSV outputs in curated/

### Curated Outputs (Both in curated/metaads/)

**1. `metaads_campaigns_daily.csv` - Campaign Metadata**
- Campaign-level summary statistics and metadata
- Fields: campaign_id, campaign_name, total_spend_usd, total_impressions, total_clicks, max_daily_reach, is_currently_active, avg_cpc, avg_ctr, etc.
- One record per campaign with aggregated lifetime metrics

**2. `metaads_campaigns_performance_log.csv` - Daily Performance Log**  
- Daily performance metrics with 28-day rolling history
- Fields: date, campaign_id, campaign_name, reach, cpc, spend_usd, impressions, clicks, meta_pixel_events
- One record per campaign per day for active campaigns
- Automatically maintains 28-day sliding window
- Includes JSON-formatted Meta Pixel events (ViewContent, AddToCart, Purchase, etc.)

## Environment Variables

Required in `.env`:
```
META_ACCESS_TOKEN=your_meta_access_token
META_AD_ACCOUNT_ID=act_your_account_id
PROJECT_ROOT=/path/to/data_lake
```

## Usage

### Enhanced Daily Extraction (Recommended)
```bash
# Extract daily campaign performance with pixel events
python src/metaads/extractors/meta_daily_campaigns_extractor.py

# Process through zones to create dual CSV outputs
python src/metaads/cleaners/metaads_daily_landing2raw.py
python src/metaads/cleaners/metaads_daily_raw2staging.py
python src/metaads/cleaners/metaads_daily_staging2curated.py
```

### Legacy Full Dump
```bash
# Run full extraction and cleaning pipeline
python src/metaads/extractors/meta_raw_dump.py
python src/metaads/cleaners/metaads_landing2raw.py
python src/metaads/cleaners/metaads_raw2staging.py
python src/metaads/cleaners/metaads_staging2curated.py
```

## Campaign Activity Tracking

The enhanced extractor maintains a SQLite database (`src/metaads/cache/campaign_activity.db`) to track:
- Last active date per campaign  
- Consecutive inactive days
- Active/inactive status

Campaigns with no data for 7+ days are automatically excluded from future API calls to improve efficiency and reduce API quota usage.
