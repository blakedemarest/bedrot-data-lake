# CLAUDE.md - DistroKid Data Pipeline

This directory contains the DistroKid data extraction and processing pipeline for streaming statistics and financial data from the music distribution platform.

## Overview

The DistroKid pipeline extracts comprehensive streaming data and earnings information across all major platforms (Spotify, Apple Music, YouTube, etc.) as well as detailed financial transactions. This data is critical for tracking music performance and revenue.

## Directory Structure

```
distrokid/
├── extractors/
│   └── dk_auth.py                    # Main DistroKid scraper with auth
├── cleaners/
│   ├── distrokid_landing2raw.py     # HTML/TSV to structured format
│   ├── distrokid_raw2staging.py     # Clean and normalize data
│   └── distrokid_staging2curated.py # Create analytics datasets
└── cookies/
    └── distrokid_cookies.json        # Saved authentication
```

## Key Files

### Extractors

**dk_auth.py**
- Handles DistroKid login with 2FA support
- Downloads streaming stats pages (HTML)
- Downloads bank/earnings data (TSV)
- Manages session persistence
- Implements careful rate limiting

### Cleaners

**distrokid_landing2raw.py**
- Parses HTML streaming reports using BeautifulSoup
- Converts TSV financial data to CSV
- Extracts data from complex nested tables
- Validates data completeness

**distrokid_raw2staging.py**
- Standardizes platform names (e.g., "Apple Music" vs "iTunes")
- Normalizes date formats across reports
- Cleans monetary values (handles multiple currencies)
- Calculates USD equivalents for foreign earnings

**distrokid_staging2curated.py**
- Aggregates streaming data by platform and time period
- Calculates total earnings and payment timelines
- Creates unified view across all platforms
- Generates summary statistics and trends

## Common Tasks

### Extracting Data

```bash
cd /mnt/c/Users/Earth/BEDROT\ PRODUCTIONS/bedrot-data-ecosystem/data_lake
export PROJECT_ROOT=$(pwd)

# Run with visible browser for first-time auth
python src/distrokid/extractors/dk_auth.py --headless=False

# Normal automated extraction
python src/distrokid/extractors/dk_auth.py
```

### Processing Pipeline

```bash
# Convert HTML/TSV to structured format
python src/distrokid/cleaners/distrokid_landing2raw.py

# Clean and standardize
python src/distrokid/cleaners/distrokid_raw2staging.py

# Create final datasets
python src/distrokid/cleaners/distrokid_staging2curated.py
```

### Handling Multiple Artists

If distributing for multiple artists:
```python
# In dk_auth.py, configure:
ARTIST_PAGES = [
    "/artist/stats/artist1",
    "/artist/stats/artist2"
]
```

## Data Schema

### Streaming Data Fields
- **date**: Reporting date (YYYY-MM-DD)
- **platform**: Service name (Spotify, Apple Music, etc.)
- **track_title**: Song name
- **artist**: Artist name
- **album**: Album/single name
- **streams**: Play count
- **revenue**: Earnings in reporting currency
- **revenue_usd**: Converted to USD
- **territory**: Country/region code

### Financial Data Fields
- **transaction_date**: When payment was made
- **reporting_period**: Month/year of streams
- **platform**: Source platform
- **gross_revenue**: Total earnings
- **distrokid_fee**: Distribution fee
- **net_revenue**: Amount paid out
- **payment_method**: Bank transfer, PayPal, etc.
- **payment_status**: Pending, Paid, Processing

### Derived Metrics
- **revenue_per_stream**: Average payout rate
- **platform_share**: % of total streams per platform
- **growth_rate**: Month-over-month change
- **payout_delay**: Days from earning to payment

## Configuration

### Environment Variables
```bash
# DistroKid credentials (optional, can use saved session)
DISTROKID_EMAIL=your-email@example.com
DISTROKID_PASSWORD=your-password  # Only for initial setup

# Custom paths
DISTROKID_LANDING_PATH=/custom/landing/path
```

### Platform Mapping
Edit `src/distrokid/cleaners/distrokid_raw2staging.py`:
```python
PLATFORM_MAPPING = {
    "Apple Music": "apple_music",
    "iTunes": "apple_music",  # Consolidate variants
    "Spotify": "spotify",
    "YouTube Music": "youtube_music",
    # Add custom mappings as needed
}
```

## Authentication & Security

### Initial Setup
1. Run extractor with visible browser
2. Log in manually (handle 2FA if enabled)
3. Cookies are automatically saved
4. Delete password from environment

### Session Management
- Sessions typically last 30 days
- Script auto-detects expired sessions
- Re-authentication preserves existing cookies
- Never store passwords in code

## Rate Limiting

DistroKid's unofficial limits:
- Page loads: ~1 per 2-3 seconds
- Data exports: No hard limit
- Session duration: 30 days
- Concurrent sessions: 1 recommended

The extractor implements:
- Random delays (2-5 seconds) between requests
- Exponential backoff on errors
- Maximum 3 retry attempts
- Graceful failure handling

## Error Handling

### Common Issues

**Login Failed**
```
Error: Could not find stats page after login
Solution:
1. Check if DistroKid changed their UI
2. Verify credentials are correct
3. Handle any new security prompts
```

**Incomplete Data**
```
Error: Missing streaming data for [month]
Solution:
1. Check if data is available on DistroKid yet
2. Verify date range in extractor
3. Look for platform-specific delays
```

**Currency Conversion**
```
Error: Unknown currency code: XXX
Solution: Add to CURRENCY_RATES in raw2staging.py
```

## Data Quality Checks

Automated validations:
1. **Completeness**: All expected platforms present
2. **Consistency**: Stream counts are non-negative
3. **Accuracy**: Revenue calculations match totals
4. **Timeliness**: Data includes recent periods

Manual checks:
- Compare totals with DistroKid dashboard
- Verify high-value transactions
- Check for missing platforms
- Validate currency conversions

## Testing

### Unit Tests
```bash
pytest tests/distrokid/ -v
```

### Integration Tests
```bash
# Test with sample HTML file
cp tests/fixtures/dk_sample.html landing/distrokid/streams/
python src/distrokid/cleaners/distrokid_landing2raw.py --test-mode
```

### Validation Scripts
```bash
# Check data quality
python src/distrokid/validators/check_streaming_data.py

# Verify financial reconciliation
python src/distrokid/validators/reconcile_payments.py
```

## Advanced Usage

### Historical Data Import
For bulk historical imports:
```bash
# Place exported files in landing/
cp ~/Downloads/distrokid_export_*.html landing/distrokid/streams/

# Process all at once
python src/distrokid/cleaners/distrokid_landing2raw.py --process-all
```

### Multi-Currency Handling
```python
# Configure additional currencies
CURRENCY_RATES = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.25,
    "JPY": 0.0067,
    # Add more as needed
}
```

### Platform-Specific Extraction
Extract data for specific platforms only:
```python
# In staging2curated.py
df_filtered = df[df['platform'].isin(['spotify', 'apple_music'])]
```

## Integration with Data Warehouse

DistroKid data feeds these warehouse tables:
- `streaming_data`: Core streaming metrics
- `financial_transactions`: Payment records
- `platform_performance`: Platform comparisons
- `revenue_forecasts`: Projected earnings

SQL example:
```sql
-- Monthly revenue by platform
SELECT 
    platform,
    DATE_TRUNC('month', date) as month,
    SUM(streams) as total_streams,
    SUM(revenue_usd) as total_revenue
FROM streaming_data
WHERE source = 'distrokid'
GROUP BY platform, month
ORDER BY month DESC, total_revenue DESC;
```

## Troubleshooting

### Missing Platforms
- Some platforms report on different schedules
- Check DistroKid's "Excruciating Details" page
- Historical data may be incomplete

### Data Discrepancies
- DistroKid updates historical data occasionally
- Compare with platform-native analytics
- Check timezone differences

### Performance Issues
- Large catalogs may timeout - increase wait times
- Consider splitting by date ranges
- Archive old HTML files after processing

## Best Practices

1. **Regular Extraction**: Run weekly to catch updates
2. **Backup Raw Files**: Keep landing/ files for reprocessing
3. **Monitor Changes**: DistroKid updates UI frequently
4. **Validate Totals**: Cross-check with bank deposits
5. **Track Anomalies**: Flag unusual spikes/drops

## Future Enhancements

Planned improvements:
- [ ] API integration (if DistroKid releases one)
- [ ] Automated reconciliation with bank statements
- [ ] Playlist tracking integration
- [ ] Rights management data extraction
- [ ] Automated report generation
- [ ] Multi-distributor consolidation