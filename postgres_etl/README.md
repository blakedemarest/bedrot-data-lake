# BEDROT Data Lake PostgreSQL ETL System

A robust PostgreSQL-based data system that automatically ingests and stores analytical insights from curated CSV data with support for semi-structured data using JSONB.

## Architecture Overview

- **PostgreSQL Database**: Stores insights with flexible JSONB columns for semi-structured data
- **Modular ETL Pipeline**: Python-based system for automatic CSV discovery and ingestion
- **Docker Support**: Containerized setup for easy deployment and portability
- **Intelligent Data Detection**: Automatic classification of metrics types and platforms

## Features

✅ **Flexible Schema**: JSONB columns preserve original data structure while enabling SQL queries  
✅ **Automatic Discovery**: Recursively finds and processes all CSV files in `/curated/`  
✅ **Data Type Detection**: Intelligently classifies streaming, social, advertising, and financial metrics  
✅ **Deduplication**: Hash-based deduplication prevents duplicate records  
✅ **Future-Proof**: Easily extensible for new data sources and formats  
✅ **Docker Ready**: Complete containerized setup with PostgreSQL and pgAdmin  

## Quick Start

### 1. Setup Environment
```bash
# Clone/navigate to the postgres_etl directory
cd postgres_etl

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your database credentials
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize Database
```bash
python init_db.py
```

### 4. Run ETL Pipeline
```bash
python etl_pipeline.py
```

## Docker Setup (Recommended)

### Start PostgreSQL Database
```bash
docker-compose up postgres -d
```

### Initialize Database (first time)
```bash
docker-compose run --rm etl_runner python init_db.py
```

### Run ETL Pipeline
```bash
docker-compose --profile etl up
```

### Access pgAdmin (optional)
```bash
docker-compose --profile admin up pgadmin -d
# Visit http://localhost:8080
```

## Database Schema

### Core Tables

**`bedrot_analytics.data_sources`**
- Tracks metadata about each data source file
- Includes ingestion timestamps and row counts

**`bedrot_analytics.insights`**
- Main table storing all analytical data
- Uses JSONB for flexible data storage
- Includes structured fields for efficient querying

### Views for Easy Access

**`bedrot_analytics.streaming_insights`**
```sql
SELECT artist_name, platform, spotify_streams, apple_streams, combined_streams
FROM bedrot_analytics.streaming_insights 
WHERE date_recorded >= '2024-01-01';
```

**`bedrot_analytics.social_insights`**
```sql
SELECT platform, total_views, total_clicks, click_through_rate
FROM bedrot_analytics.social_insights 
WHERE date_recorded >= CURRENT_DATE - INTERVAL '30 days';
```

**`bedrot_analytics.advertising_insights`**
```sql
SELECT campaign_name, spend, impressions, cost_per_click, reach
FROM bedrot_analytics.advertising_insights 
WHERE date_recorded >= CURRENT_DATE - INTERVAL '7 days';
```

## Supported Data Types

The system automatically detects and processes:

- **Streaming Metrics**: Spotify, Apple Music, combined streams
- **Social Media**: Views, clicks, engagement rates from TikTok, Linktree
- **Advertising**: Meta/Facebook campaign performance data
- **Financial**: Purchase data and transactions

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_HOST` | Database host | localhost |
| `POSTGRES_PORT` | Database port | 5432 |
| `POSTGRES_DB` | Database name | bedrot_analytics |
| `POSTGRES_USER` | App user | bedrot_app |
| `POSTGRES_PASSWORD` | App password | (required) |
| `POSTGRES_ADMIN_USER` | Admin user | postgres |
| `POSTGRES_ADMIN_PASSWORD` | Admin password | (required) |

## File Processing Logic

1. **Discovery**: Recursively scans `/curated/` directory for CSV files
2. **Classification**: Analyzes columns and file paths to determine metric type
3. **Cleaning**: Converts numeric fields, parses dates, extracts entities
4. **Storage**: Inserts into PostgreSQL with deduplication via hash keys
5. **Indexing**: Automatically indexed on date, metric type, and platform

## Extending the System

### Adding New Data Types

1. Update `DataTypeDetector.detect_metric_type()` with new detection logic
2. Add corresponding view in `schema.sql`
3. Update `DataCleaner` if special processing is needed

### Adding New Platforms

1. Update `platform_mapping` in `DataTypeDetector.extract_platform()`
2. Add any platform-specific cleaning logic

## Monitoring and Maintenance

### View Ingestion Status
```sql
SELECT source_name, last_ingested_at, row_count 
FROM bedrot_analytics.data_sources 
ORDER BY last_ingested_at DESC;
```

### Check Data Quality
```sql
SELECT metric_type, platform, COUNT(*), MIN(date_recorded), MAX(date_recorded)
FROM bedrot_analytics.insights 
GROUP BY metric_type, platform;
```

### Performance Monitoring
- All queries on common fields (date, platform, metric_type) are indexed
- JSONB columns use GIN indexes for efficient JSON queries
- Consider partitioning by date for very large datasets

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure database user has proper permissions
2. **Date Parsing**: Check date formats in CSV files match expected patterns  
3. **Memory Issues**: Adjust batch size for large CSV files
4. **Encoding Issues**: Ensure CSV files are UTF-8 encoded

### Logs
Check application logs for detailed error information:
```bash
# Local
tail -f etl.log

# Docker
docker-compose logs etl_runner
```

## Future Enhancements

- [ ] Incremental loading based on file modification times
- [ ] Data validation rules and quality checks
- [ ] Automated data lineage tracking  
- [ ] Real-time streaming ingestion via Kafka
- [ ] Machine learning insights generation
- [ ] REST API for data access
- [ ] Automated alerting for data quality issues

## License

Internal use for BEDROT Productions data analytics.