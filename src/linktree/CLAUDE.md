# CLAUDE.md - Linktree Data Pipeline

This directory contains the Linktree analytics extraction and processing pipeline for tracking link performance and visitor engagement metrics.

## Overview

The Linktree pipeline extracts detailed analytics about link clicks, visitor demographics, and traffic sources. This data helps optimize link placement and understand audience behavior across different platforms.

## Directory Structure

```
linktree/
├── extractors/
│   └── linktree_analytics_extractor.py  # GraphQL-based data extraction
├── cleaners/
│   ├── linktree_landing2raw.py         # JSON to NDJSON conversion
│   ├── linktree_raw2staging.py         # Data normalization
│   └── linktree_staging2curated.py     # Analytics aggregation
└── cookies/
    └── linktree_cookies.json            # Authentication cookies
```

## Key Files

### Extractors

**linktree_analytics_extractor.py**
- Uses Playwright to authenticate with Linktree
- Intercepts GraphQL API calls for analytics data
- Captures detailed metrics for each link
- Handles pagination for historical data

### Cleaners

**linktree_landing2raw.py**
- Parses GraphQL JSON responses
- Extracts nested analytics objects
- Converts to NDJSON format
- Validates data structure

**linktree_raw2staging.py**
- Normalizes timestamp formats
- Flattens nested JSON structures
- Calculates click-through rates
- Enriches with derived metrics

**linktree_staging2curated.py**
- Aggregates metrics by time period
- Creates link performance rankings
- Analyzes traffic source breakdowns
- Generates trend analysis

## Common Tasks

### Data Extraction

```bash
cd /mnt/c/Users/Earth/BEDROT\ PRODUCTIONS/bedrot-data-ecosystem/data_lake
export PROJECT_ROOT=$(pwd)

# Run with browser visible (for debugging)
python src/linktree/extractors/linktree_analytics_extractor.py --headless=False

# Normal headless extraction
python src/linktree/extractors/linktree_analytics_extractor.py
```

### Processing Pipeline

```bash
# Convert GraphQL responses to NDJSON
python src/linktree/cleaners/linktree_landing2raw.py

# Clean and normalize data
python src/linktree/cleaners/linktree_raw2staging.py

# Create analytics datasets
python src/linktree/cleaners/linktree_staging2curated.py
```

### Custom Date Ranges

```python
# In extractor, modify date range
START_DATE = datetime.now() - timedelta(days=90)
END_DATE = datetime.now()
```

## Data Schema

### Core Metrics
- **link_id**: Unique identifier for each link
- **title**: Link display title
- **url**: Destination URL
- **clicks**: Total click count
- **unique_visitors**: Unique visitor count
- **created_at**: When link was added
- **position**: Order on Linktree page

### Analytics Fields
- **timestamp**: Metric timestamp
- **views**: Page views (not clicks)
- **clicks**: Link clicks
- **ctr**: Click-through rate (clicks/views)
- **avg_time_on_page**: Visitor engagement
- **bounce_rate**: Single-click sessions

### Traffic Sources
- **source**: Referrer category (direct, social, search)
- **medium**: Specific platform (instagram, twitter, google)
- **campaign**: UTM campaign if tracked
- **device_type**: Mobile, desktop, tablet
- **country**: Visitor location
- **city**: City-level data if available

## Configuration

### Environment Variables
```bash
# Optional overrides
LINKTREE_USERNAME=your-username
LINKTREE_PROFILE_URL=https://linktr.ee/your-profile

# Data extraction settings
LINKTREE_DAYS_BACK=90  # Historical data range
LINKTREE_WAIT_TIMEOUT=30  # Seconds to wait for data
```

### GraphQL Interception
The extractor captures GraphQL requests:
```python
# Intercepted endpoints
ANALYTICS_ENDPOINT = "https://linktr.ee/api/graphql"
METRICS_QUERY = "GetProfileAnalytics"
```

## Authentication

### Cookie Management
```bash
# First-time setup
python src/linktree/extractors/linktree_analytics_extractor.py --setup

# Refresh expired session
rm src/linktree/cookies/linktree_cookies.json
python src/linktree/extractors/linktree_analytics_extractor.py --headless=False
```

### Session Handling
- Sessions expire after 30 days
- Auto-detection of expired cookies
- Graceful re-authentication flow
- Secure cookie storage

## Rate Limiting

Linktree considerations:
- No official API rate limits
- Respectful scraping: 2-3 second delays
- Avoid parallel requests
- Cache responses when possible

Implemented safeguards:
```python
# Random delays between requests
time.sleep(random.uniform(2, 5))

# Exponential backoff on errors
wait_time = min(300, (2 ** attempt) * 10)
```

## Error Handling

### Common Issues

**GraphQL Interception Failed**
```
Error: No analytics requests captured
Solution:
1. Check if Linktree changed their API
2. Update GraphQL query names
3. Verify network interception is enabled
```

**Missing Analytics Data**
```
Error: Empty response for date range
Solution:
1. Verify account has Pro features
2. Check if data exists for period
3. Try smaller date ranges
```

**Authentication Loop**
```
Error: Redirect loop during login
Solution:
1. Clear all cookies
2. Check for 2FA requirements
3. Try different browser engine
```

## Data Quality

### Validation Checks
1. **Click Consistency**: Clicks ≤ Views
2. **CTR Bounds**: 0% ≤ CTR ≤ 100%
3. **Temporal Order**: Timestamps sequential
4. **Link Matching**: All links have analytics

### Quality Metrics
```python
# Data quality report
def generate_quality_report(df):
    return {
        'missing_clicks': df['clicks'].isna().sum(),
        'invalid_ctr': (df['ctr'] > 1.0).sum(),
        'orphan_links': find_links_without_data(df),
        'date_gaps': find_missing_dates(df)
    }
```

## Testing

### Unit Tests
```bash
pytest tests/linktree/ -v
```

### Mock GraphQL Responses
```python
# tests/linktree/fixtures/mock_graphql.json
{
  "data": {
    "profile": {
      "analytics": {
        "links": [{
          "id": "123",
          "clicks": 100,
          "views": 1000
        }]
      }
    }
  }
}
```

### Integration Testing
```bash
# Test with real account (be careful with rate limits)
python src/linktree/extractors/linktree_analytics_extractor.py --test-mode --days=1
```

## Advanced Features

### Link Performance Analysis
```python
# Identify top performing links
def analyze_link_performance(df):
    return df.groupby('link_id').agg({
        'clicks': 'sum',
        'ctr': 'mean',
        'unique_visitors': 'sum'
    }).sort_values('clicks', ascending=False)
```

### Traffic Source Attribution
```python
# Breakdown by source
def analyze_traffic_sources(df):
    return pd.pivot_table(
        df,
        values='clicks',
        index='source',
        columns='device_type',
        aggfunc='sum'
    )
```

### Time-based Patterns
```python
# Find peak engagement times
def find_peak_times(df):
    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
    return df.groupby('hour')['clicks'].mean()
```

## Integration with Other Data

### Cross-Platform Analysis
Combine with social media data:
```python
# Match Linktree clicks with social posts
linktree_df = pd.read_csv('curated/linktree_analytics.csv')
social_df = pd.read_csv('curated/social_media_posts.csv')

# Find correlation between posts and link clicks
merged = pd.merge_asof(
    linktree_df.sort_values('timestamp'),
    social_df.sort_values('posted_at'),
    left_on='timestamp',
    right_on='posted_at',
    direction='backward',
    tolerance=pd.Timedelta('1h')
)
```

### Campaign Attribution
Track marketing campaign effectiveness:
```python
# Extract UTM parameters
df['campaign'] = df['url'].str.extract(r'utm_campaign=([^&]+)')
campaign_performance = df.groupby('campaign')['clicks'].sum()
```

## Troubleshooting

### Browser Automation
- Update Playwright: `playwright install`
- Check browser console for errors
- Use screenshots for debugging

### Data Gaps
- Linktree only shows data for Pro accounts
- Historical data limited to 365 days
- Some metrics require higher tier plans

### Performance
- Large link collections may be slow
- Consider date-based chunking
- Archive old raw files regularly

## Best Practices

1. **Regular Extraction**: Daily for active profiles
2. **Link Naming**: Use descriptive, consistent titles
3. **UTM Tracking**: Add campaign parameters
4. **A/B Testing**: Track performance variations
5. **Data Backup**: Keep raw GraphQL responses

## Future Enhancements

Planned improvements:
- [ ] Real-time webhook integration
- [ ] Competitive analysis features
- [ ] Link optimization recommendations
- [ ] Automated A/B testing
- [ ] QR code performance tracking
- [ ] Integration with URL shorteners