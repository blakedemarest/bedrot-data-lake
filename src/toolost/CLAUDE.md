# CLAUDE.md - TooLost Data Pipeline

This directory contains the TooLost streaming aggregator data extraction and processing pipeline, which consolidates streaming data from multiple platforms.

## Overview

TooLost provides aggregated streaming analytics across Spotify, Apple Music, and other platforms. The pipeline extracts unified streaming metrics, helping track overall music performance without needing to access each platform individually.

## Directory Structure

```
toolost/
├── extractors/
│   └── toolost_scraper.py              # Main TooLost data extractor
├── cleaners/
│   ├── toolost_landing2raw.py         # JSON to structured format
│   ├── toolost_raw2staging.py         # Data cleaning and validation
│   └── toolost_staging2curated.py     # Final analytics dataset
└── cookies/
    └── toolost_cookies.json            # Saved authentication
```

## Key Files

### Extractors

**toolost_scraper.py**
- Authenticates with TooLost platform
- Downloads streaming data for all connected platforms
- Handles both API responses and web scraping
- Manages rate limiting and retries

### Cleaners

**toolost_landing2raw.py**
- Parses JSON responses from TooLost
- Validates data structure and completeness
- Converts to NDJSON format
- Adds metadata and timestamps

**toolost_raw2staging.py**
- Standardizes platform identifiers
- Normalizes date formats across sources
- Calculates aggregate metrics
- Handles missing or null values

**toolost_staging2curated.py**
- Creates unified streaming view
- Calculates platform market share
- Generates growth trends
- Produces comparison analytics

## Common Tasks

### Data Extraction

```bash
cd /mnt/c/Users/Earth/BEDROT\ PRODUCTIONS/bedrot-data-ecosystem/data_lake
export PROJECT_ROOT=$(pwd)

# Run extractor
python src/toolost/extractors/toolost_scraper.py

# Extract specific date range
python src/toolost/extractors/toolost_scraper.py --start-date=2024-01-01 --end-date=2024-01-31
```

### Processing Pipeline

```bash
# Process downloaded data
python src/toolost/cleaners/toolost_landing2raw.py

# Clean and validate
python src/toolost/cleaners/toolost_raw2staging.py

# Create final dataset
python src/toolost/cleaners/toolost_staging2curated.py
```

## Data Schema

### Streaming Metrics
- **date**: Reporting date (YYYY-MM-DD)
- **platform**: Streaming service name
- **track_id**: TooLost internal track ID
- **track_title**: Song name
- **artist**: Artist name
- **streams**: Play count for period
- **listeners**: Unique listener count
- **saves**: Playlist adds/favorites
- **skip_rate**: Percentage of skips

### Platform Coverage
- **spotify**: Spotify streams and saves
- **apple_music**: Apple Music plays
- **youtube_music**: YouTube Music streams
- **amazon_music**: Amazon Music plays
- **deezer**: Deezer streams
- **tidal**: Tidal plays

### Aggregated Metrics
- **total_streams**: Sum across all platforms
- **platform_distribution**: JSON object with percentages
- **growth_rate**: Period-over-period change
- **market_penetration**: Platforms with activity

## Configuration

### Environment Variables
```bash
# TooLost credentials
TOOLOST_EMAIL=your-email@example.com
TOOLOST_API_KEY=your-api-key  # If available

# Data settings
TOOLOST_SYNC_DAYS=90  # Days of historical data
TOOLOST_PLATFORMS=spotify,apple_music,youtube_music
```

### Platform Mapping
Configure in `toolost_raw2staging.py`:
```python
PLATFORM_NORMALIZATION = {
    "Spotify": "spotify",
    "Apple Music": "apple_music",
    "YouTube Music": "youtube_music",
    "iTunes": "apple_music",  # Legacy naming
}
```

## Authentication

### API Key Method
```python
# If TooLost provides API access
headers = {
    'Authorization': f'Bearer {API_KEY}',
    'X-API-Version': '2.0'
}
```

### Cookie-Based Auth
```bash
# Initial setup with browser
python src/toolost/extractors/toolost_scraper.py --setup

# Cookies saved automatically to cookies/toolost_cookies.json
```

## Rate Limiting

TooLost guidelines:
- API calls: 100 per hour (if using API)
- Web requests: Respectful scraping
- Data exports: No explicit limit
- Concurrent requests: Not recommended

Implementation:
```python
# Rate limiting decorator
@rate_limit(calls=10, period=60)  # 10 calls per minute
def fetch_streaming_data(date_range):
    # Implementation
    pass
```

## Error Handling

### Common Issues

**Authentication Failed**
```
Error: Login credentials invalid
Solution:
1. Verify email/password correct
2. Check if account is active
3. Handle any 2FA requirements
```

**Incomplete Platform Data**
```
Error: Missing data for platform: apple_music
Solution:
1. Verify platform is connected in TooLost
2. Check if data is available for date range
3. Platform might have reporting delays
```

**Rate Limit Hit**
```
Error: 429 Too Many Requests
Solution:
1. Implement exponential backoff
2. Reduce request frequency
3. Cache responses when possible
```

## Data Validation

### Quality Checks
```python
def validate_streaming_data(df):
    checks = {
        'non_negative_streams': (df['streams'] >= 0).all(),
        'valid_dates': pd.to_datetime(df['date'], errors='coerce').notna().all(),
        'platform_coverage': df['platform'].nunique() >= 2,
        'no_duplicates': not df.duplicated(['date', 'track_id', 'platform']).any()
    }
    return all(checks.values()), checks
```

### Cross-Platform Validation
```python
# Compare with direct platform data
def cross_validate_streams(toolost_df, spotify_df):
    merged = pd.merge(
        toolost_df[toolost_df['platform'] == 'spotify'],
        spotify_df,
        on=['date', 'track_title'],
        suffixes=('_toolost', '_direct')
    )
    
    # Calculate variance
    merged['variance'] = abs(
        merged['streams_toolost'] - merged['streams_direct']
    ) / merged['streams_direct']
    
    return merged['variance'].mean()
```

## Testing

### Unit Tests
```bash
pytest tests/toolost/ -v
```

### Mock Data Testing
```python
# Create test fixtures
def create_mock_toolost_response():
    return {
        "data": [{
            "date": "2024-01-15",
            "platform": "spotify",
            "streams": 1000,
            "track": "Test Song"
        }],
        "meta": {
            "total_platforms": 3,
            "date_range": "2024-01-01 to 2024-01-31"
        }
    }
```

## Advanced Usage

### Multi-Artist Handling
```python
# If managing multiple artists
ARTIST_ACCOUNTS = [
    {"email": "artist1@example.com", "id": "123"},
    {"email": "artist2@example.com", "id": "456"}
]

for account in ARTIST_ACCOUNTS:
    extract_artist_data(account)
```

### Historical Data Import
```python
# Bulk import historical data
def import_historical_data(start_year=2020):
    for year in range(start_year, datetime.now().year + 1):
        for month in range(1, 13):
            extract_monthly_data(year, month)
            time.sleep(60)  # Rate limiting
```

### Platform Comparison
```python
# Analyze platform performance
def compare_platforms(df):
    platform_stats = df.groupby('platform').agg({
        'streams': ['sum', 'mean'],
        'listeners': 'sum',
        'skip_rate': 'mean'
    })
    
    platform_stats['efficiency'] = (
        platform_stats[('listeners', 'sum')] / 
        platform_stats[('streams', 'sum')]
    )
    
    return platform_stats
```

## Integration Points

### Data Warehouse
TooLost data feeds into:
- `streaming_data`: Core streaming table
- `platform_comparison`: Cross-platform analytics
- `streaming_aggregated`: Combined metrics

### Reconciliation
```sql
-- Compare TooLost with direct platform data
SELECT 
    t.date,
    t.platform,
    t.streams as toolost_streams,
    d.streams as direct_streams,
    ABS(t.streams - d.streams) / d.streams as variance
FROM toolost_staging t
JOIN direct_platform_data d 
    ON t.date = d.date 
    AND t.platform = d.platform
WHERE variance > 0.05;  -- Flag >5% variance
```

## Monitoring

### Health Checks
```python
def check_toolost_health():
    latest_data = get_latest_extraction_date()
    days_behind = (datetime.now() - latest_data).days
    
    return {
        'data_freshness': days_behind <= 2,
        'platform_coverage': check_all_platforms_present(),
        'data_quality': run_quality_validations(),
        'api_status': test_api_connection()
    }
```

### Alerts
Set up monitoring for:
- Data gaps > 3 days
- Platform data missing
- High variance from direct sources
- Authentication failures

## Best Practices

1. **Regular Syncs**: Daily for active monitoring
2. **Validation**: Cross-check with platform data monthly
3. **Documentation**: Note any data discrepancies
4. **Efficiency**: Only extract needed date ranges
5. **Backup**: Keep raw JSON responses

## Troubleshooting

### Data Discrepancies
- TooLost may have 24-48 hour delays
- Some platforms report at different intervals
- Currency/timezone differences possible

### Missing Platforms
- Ensure platforms are connected in TooLost
- Some require separate authentication
- Check platform-specific requirements

### Performance
- Large catalogs may require chunking
- Consider parallel processing by date range
- Archive old landing files regularly

## Future Enhancements

Planned features:
- [ ] Real-time streaming via webhooks
- [ ] Playlist performance tracking
- [ ] Geographic distribution data
- [ ] Revenue estimation models
- [ ] Automated anomaly detection
- [ ] Cross-distributor reconciliation