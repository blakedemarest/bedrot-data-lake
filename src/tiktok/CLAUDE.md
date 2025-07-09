# CLAUDE.md - TikTok Data Pipeline

This directory contains the TikTok analytics extraction and processing pipeline, supporting multiple TikTok accounts and comprehensive engagement metrics.

## Overview

The TikTok pipeline extracts analytics data from TikTok for Business accounts, including video performance, audience demographics, and engagement metrics. It supports multiple accounts and handles the unique challenges of TikTok's dynamic web interface.

## Directory Structure

```
tiktok/
├── extractors/
│   ├── tiktok_analytics_extractor_pig1987.py  # Account-specific extractor
│   └── tiktok_analytics_extractor_zonea0.py   # Account-specific extractor
├── cleaners/
│   ├── tiktok_landing2raw.py                  # ZIP to CSV/NDJSON conversion
│   ├── tiktok_raw2staging.py                  # Data cleaning and validation
│   └── tiktok_staging2curated.py              # Final analytics dataset
├── cookies/
│   └── tiktok_cookies_<account>.json          # Per-account authentication
└── utilities/
    ├── test_enhanced_pipeline.py              # Pipeline testing
    └── migrate_reach_to_views.py              # Schema migration tool
```

## Key Files

### Extractors

**tiktok_analytics_extractor_<account>.py**
- Downloads analytics exports from TikTok for Business
- Handles ZIP file downloads containing CSV data
- Manages authentication per account
- Implements retry logic for flaky downloads

### Cleaners

**tiktok_landing2raw.py**
- Extracts CSV files from downloaded ZIPs
- Validates data structure and headers
- Converts to NDJSON with metadata
- Handles multiple report types (Overview, Content, etc.)

**tiktok_raw2staging.py**
- Standardizes column names across report versions
- Cleans engagement metrics (views, likes, shares)
- Calculates engagement rates and ratios
- Handles TikTok's changing schema gracefully

**tiktok_staging2curated.py**
- Aggregates metrics by time period
- Calculates growth trends and viral coefficients
- Merges data from multiple accounts
- Creates unified analytics view

## Common Tasks

### Extracting Analytics Data

```bash
cd /mnt/c/Users/Earth/BEDROT\ PRODUCTIONS/bedrot-data-ecosystem/data_lake
export PROJECT_ROOT=$(pwd)

# Extract for specific account
python src/tiktok/extractors/tiktok_analytics_extractor_pig1987.py

# Extract for all configured accounts
for account in pig1987 zonea0; do
    python src/tiktok/extractors/tiktok_analytics_extractor_${account}.py
done
```

### Processing Downloaded Data

```bash
# Process all ZIP files in landing
python src/tiktok/cleaners/tiktok_landing2raw.py

# Clean and standardize
python src/tiktok/cleaners/tiktok_raw2staging.py

# Create final dataset
python src/tiktok/cleaners/tiktok_staging2curated.py
```

### Account Management

Add a new TikTok account:
1. Create new extractor script:
   ```bash
   cp src/tiktok/extractors/tiktok_analytics_extractor_pig1987.py \
      src/tiktok/extractors/tiktok_analytics_extractor_newaccount.py
   ```

2. Update account credentials in the new script

3. Run authentication flow:
   ```bash
   python src/tiktok/extractors/tiktok_analytics_extractor_newaccount.py --headless=False
   ```

## Data Schema

### Core Metrics (Overview Report)
- **date**: Activity date
- **video_views**: Total views (formerly "reach")
- **profile_views**: Profile page visits
- **likes**: Total likes received
- **comments**: Total comments
- **shares**: Total shares
- **followers**: Current follower count
- **following**: Accounts being followed

### Content Performance
- **video_id**: Unique video identifier
- **publish_date**: When video was posted
- **total_views**: Lifetime views
- **average_watch_time**: In seconds
- **completion_rate**: % who watched to end
- **engagement_rate**: (likes + comments + shares) / views

### Audience Demographics
- **age_range**: Age distribution
- **gender**: Gender breakdown
- **top_territories**: Geographic data
- **active_times**: When audience is online

## Configuration

### Environment Variables
```bash
# Override default paths
TIKTOK_LANDING_PATH=/custom/landing/path
TIKTOK_ACCOUNTS=pig1987,zonea0,newaccount

# Set download timeout (seconds)
TIKTOK_DOWNLOAD_TIMEOUT=60
```

### Account Configuration
Each account extractor contains:
```python
ACCOUNT_CONFIG = {
    "username": "account_name",
    "business_id": "1234567890",
    "default_date_range": 28  # days
}
```

## Rate Limiting & Best Practices

TikTok analytics has these limitations:
- Export frequency: Max 1 per hour per account
- Date ranges: Max 180 days per export
- File availability: Downloads expire after 1 hour

Best practices:
- Space out multi-account extractions by 5+ minutes
- Download immediately after export generation
- Use specific date ranges to avoid large files
- Implement checkpoints for long-running extractions

## Error Handling

### Common Issues

**Download Failed**
```
Error: Download did not start within timeout
Solution: 
1. Check if export was actually generated
2. Increase timeout in script
3. Verify download permissions in browser
```

**Schema Changes**
```
Error: Column 'reach' not found, found 'video_views' instead
Solution: Run migration script:
python src/tiktok/migrate_reach_to_views.py
```

**Authentication Expired**
```
Error: Could not find analytics tab
Solution:
1. Delete cookies file
2. Run extractor with --headless=False
3. Complete 2FA if required
```

## Data Quality & Validation

The pipeline validates:
1. **Metric Consistency**: Views ≥ Likes + Comments + Shares
2. **Date Continuity**: No gaps in daily data
3. **Follower Trends**: Reasonable growth patterns
4. **Engagement Rates**: Within 0-100% bounds

Anomaly detection flags:
- Sudden follower drops (>10% daily)
- Engagement rate outliers
- Missing data for active periods
- Duplicate entries

## Testing

### Unit Tests
```bash
pytest tests/tiktok/ -v
```

### Pipeline Testing
```bash
# Test with sample data
python src/tiktok/test_enhanced_pipeline.py

# Test specific account
python src/tiktok/test_enhanced_pipeline.py --account=pig1987
```

### Data Validation
```python
# Run built-in diagnostics
python -c "
from src.tiktok.cleaners.tiktok_staging2curated import validate_staging_data
validate_staging_data('staging/tiktok/tiktok_metrics_*.csv')
"
```

## Advanced Features

### Follower Network Analysis
Experimental feature for competitor tracking:
```bash
python src/tiktok/test_follower_network_discovery.py
```

### Multi-Account Aggregation
Combine metrics across accounts:
```python
from src.tiktok.cleaners.tiktok_staging2curated import aggregate_accounts

aggregate_accounts(
    accounts=['pig1987', 'zonea0'],
    output_path='curated/tiktok_combined.csv'
)
```

### Trend Detection
Identify viral content patterns:
```python
from src.tiktok.analytics import detect_viral_trends

trends = detect_viral_trends(
    min_views=10000,
    growth_threshold=5.0  # 5x daily growth
)
```

## Integration with Data Warehouse

TikTok data feeds these warehouse tables:
- `social_media_stats`: Platform-level metrics
- `content_performance`: Individual video analytics
- `viral_content`: High-performing content tracking
- `audience_insights`: Demographic breakdowns

## Troubleshooting

### Browser Automation
- Update Playwright: `playwright install --with-deps chromium`
- Check TikTok UI changes with browser inspector
- Use screenshots for debugging: `--screenshot-on-error`

### Large File Handling
- For exports >100MB, increase memory limits
- Consider streaming processing with chunks
- Archive old landing files after processing

### Cross-Account Discrepancies
- Verify timezone settings (TikTok uses account timezone)
- Check for different report versions
- Ensure consistent date range selection

## Schema Migration

When TikTok changes column names:
```bash
# Check current schema
python -m src.tiktok.schema_checker

# Apply migrations
python src/tiktok/migrate_reach_to_views.py
```

## Future Enhancements

Planned features:
- [ ] Real-time API integration (when available)
- [ ] Competitor benchmarking
- [ ] Content recommendation engine
- [ ] Automated posting optimization
- [ ] Hashtag performance tracking
- [ ] Creator marketplace integration