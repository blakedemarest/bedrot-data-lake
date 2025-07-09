# CLAUDE.md - Data Lake Source Code

This directory contains the core ETL pipeline implementations for the BEDROT Data Lake. All platform-specific extractors and cleaners are organized here following a consistent pattern.

## Directory Structure

```
src/
├── common/           # Shared utilities and helpers
├── distrokid/       # DistroKid streaming and financial data
├── spotify/         # Spotify audience analytics
├── tiktok/          # TikTok analytics and engagement
├── metaads/         # Meta (Facebook/Instagram) advertising
├── linktree/        # Linktree link analytics
├── toolost/         # TooLost streaming aggregator
├── youtube/         # YouTube analytics (planned)
├── instagram/       # Instagram insights (planned)
└── mailchimp/       # Email marketing data (planned)
```

## Common Development Tasks

### Adding a New Data Source

1. **Create the directory structure**:
   ```bash
   mkdir -p src/<service>/extractors
   mkdir -p src/<service>/cleaners
   mkdir -p src/<service>/cookies
   ```

2. **Implement the extractor** (`src/<service>/extractors/<service>_extractor.py`):
   - Use Playwright for web scraping (see `common/cookies.py` for cookie management)
   - Use requests for API-based extraction
   - Save raw data to `landing/<service>/` with timestamp in filename

3. **Create three cleaner scripts** following the naming convention:
   - `<service>_landing2raw.py` - Validates and converts to NDJSON/CSV
   - `<service>_raw2staging.py` - Cleans and standardizes data
   - `<service>_staging2curated.py` - Creates business-ready datasets

4. **Add tests** in `tests/<service>/`

### Running Individual Components

Always ensure `PROJECT_ROOT` is set:
```bash
cd /mnt/c/Users/Earth/BEDROT\ PRODUCTIONS/bedrot-data-ecosystem/data_lake
export PROJECT_ROOT=$(pwd)
```

Run extractors:
```bash
python src/<service>/extractors/<extractor_name>.py
```

Run cleaners in order:
```bash
python src/<service>/cleaners/<service>_landing2raw.py
python src/<service>/cleaners/<service>_raw2staging.py
python src/<service>/cleaners/<service>_staging2curated.py
```

## Key Conventions

### File Naming
- Extractors: `<service>_<data_type>_extractor.py`
- Cleaners: `<service>_<source>2<target>.py`
- Output files: `<service>_<data_type>_YYYYMMDD_HHMMSS.<ext>`

### Data Formats
- Landing zone: Raw format (HTML, JSON, CSV, TSV)
- Raw zone: NDJSON for structured data, CSV for tabular
- Staging zone: Cleaned CSV with standardized columns
- Curated zone: Business-ready CSV/Parquet files

### Error Handling
- Log all operations with timestamps
- Handle missing files gracefully
- Archive existing curated files before overwriting
- Track processed files using hash helpers

### Authentication
- Store cookies in `src/<service>/cookies/` as JSON files
- Use environment variables for API keys (never commit secrets)
- Implement retry logic for rate-limited APIs

## Common Utilities

### Cookie Management (`common/cookies.py`)
Handles Playwright browser automation with saved sessions:
```python
from common.cookies import setup_browser_with_cookies

# Load cookies for authenticated session
context, browser = await setup_browser_with_cookies(
    service="spotify",
    headless=True
)
```

### Hash Helpers (`common/utils/hash_helpers.py`)
Prevents duplicate data processing:
```python
from common.utils.hash_helpers import is_duplicate, mark_as_processed

# Check if file was already processed
if not is_duplicate(file_path, service="spotify"):
    process_file(file_path)
    mark_as_processed(file_path, service="spotify")
```

### File Utilities (`common/utils/file_utils.py`)
Standardized file operations:
```python
from common.utils.file_utils import get_latest_file, archive_file

# Get most recent file matching pattern
latest = get_latest_file("landing/spotify/", pattern="audience_*.csv")

# Archive before overwriting
archive_file("curated/spotify_audience.csv")
```

## Testing

Run tests for a specific service:
```bash
pytest tests/<service>/ -v
```

Run all tests with coverage:
```bash
pytest -ra --cov=src --cov-report=term-missing
```

## Important Notes

- Always validate data types in cleaners
- Use pandas for data processing, polars for large files
- Log processing stats (rows processed, errors, etc.)
- Follow PEP 8 and use black/isort for formatting
- Document any service-specific quirks in the service's README

## Troubleshooting

### Import Errors
Ensure `PROJECT_ROOT` is set and `src/` is in Python path:
```bash
export PYTHONPATH=$PROJECT_ROOT/src:$PYTHONPATH
```

### Cookie Expiration
Re-run the extractor with `--headless=False` to manually log in and save new cookies.

### Rate Limiting
Check service-specific README for rate limit handling. Most extractors implement exponential backoff.

### Data Quality Issues
Run diagnostic scripts in each cleaner to identify data anomalies before promotion.