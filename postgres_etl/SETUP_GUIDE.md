# CSV-to-Tables ETL Setup Guide

## Overview

This solution automatically creates individual PostgreSQL tables for each CSV file in your `curated/` directory. Each table exactly matches the CSV schema with identical column names and data types.

## Features

✅ **Automated Table Creation**: Every CSV becomes its own PostgreSQL table  
✅ **Schema Consistency**: Tables match CSV structure exactly  
✅ **Future Expansion**: Automatically detects new CSV files  
✅ **Directory Monitoring**: Real-time file watching with `file_watcher.py`  
✅ **Deduplication**: Hash-based duplicate prevention  
✅ **Type Detection**: Intelligent PostgreSQL data type mapping  

## Files Created

1. **`csv_to_tables_etl.py`** - Core ETL pipeline for CSV-to-table conversion
2. **`file_watcher.py`** - Directory monitoring with real-time file detection
3. **`test_csv_schema.py`** - Schema analysis tool (no dependencies)
4. **`SETUP_GUIDE.md`** - This setup guide

## Quick Start

### 1. Install Dependencies

```bash
cd postgres_etl
pip install -r requirements.txt
```

### 2. Configure Environment

Create or update `.env` file:

```bash
# Database Connection
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=bedrot_analytics
POSTGRES_USER=bedrot_app
POSTGRES_PASSWORD=your_password_here

# Optional: Override curated directory path
CURATED_DATA_PATH=/path/to/curated
```

### 3. Initialize Database

```bash
# Create the database schema first
python init_db.py

# Run the CSV-to-tables ETL once
python csv_to_tables_etl.py
```

### 4. Start File Monitoring (Optional)

```bash
# Monitor for new CSV files and auto-process them
python file_watcher.py

# Or run once without monitoring
python file_watcher.py --once
```

## What Gets Created

Based on your current CSV files, these tables will be created:

### `bedrot_analytics.capitol_one_purchases_7113`
- `date` (DATE)
- `description` (VARCHAR)
- `category` (VARCHAR)
- `amount` (DECIMAL)
- `status` (VARCHAR)

### `bedrot_analytics.distrokid_dk_bank_details`
- `reporting_date` (DATE)
- `sale_month` (VARCHAR)
- `store` (VARCHAR)
- `artist` (VARCHAR)
- `title` (VARCHAR)
- `earnings_usd` (DECIMAL)
- ... (13 columns total)

### `bedrot_analytics.linktree_linktree_analytics_curated_*`
- `date` (DATE)
- `totalviews` (INTEGER)
- `uniqueviews` (INTEGER)
- `totalclicks` (INTEGER)
- `uniqueclicks` (INTEGER)
- `clickthroughrate` (DECIMAL)

### `bedrot_analytics.metaads_metaads_campaigns_daily`
- `campaign_id` (VARCHAR)
- `campaign_name_x` (VARCHAR)
- `spend` (DECIMAL)
- `impressions` (INTEGER)
- `clicks` (INTEGER)
- `date_start` (DATE)
- ... (38 columns total)

### `bedrot_analytics.tidy_daily_streams`
- `date` (DATE)
- `spotify_streams` (INTEGER)
- `apple_streams` (INTEGER)
- `combined_streams` (INTEGER)
- `source` (VARCHAR)

### `bedrot_analytics.tiktok_tiktok_analytics_curated_*`
- `artist` (VARCHAR)
- `zone` (VARCHAR)
- `date` (DATE)
- `video_views` (INTEGER)
- `profile_views` (INTEGER)
- `likes` (INTEGER)
- `engagement_rate` (DECIMAL)
- ... (10 columns total)

## Schema Analysis

To see what tables would be created without actually creating them:

```bash
python test_csv_schema.py
```

This will show:
- All CSV files found
- Proposed table names
- Column analysis
- Generated SQL schemas

## How It Works

### 1. File Discovery
- Recursively scans `curated/` directory
- Finds all `.csv` files in subdirectories
- Generates table names from file paths

### 2. Schema Detection
- Analyzes CSV columns and data types
- Maps to appropriate PostgreSQL types:
  - Date columns → `DATE`
  - Numeric columns → `INTEGER` or `DECIMAL`
  - Text columns → `VARCHAR(255)` or `TEXT`
  - Boolean columns → `BOOLEAN`

### 3. Table Creation
- Creates tables with exact CSV column structure
- Adds metadata columns:
  - `id` (SERIAL PRIMARY KEY)
  - `_ingested_at` (TIMESTAMP)
  - `_file_source` (VARCHAR)
  - `_row_hash` (VARCHAR) for deduplication

### 4. Data Loading
- Inserts all CSV rows into corresponding tables
- Handles NULL values and data type conversion
- Prevents duplicates using hash-based deduplication

## Directory Monitoring

The file watcher monitors your `curated/` directory for:
- New CSV files
- Modified CSV files
- Moved CSV files

When detected, it automatically:
1. Creates the table if it doesn't exist
2. Loads the new data
3. Prevents duplicate records

## Querying Your Data

Once tables are created, query them directly:

```sql
-- Daily streaming data
SELECT date, spotify_streams, apple_streams, combined_streams 
FROM bedrot_analytics.tidy_daily_streams 
WHERE date >= '2024-01-01'
ORDER BY date;

-- DistroKid earnings
SELECT artist, title, earnings_usd, reporting_date
FROM bedrot_analytics.distrokid_dk_bank_details
WHERE earnings_usd > 0
ORDER BY reporting_date DESC;

-- Meta advertising performance
SELECT campaign_name_x, spend, impressions, clicks, date_start
FROM bedrot_analytics.metaads_metaads_campaigns_daily
WHERE date_start >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY spend DESC;

-- TikTok analytics
SELECT artist, date, video_views, likes, engagement_rate
FROM bedrot_analytics.tiktok_tiktok_analytics_curated_20250618_074425
WHERE video_views > 0
ORDER BY date DESC;
```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_HOST` | Database host | localhost |
| `POSTGRES_PORT` | Database port | 5432 |
| `POSTGRES_DB` | Database name | bedrot_analytics |
| `POSTGRES_USER` | Database user | bedrot_app |
| `POSTGRES_PASSWORD` | Database password | (required) |
| `CURATED_DATA_PATH` | Path to curated directory | ../curated |

### Command Line Options

```bash
# File watcher options
python file_watcher.py --once              # Run once, don't monitor
python file_watcher.py --curated-dir /path # Override curated directory

# ETL pipeline options  
python csv_to_tables_etl.py               # Process all CSV files once
```

## Troubleshooting

### Missing Dependencies
```bash
pip install pandas psycopg2-binary python-dotenv watchdog
```

### Database Connection Issues
- Verify PostgreSQL is running
- Check `.env` file credentials
- Ensure database and user exist

### CSV Parsing Issues
- Ensure CSV files are UTF-8 encoded
- Check for malformed CSV rows
- Verify column headers are present

### Permission Issues
- Database user needs CREATE TABLE permissions
- File system read permissions on curated directory

## Integration with Existing System

This solution works alongside your existing JSONB-based ETL system:

- **Existing system**: Continues to work with `bedrot_analytics.insights` table
- **New system**: Creates individual tables for direct CSV access
- **Coexistence**: Both can run simultaneously

Choose the approach that best fits your needs:
- Use JSONB system for flexible analytics across data sources
- Use individual tables for SQL-native querying of specific datasets