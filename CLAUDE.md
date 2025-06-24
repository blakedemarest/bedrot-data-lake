# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Path Warning

AI agents often mix up these two directories:

`C:\Users\Earth\BEDROT PRODUCTIONS\BEDROT DATA LAKE`

`C:\Users\Earth\BEDROT PRODUCTIONS\BEDROT DATA LAKE\data_lake`

Be sure you're working in the correct folder before running any commands.

## Project Overview

BEDROT DATA LAKE is a production-grade data lake architecture for music analytics, serving as the central repository for BEDROT PRODUCTIONS' streaming analytics, marketing metrics, and audience data across multiple platforms (Spotify, TikTok, Meta Ads, DistroKid, etc.).

## Development Commands

### Testing
```bash
# Run all tests with coverage
pytest -ra --cov=src --cov-report=term-missing

# Run tests for specific service
pytest tests/spotify/ -v
```

### Code Quality
```bash
# Format code
black src/
isort src/

# Lint code  
flake8 src/
mypy src/
```

### Data Pipeline Execution
```bash
# Run full data lake pipeline (Windows)
data_lake/cronjob/run_datalake_cron.bat

# Run pipeline without extractors (cleaners only)
data_lake/cronjob/run_datalake_cron_no_extractors.bat

# Manual Python execution requires PROJECT_ROOT environment variable
cd "data_lake"
python src/spotify/extractors/spotify_audience_extractor.py
```

## Architecture

### Data Flow Zones
The data lake follows a multi-zone architecture:
- `landing/` - Raw ingested data (HTML, JSON, CSV files)
- `raw/` - Validated and standardized data (NDJSON, CSV)
- `staging/` - Cleaned and processed data
- `curated/` - Business-ready datasets for analytics
- `archive/` - Historical snapshots with timestamps

### ETL Organization
Code is organized by platform under `src/<platform>/`:
- `extractors/` - Scripts that download/scrape data into `landing/`
- `cleaners/` - Scripts that promote data through zones (landing→raw→staging→curated)
- `cookies/` - JSON cookie files for Playwright-based extractors

Example platforms: `distrokid/`, `spotify/`, `tiktok/`, `metaads/`, `linktree/`, `toolost/`

### Automated Pipeline
The cron job (`cronjob/run_datalake_cron.bat`) automatically:
1. Creates/activates Python virtual environment
2. Loops through all `src/<platform>/` directories
3. Executes all `extractors/*.py` scripts
4. Executes all `cleaners/*.py` scripts in order
5. Generates final consolidated reports

## Key Conventions

### Environment Setup
- All scripts expect `PROJECT_ROOT` environment variable (set via `.env`)
- Virtual environment: `.venv/` in project root
- Python path includes `src/` for `from common...` imports

### Cleaner Naming Pattern
Follow strict naming for automatic execution order:
- `<service>_landing2raw.py`
- `<service>_raw2staging.py` 
- `<service>_staging2curated.py`

### File Formats
- Raw data: NDJSON for structured data, CSV for tabular
- All files: UTF-8 encoding
- Timestamps: ISO format `YYYYMMDD_HHMMSS` in filenames

### Service Integration
To add a new data source:
1. Create `src/<service>/extractors/`, `src/<service>/cleaners/`, `src/<service>/cookies/`
2. Follow extractor template using Playwright/requests
3. Implement three cleaner scripts following naming convention
4. Add placeholder tests in `tests/<service>/`
5. No manual registration required - cron job auto-discovers new services

### Common Utilities
- `common/cookies.py` - Cookie loading for Playwright extractors
- `common/utils/hash_helpers.py` - Data deduplication utilities
- `common/extractors/tiktok_shared.py` - Shared TikTok functionality

## Data Quality
- Use pandas/polars for data processing
- Implement data validation in cleaner scripts
- Archive old data before overwriting curated files
- Log all ETL operations with timestamps

## Dependencies
Key packages in `requirements.txt`:
- Data processing: pandas, polars, pyarrow
- Storage: minio, boto3, sqlalchemy, psycopg2-binary
- Web scraping: playwright, requests
- Testing: pytest, pytest-cov
- Code quality: black, isort, flake8, mypy