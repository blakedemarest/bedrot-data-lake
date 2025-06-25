# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Path Warning

AI agents often mix up these two directories:

`C:\Users\Earth\BEDROT PRODUCTIONS\BEDROT DATA LAKE`

`C:\Users\Earth\BEDROT PRODUCTIONS\BEDROT DATA LAKE\data_lake`

Be sure you're working in the correct folder before running any commands.

## Project Overview

BEDROT DATA ECOSYSTEM is a production-grade data architecture for music analytics, consisting of:

1. **Data Lake** (`data_lake/`) - ETL pipelines for raw data ingestion and processing
2. **Data Warehouse** (`data-warehouse/`) - Normalized SQLite database for analytics

The ecosystem serves as the central repository for BEDROT PRODUCTIONS' streaming analytics, marketing metrics, and audience data across multiple platforms (Spotify, TikTok, Meta Ads, DistroKid, etc.).

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

# Run complete data warehouse ETL pipeline
cd "data_lake"
.venv/Scripts/python.exe etl/run_all_etl.py

# Run individual ETL pipelines
.venv/Scripts/python.exe etl/etl_master_data.py
.venv/Scripts/python.exe etl/etl_streaming_performance.py
.venv/Scripts/python.exe etl/etl_social_media_performance.py

# Manual Python execution requires PROJECT_ROOT environment variable
python src/spotify/extractors/spotify_audience_extractor.py
```

## Architecture

### Data Lake Zones
The data lake follows a multi-zone architecture:
- `landing/` - Raw ingested data (HTML, JSON, CSV files)
- `raw/` - Validated and standardized data (NDJSON, CSV)
- `staging/` - Cleaned and processed data
- `curated/` - Business-ready datasets for analytics
- `archive/` - Historical snapshots with timestamps

### Data Warehouse
The data warehouse (`../data-warehouse/`) provides:
- **SQLite Database**: `bedrot_analytics.db` with 3NF normalized schema
- **10 Tables**: Artists, Platforms, Tracks, Campaigns, Financial Transactions, etc.
- **ETL Pipelines**: Located in `data_lake/etl/` directory
- **Business Analytics**: Ready-to-query performance metrics and financial data

### Data Lake ETL Organization
Code is organized by platform under `src/<platform>/`:
- `extractors/` - Scripts that download/scrape data into `landing/`
- `cleaners/` - Scripts that promote data through zones (landing→raw→staging→curated)
- `cookies/` - JSON cookie files for Playwright-based extractors

Example platforms: `distrokid/`, `spotify/`, `tiktok/`, `metaads/`, `linktree/`, `toolost/`

### Data Warehouse ETL Pipelines
Located in `etl/` directory:
- `etl_master_data.py` - Load artists, platforms, and tracks (master data)
- `etl_financial_data.py` - Load financial transactions from DistroKid and Capitol One
- `etl_streaming_performance.py` - Load Spotify audience and performance metrics
- `etl_social_media_performance.py` - Load TikTok analytics and engagement data
- `run_all_etl.py` - Master orchestrator that runs all pipelines in sequence

### Automated Pipelines
**Data Lake Pipeline** (`cronjob/run_datalake_cron.bat`) automatically:
1. Creates/activates Python virtual environment
2. Loops through all `src/<platform>/` directories
3. Executes all `extractors/*.py` scripts
4. Executes all `cleaners/*.py` scripts in order
5. Generates final consolidated reports

**Data Warehouse Pipeline** (`etl/run_all_etl.py`) automatically:
1. Loads master data (artists, tracks, platforms)
2. Processes financial transactions
3. Loads streaming performance metrics
4. Loads social media performance data
5. Generates analytics-ready database

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
- `etl/` - Data warehouse ETL pipelines and orchestration

## Data Quality
- Use pandas/polars for data processing
- Implement data validation in cleaner scripts
- Archive old data before overwriting curated files
- Log all ETL operations with timestamps
- Normalize artist names consistently across all pipelines
- Handle ISRC/UPC code uniqueness constraints
- Deduplicate tracks and performance records

## Dependencies
Key packages in `requirements.txt`:
- Data processing: pandas, polars, pyarrow
- Database: sqlite3 (built-in), sqlalchemy
- Web scraping: playwright, requests  
- Testing: pytest, pytest-cov
- Code quality: black, isort, flake8, mypy

Data warehouse dependencies in `../data-warehouse/requirements.txt`:
- pandas, numpy, python-dateutil (minimal set for ETL processing)

## Current Data Warehouse Status
- **Database**: `../data-warehouse/bedrot_analytics.db` (160 KB)
- **Artists**: 5 (PIG1987, ZONE A0, IWARY, collaborations)
- **Tracks**: 19 (with ISRC codes)
- **Streaming Records**: 1,800 (Spotify performance data)
- **Social Media Records**: 765 (TikTok analytics)
- **Platforms**: 10 (Spotify, TikTok, Meta Ads, etc.)

Ready for business analytics and reporting!