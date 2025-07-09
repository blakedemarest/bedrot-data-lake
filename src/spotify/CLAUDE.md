# CLAUDE.md - Spotify Data Pipeline

This directory contains the Spotify data extraction and processing pipeline, focusing on Spotify for Artists audience analytics data.

## Overview

The Spotify pipeline extracts detailed audience demographics, listening patterns, and geographic data from Spotify for Artists. This data helps understand listener behavior and optimize marketing strategies.

## Directory Structure

```
spotify/
├── extractors/
│   └── spotify_audience_extractor.py  # Playwright-based audience data scraper
├── cleaners/
│   ├── spotify_landing2raw.py        # Convert CSV to NDJSON
│   ├── spotify_raw2staging.py        # Clean and validate data
│   └── spotify_staging2curated.py    # Create final analytics dataset
└── cookies/
    └── spotify_cookies.json           # Saved authentication session
```

## Key Files

### Extractors

**spotify_audience_extractor.py**
- Uses Playwright to log into Spotify for Artists
- Navigates to Audience tab and downloads CSV exports
- Handles multiple artist profiles if configured
- Saves to `landing/spotify/audience/` with timestamps

### Cleaners

**spotify_landing2raw.py**
- Validates CSV structure and headers
- Converts to NDJSON format for consistency
- Checks for required columns: date, listeners, streams, etc.
- Deduplicates data using hash tracking

**spotify_raw2staging.py**
- Standardizes date formats to ISO 8601
- Cleans numeric fields (removes commas, converts to int/float)
- Handles missing values appropriately
- Adds derived metrics (e.g., streams per listener)

**spotify_staging2curated.py**
- Aggregates data by time period (daily, weekly, monthly)
- Calculates growth metrics and trends
- Merges with artist metadata
- Outputs both CSV and Parquet formats

## Common Tasks

### Manual Data Extraction

```bash
cd /mnt/c/Users/Earth/BEDROT\ PRODUCTIONS/bedrot-data-ecosystem/data_lake
export PROJECT_ROOT=$(pwd)

# Run with visible browser (for debugging/re-auth)
python src/spotify/extractors/spotify_audience_extractor.py --headless=False

# Normal headless execution
python src/spotify/extractors/spotify_audience_extractor.py
```

### Processing Downloaded Data

Run the cleaners in sequence:
```bash
# 1. Convert landing data to raw
python src/spotify/cleaners/spotify_landing2raw.py

# 2. Clean and validate
python src/spotify/cleaners/spotify_raw2staging.py

# 3. Create curated dataset
python src/spotify/cleaners/spotify_staging2curated.py
```

### Updating Authentication

When cookies expire:
```bash
# Run extractor with visible browser
python src/spotify/extractors/spotify_audience_extractor.py --headless=False

# Log in manually when browser opens
# Script will save new cookies automatically
```

## Data Schema

### Audience Data Fields
- **date**: Report date (YYYY-MM-DD)
- **listeners**: Unique listener count
- **streams**: Total stream count
- **followers**: Artist follower count
- **monthly_listeners**: 28-day unique listeners
- **listener_demographics**: Age and gender breakdown
- **top_cities**: Geographic distribution
- **source_breakdown**: How listeners discover music

### Derived Metrics
- **streams_per_listener**: Engagement metric
- **follower_conversion_rate**: Followers / Monthly Listeners
- **growth_rate**: Period-over-period change
- **retention_rate**: Returning listener percentage

## Configuration

### Environment Variables
```bash
# Optional: Override default paths
SPOTIFY_LANDING_PATH=/custom/path/to/landing
SPOTIFY_ARTIST_IDS=id1,id2,id3  # Multiple artists
```

### Artist Configuration
Edit `src/spotify/extractors/spotify_audience_extractor.py`:
```python
ARTIST_CONFIGS = [
    {"id": "1234567890", "name": "Artist Name"},
    # Add more artists as needed
]
```

## Rate Limiting

Spotify for Artists has the following limits:
- Data exports: Max 5 per hour
- Page navigation: No hard limit, but use delays
- Session timeout: 24 hours

The extractor implements:
- 3-5 second delays between page loads
- Exponential backoff on errors
- Maximum 3 retry attempts

## Error Handling

Common issues and solutions:

### Authentication Failed
```
Error: Could not find audience tab
Solution: Delete cookies and re-authenticate
```

### Download Timeout
```
Error: Download did not complete in 30s
Solution: Check internet connection, increase timeout in script
```

### Missing Data Columns
```
Error: Expected column 'monthly_listeners' not found
Solution: Spotify may have changed export format, update cleaners
```

## Testing

Run unit tests:
```bash
pytest tests/spotify/ -v
```

Test with sample data:
```bash
# Create test file in landing/
echo "date,listeners,streams\n2024-01-01,1000,5000" > landing/spotify/audience/test.csv

# Run cleaners
python src/spotify/cleaners/spotify_landing2raw.py --test-mode
```

## Data Quality Checks

The pipeline performs these validations:
1. **Completeness**: All required fields present
2. **Consistency**: Dates in chronological order
3. **Accuracy**: Numeric values within reasonable ranges
4. **Uniqueness**: No duplicate entries for same date

## Integration with Data Warehouse

Curated Spotify data feeds into these warehouse tables:
- `streaming_data`: Platform-level metrics
- `audience_demographics`: Detailed listener profiles
- `geographic_distribution`: City and country breakdowns

## Troubleshooting

### Browser Automation Issues
- Ensure Playwright is installed: `playwright install chromium`
- Check if Spotify UI has changed (inspect elements)
- Try running with `--debug` flag for verbose logging

### Data Discrepancies
- Compare with Spotify for Artists dashboard
- Check timezone handling (UTC vs local)
- Verify aggregation logic in staging2curated

### Performance
- For large datasets, consider using Polars instead of Pandas
- Implement incremental processing (only new data)
- Archive old landing files regularly

## Future Enhancements

Planned improvements:
- [ ] Real-time streaming via Spotify Web API
- [ ] Playlist performance tracking
- [ ] Competition analysis features
- [ ] Automated anomaly detection
- [ ] Integration with marketing campaign data