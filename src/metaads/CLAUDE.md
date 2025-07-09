# CLAUDE.md - Meta Ads Data Pipeline

This directory contains the Meta (Facebook/Instagram) Ads data extraction and processing pipeline for comprehensive advertising analytics.

## Overview

The Meta Ads pipeline extracts campaign performance data, audience insights, and cost metrics from Facebook Ads Manager. It supports both API-based extraction and manual CSV exports, providing flexibility for different use cases and access levels.

## Directory Structure

```
metaads/
├── extractors/
│   ├── meta_raw_dump.py                    # Full campaign data via API
│   ├── meta_daily_campaigns_extractor.py   # Daily performance metrics
│   └── test_meta_extractor.py             # Testing utilities
├── cleaners/
│   ├── metaads_landing2raw.py             # JSON to NDJSON conversion
│   ├── metaads_raw2staging.py             # Data normalization
│   ├── metaads_staging2curated.py         # Analytics datasets
│   ├── metaads_daily_landing2raw.py       # Daily data processing
│   ├── metaads_daily_raw2staging.py       # Daily data cleaning
│   └── metaads_daily_staging2curated.py   # Daily aggregations
└── cookies/
    └── meta_cookies.json                   # Browser authentication
```

## Key Files

### Extractors

**meta_raw_dump.py**
- Uses Meta Marketing API for comprehensive data
- Extracts campaigns, ad sets, ads, and insights
- Handles pagination and rate limiting
- Saves nested JSON structures

**meta_daily_campaigns_extractor.py**
- Focused on daily performance metrics
- Lighter weight than full dump
- Ideal for frequent updates
- CSV export format

### Cleaners

**metaads_landing2raw.py**
- Flattens nested JSON structures
- Extracts insights from complex objects
- Converts to NDJSON line format
- Preserves all API fields

**metaads_raw2staging.py**
- Standardizes metric names
- Calculates derived metrics (CPC, CPM, CTR)
- Handles currency conversions
- Validates data quality

**metaads_staging2curated.py**
- Creates time-series analytics
- Aggregates by campaign objectives
- Calculates ROAS and efficiency metrics
- Generates performance summaries

## Common Tasks

### API-Based Extraction

```bash
cd /mnt/c/Users/Earth/BEDROT\ PRODUCTIONS/bedrot-data-ecosystem/data_lake
export PROJECT_ROOT=$(pwd)

# Set up Meta API credentials
export META_ACCESS_TOKEN="your-access-token"
export META_AD_ACCOUNT_ID="act_123456789"

# Full data dump
python src/metaads/extractors/meta_raw_dump.py

# Daily metrics only
python src/metaads/extractors/meta_daily_campaigns_extractor.py --days=7
```

### Manual CSV Processing

```bash
# Place exported CSVs in landing/
cp ~/Downloads/FacebookAds_*.csv landing/metaads/

# Process through pipeline
python src/metaads/cleaners/metaads_landing2raw.py
python src/metaads/cleaners/metaads_raw2staging.py
python src/metaads/cleaners/metaads_staging2curated.py
```

### Testing the Pipeline

```bash
# Run test extractor with sample data
python src/metaads/extractors/test_meta_extractor.py

# Validate API connection
python -m src.metaads.validators.test_api_connection
```

## Data Schema

### Campaign Level Fields
- **campaign_id**: Unique identifier
- **campaign_name**: Human-readable name
- **objective**: CONVERSIONS, TRAFFIC, etc.
- **status**: ACTIVE, PAUSED, DELETED
- **daily_budget**: Spend limit
- **lifetime_budget**: Total budget
- **start_time**: Campaign start date
- **end_time**: Campaign end date (if set)

### Performance Metrics
- **impressions**: Ad views
- **clicks**: Link clicks
- **spend**: Amount spent (USD)
- **conversions**: Goal completions
- **cpc**: Cost per click
- **cpm**: Cost per 1000 impressions
- **ctr**: Click-through rate
- **conversion_rate**: Conversions/clicks

### Audience Insights
- **reach**: Unique users reached
- **frequency**: Average views per user
- **age_range**: Demographic breakdown
- **gender**: Audience composition
- **placement**: Facebook, Instagram, etc.

## Configuration

### API Setup

1. Get Access Token:
   - Go to [Facebook Developers](https://developers.facebook.com)
   - Create app with Marketing API access
   - Generate long-lived token

2. Configure Environment:
   ```bash
   # .env file
   META_ACCESS_TOKEN=your-token-here
   META_AD_ACCOUNT_ID=act_123456789
   META_API_VERSION=v18.0
   ```

### Date Ranges
```python
# In extractors, configure default ranges:
DEFAULT_DATE_PRESET = 'last_30d'  # or 'last_7d', 'yesterday', etc.

# Custom date range:
START_DATE = '2024-01-01'
END_DATE = '2024-01-31'
```

## Rate Limiting

Meta API limits:
- 200 calls per hour per app
- 1000 calls per day per app
- Large requests count more

Best practices:
- Use field filtering to reduce response size
- Batch multiple ad accounts if needed
- Implement exponential backoff
- Cache responses when possible

## Error Handling

### Common API Errors

**Invalid Access Token**
```
Error: (#190) Invalid access token
Solution:
1. Regenerate token in Facebook Developers
2. Ensure token has ads_read permission
3. Check token expiration
```

**Rate Limit Exceeded**
```
Error: (#17) User request limit reached
Solution:
1. Wait for rate limit reset (1 hour)
2. Reduce request frequency
3. Use more specific field selections
```

**Permission Denied**
```
Error: (#10) Permission denied for ad account
Solution:
1. Verify ad account ID is correct
2. Check user has appropriate role
3. Ensure app has necessary permissions
```

## Data Quality & Validation

Automated checks:
1. **Metric Consistency**: Spend >= 0, CTR between 0-100%
2. **Date Coverage**: No gaps in daily data
3. **Currency Validation**: All amounts in USD
4. **Status Accuracy**: Only valid campaign states

Data quality queries:
```python
# Check for anomalies
df[df['cpc'] > df['spend']]  # CPC can't exceed total spend

# Verify conversions
df[df['conversions'] > df['clicks']]  # More conversions than clicks?
```

## Advanced Features

### Multi-Account Management
```python
# Process multiple ad accounts
AD_ACCOUNTS = [
    'act_123456789',
    'act_987654321'
]

for account in AD_ACCOUNTS:
    extract_account_data(account)
```

### Custom Attribution Windows
```python
# Configure attribution settings
ATTRIBUTION_WINDOWS = {
    'view': '1d',    # 1-day view
    'click': '7d'    # 7-day click
}
```

### Breakdowns and Segments
```python
# Get data by placement
BREAKDOWNS = ['placement', 'device_platform']

# Age and gender analysis
BREAKDOWNS = ['age', 'gender']
```

## Testing

### Unit Tests
```bash
pytest tests/metaads/ -v
```

### API Testing
```bash
# Test with limited data
python src/metaads/extractors/meta_raw_dump.py --test-mode --limit=10
```

### Data Validation
```bash
# Run quality checks
python src/metaads/validators/check_campaign_data.py
```

## Integration with Data Warehouse

Meta Ads data feeds these warehouse tables:
- `marketing_campaigns`: Campaign metadata
- `ad_performance`: Daily performance metrics
- `audience_insights`: Demographic data
- `attribution_data`: Conversion tracking

Example queries:
```sql
-- Campaign performance summary
SELECT 
    campaign_name,
    SUM(spend) as total_spend,
    SUM(conversions) as total_conversions,
    SUM(spend) / NULLIF(SUM(conversions), 0) as cost_per_conversion
FROM ad_performance
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY campaign_name
ORDER BY total_spend DESC;
```

## Troubleshooting

### Missing Data
- Check if campaigns were active during period
- Verify API permissions include all ad accounts
- Some metrics require specific attribution setup

### Discrepancies with Ads Manager
- API uses UTC timezone
- Attribution windows may differ
- Some metrics update with delay

### Performance Issues
- Large accounts: Use date filtering
- Reduce fields requested
- Implement parallel processing for multiple accounts

## Best Practices

1. **Regular Syncs**: Run daily for active campaigns
2. **Historical Data**: Monthly full dumps for reconciliation
3. **Field Selection**: Only request needed fields
4. **Error Logging**: Track API errors for monitoring
5. **Data Backup**: Archive raw API responses

## Manual Export Processing

When API access is limited:

1. Export from Ads Manager:
   - Go to Ads Manager > Reports
   - Select "Export Table Data"
   - Choose CSV format
   - Include all available metrics

2. Process exports:
   ```bash
   # Place in landing folder
   cp ~/Downloads/FacebookAds*.csv landing/metaads/
   
   # Run manual pipeline
   python src/metaads/cleaners/metaads_manual_csv_processor.py
   ```

## Future Enhancements

Planned features:
- [ ] Real-time webhook integration
- [ ] Automated budget optimization
- [ ] Cross-platform attribution (with Google Ads)
- [ ] Creative performance analysis
- [ ] Audience overlap detection
- [ ] Predictive campaign modeling
- [ ] Automated reporting via email/Slack