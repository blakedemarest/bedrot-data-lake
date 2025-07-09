# Staging Zone

## Purpose
The staging zone serves as the critical data preparation and quality assurance layer within the BEDROT Data Lake. This zone transforms raw, validated data into clean, standardized, and schema-compliant datasets that are ready for business logic application and analytical consumption. The staging zone ensures data consistency, quality, and reliability before promotion to the curated zone.

## What Goes Here
- **Cleaned and standardized data**: Normalized formats, consistent data types, and unified schemas
- **Schema-compliant datasets**: Data structures validated against predefined schemas
- **Quality-assured data**: Datasets that have passed comprehensive validation checks
- **Joined and aggregated data**: Cross-platform data integration and preliminary aggregations
- **Transformed datasets**: Data with applied business rules and derived calculations
- **Deduplicated data**: Removal of duplicate records with hash-based validation
- **Enriched data**: Addition of calculated fields, metadata, and contextual information
- **Intermediate processing outputs**: Results from multi-stage transformation pipelines

## Platform-Specific Processing

### DistroKid Data Processing
- **Input**: Validated HTML files from raw zone (`streams_stats_YYYYMMDD_HHMMSS.html`)
- **Processing**: HTML parsing, data extraction, format standardization
- **Output**: `distrokid_streams_staging_YYYYMMDD_HHMMSS.csv`
- **Transformations**: Date normalization, numeric conversion, field mapping

### TooLost Analytics Processing
- **Input**: Validated JSON files from raw zone (`toolost_analytics_YYYYMMDD_HHMMSS.json`)
- **Processing**: JSON parsing, schema validation, data standardization
- **Output**: `toolost_analytics_staging_YYYYMMDD_HHMMSS.csv`
- **Transformations**: Platform-specific metric extraction, cross-platform harmonization

### Meta Ads Processing
- **Input**: Campaign data from raw zone (JSON and CSV formats)
- **Processing**: API response parsing, metric calculation, data enrichment
- **Output**: `metaads_staging_YYYYMMDD_HHMMSS.csv`
- **Transformations**: Campaign performance calculations, pixel event processing

### TikTok Analytics Processing
- **Input**: Analytics JSON from raw zone
- **Processing**: Video performance extraction, audience data processing
- **Output**: `tiktok_staging_YYYYMMDD_HHMMSS.csv`
- **Transformations**: Engagement rate calculations, trend analysis preparation

### Social Media Processing
- **Input**: Platform-specific data from raw zone (Linktree, YouTube, etc.)
- **Processing**: Click analytics, engagement metrics, traffic source analysis
- **Output**: `{platform}_analytics_staging_YYYYMMDD_HHMMSS.csv`
- **Transformations**: Click-through rate calculations, conversion tracking

## Directory Structure
```
staging/
├── distrokid/
│   ├── streams/
│   │   ├── distrokid_streams_staging_20240522_143022.csv
│   │   └── distrokid_streams_staging_20240523_091500.csv
│   └── sales/
│       └── distrokid_sales_staging_20240601.csv
├── toolost/
│   ├── analytics/
│   │   ├── toolost_analytics_staging_20240522_140530.csv
│   │   └── toolost_analytics_staging_20240523_140730.csv
│   └── spotify/
│       └── toolost_spotify_staging_20240522.csv
├── metaads/
│   ├── campaigns/
│   │   └── metaads_campaigns_staging_20240522.csv
│   └── daily/
│       └── metaads_daily_staging_20240522_083045.csv
├── tiktok/
│   ├── analytics/
│   │   └── tiktok_analytics_staging_20240522.csv
│   └── videos/
│       └── tiktok_videos_staging_20240522.csv
├── social_media/
│   ├── linktree/
│   │   └── linktree_analytics_staging_20240522_120000.csv
│   ├── youtube/
│   │   └── youtube_analytics_staging_20240522.csv
│   └── spotify/
│       └── spotify_artists_staging_20240522.csv
├── cross_platform/
│   ├── streaming_unified_staging_20240522.csv
│   ├── social_media_unified_staging_20240522.csv
│   └── marketing_unified_staging_20240522.csv
└── quality_reports/
    ├── validation_summary_20240522.json
    ├── data_quality_metrics_20240522.csv
    └── transformation_log_20240522.txt
```

## Data Transformation Pipeline

### Schema Standardization
All staging datasets follow consistent schema patterns:

```python
# Standard schema for streaming data
streaming_schema = {
    'date': 'datetime64[ns]',
    'platform': 'string',
    'artist_name': 'string',
    'track_name': 'string',
    'streams': 'int64',
    'revenue_usd': 'float64',
    'country': 'string',
    'source_file': 'string',
    'processed_timestamp': 'datetime64[ns]'
}

# Standard schema for marketing data
marketing_schema = {
    'date': 'datetime64[ns]',
    'platform': 'string',
    'campaign_id': 'string',
    'campaign_name': 'string',
    'impressions': 'int64',
    'clicks': 'int64',
    'spend_usd': 'float64',
    'conversions': 'int64',
    'ctr': 'float64',
    'cpc': 'float64',
    'source_file': 'string',
    'processed_timestamp': 'datetime64[ns]'
}
```

### Data Quality Validation
Each staging process includes comprehensive quality checks:

```python
# Example: DistroKid data validation
def validate_distrokid_staging_data(df):
    validation_results = []
    
    # Check for required columns
    required_cols = ['date', 'artist_name', 'track_name', 'streams']
    missing_cols = set(required_cols) - set(df.columns)
    if missing_cols:
        validation_results.append({
            'check': 'schema_completeness',
            'status': 'FAIL',
            'message': f'Missing columns: {missing_cols}'
        })
    
    # Check data types
    if df['streams'].dtype not in ['int64', 'float64']:
        validation_results.append({
            'check': 'data_types',
            'status': 'FAIL',
            'message': 'Streams column must be numeric'
        })
    
    # Check for negative values
    if (df['streams'] < 0).any():
        validation_results.append({
            'check': 'business_rules',
            'status': 'FAIL',
            'message': 'Negative stream counts detected'
        })
    
    # Check for duplicates
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        validation_results.append({
            'check': 'deduplication',
            'status': 'WARNING',
            'message': f'{duplicate_count} duplicate records found'
        })
    
    return validation_results
```

### Data Cleaning Transformations

#### Text Standardization
```python
# Artist and track name standardization
def standardize_text_fields(df):
    # Remove extra whitespace
    df['artist_name'] = df['artist_name'].str.strip()
    df['track_name'] = df['track_name'].str.strip()
    
    # Standardize case
    df['artist_name'] = df['artist_name'].str.title()
    
    # Remove special characters from IDs
    df['track_id'] = df['track_id'].str.replace(r'[^a-zA-Z0-9]', '', regex=True)
    
    return df
```

#### Date and Time Processing
```python
# Date standardization and timezone handling
def standardize_dates(df, date_column='date'):
    # Convert to datetime
    df[date_column] = pd.to_datetime(df[date_column])
    
    # Standardize to UTC
    if df[date_column].dt.tz is not None:
        df[date_column] = df[date_column].dt.tz_convert('UTC')
    else:
        df[date_column] = df[date_column].dt.tz_localize('UTC')
    
    # Add derived date fields
    df['year'] = df[date_column].dt.year
    df['month'] = df[date_column].dt.month
    df['day_of_week'] = df[date_column].dt.dayofweek
    
    return df
```

#### Numeric Data Processing
```python
# Revenue and metric calculations
def process_financial_data(df):
    # Convert revenue to USD (if not already)
    if 'revenue_local' in df.columns and 'currency' in df.columns:
        df['revenue_usd'] = df.apply(lambda row: 
            convert_to_usd(row['revenue_local'], row['currency']), axis=1)
    
    # Calculate derived metrics
    df['revenue_per_stream'] = df['revenue_usd'] / df['streams'].replace(0, np.nan)
    df['ctr'] = df['clicks'] / df['impressions'].replace(0, np.nan)
    df['cpc'] = df['spend_usd'] / df['clicks'].replace(0, np.nan)
    
    # Handle infinite and NaN values
    df = df.replace([np.inf, -np.inf], np.nan)
    
    return df
```

## Cross-Platform Data Integration

### Platform Harmonization
Staging processes ensure consistent data representation across platforms:

```python
# Platform-specific field mapping
platform_mappings = {
    'distrokid': {
        'date': 'report_date',
        'streams': 'total_streams',
        'revenue': 'earnings_usd'
    },
    'toolost': {
        'date': 'date',
        'streams': 'stream_count',
        'revenue': 'revenue_usd'
    },
    'spotify': {
        'date': 'period_start',
        'streams': 'streams',
        'revenue': 'net_revenue'
    }
}

def harmonize_platform_data(df, platform):
    mapping = platform_mappings.get(platform, {})
    
    # Rename columns to standard format
    df = df.rename(columns=mapping)
    
    # Add platform identifier
    df['platform'] = platform
    
    # Standardize data types
    df = standardize_schema(df)
    
    return df
```

### Data Aggregation
```python
# Cross-platform streaming aggregation
def create_unified_streaming_data():
    platforms = ['distrokid', 'toolost', 'spotify']
    unified_data = []
    
    for platform in platforms:
        # Load platform-specific staging data
        platform_data = load_latest_staging_data(platform)
        
        # Harmonize schema
        harmonized_data = harmonize_platform_data(platform_data, platform)
        
        # Validate and clean
        validated_data = validate_and_clean(harmonized_data)
        
        unified_data.append(validated_data)
    
    # Combine all platforms
    combined_df = pd.concat(unified_data, ignore_index=True)
    
    # Remove duplicates across platforms
    combined_df = combined_df.drop_duplicates(
        subset=['date', 'artist_name', 'track_name', 'platform']
    )
    
    return combined_df
```

## Staging Zone Rules & Standards

### File Format Standards
- **Primary format**: CSV for tabular data, JSONL for semi-structured data
- **CSV requirements**: UTF-8 encoding, comma-separated, header row included
- **JSONL requirements**: One JSON object per line, UTF-8 encoding
- **Compression**: gzip compression for large files (>10MB)
- **Naming convention**: `{platform}_{datatype}_staging_{timestamp}.{ext}`

### Data Quality Requirements
- **Schema compliance**: All data must conform to predefined schemas
- **Completeness**: Required fields must be present and non-null
- **Validity**: Data types and value ranges must be correct
- **Consistency**: Cross-platform data must be harmonized
- **Freshness**: Data must be processed within acceptable time limits

### Transformation Documentation
All transformations must be documented with:
- **Input schema**: Original data structure and format
- **Output schema**: Transformed data structure and format
- **Business rules**: Applied logic and calculations
- **Quality checks**: Validation rules and acceptance criteria
- **Data lineage**: Traceability to source systems

## Pipeline Integration

### ETL Script Coordination
All ETL scripts use standardized patterns and environment configuration:

```python
# Standard ETL script structure
import os
import pandas as pd
from pathlib import Path
from common.utils.config import load_config
from common.utils.validation import validate_data
from common.utils.logging import setup_logging

def main():
    # Load configuration
    config = load_config()
    project_root = Path(os.getenv('PROJECT_ROOT'))
    
    # Setup logging
    logger = setup_logging('staging_processor')
    
    # Process data
    raw_data = load_raw_data(project_root / 'raw' / 'platform')
    cleaned_data = clean_and_transform(raw_data)
    validated_data = validate_data(cleaned_data)
    
    # Save to staging
    output_path = project_root / 'staging' / 'platform'
    save_staging_data(validated_data, output_path)
    
    logger.info(f"Processed {len(validated_data)} records to staging")

if __name__ == "__main__":
    main()
```

### Error Handling & Recovery
```python
# Robust error handling for staging processes
def process_with_error_handling(data_processor, input_data):
    try:
        result = data_processor(input_data)
        return result, None
    except ValidationError as e:
        logger.error(f"Validation failed: {e}")
        # Save problematic data for manual review
        save_error_data(input_data, e)
        return None, e
    except ProcessingError as e:
        logger.error(f"Processing failed: {e}")
        # Attempt recovery with fallback logic
        result = fallback_processor(input_data)
        return result, e
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        # Escalate to monitoring system
        send_alert(f"Staging pipeline failure: {e}")
        raise
```

## Monitoring & Quality Assurance

### Data Quality Metrics
```python
# Daily data quality reporting
def generate_quality_report(date):
    quality_metrics = {
        'completeness': calculate_completeness_score(date),
        'validity': calculate_validity_score(date),
        'consistency': calculate_consistency_score(date),
        'freshness': calculate_freshness_score(date),
        'accuracy': calculate_accuracy_score(date)
    }
    
    # Save quality report
    report_path = f'staging/quality_reports/quality_metrics_{date}.json'
    save_json(quality_metrics, report_path)
    
    # Send alerts for quality issues
    if any(score < 0.95 for score in quality_metrics.values()):
        send_quality_alert(quality_metrics, date)
    
    return quality_metrics
```

### Performance Monitoring
```python
# Processing performance tracking
def track_processing_performance():
    metrics = {
        'processing_time': measure_processing_time(),
        'throughput': calculate_records_per_second(),
        'error_rate': calculate_error_rate(),
        'resource_usage': get_system_resource_usage()
    }
    
    # Log performance metrics
    logger.info(f"Processing performance: {metrics}")
    
    # Store for trend analysis
    save_performance_metrics(metrics)
    
    return metrics
```

## Integration with Ecosystem

### Data Warehouse Integration
Staging data is optimized for efficient loading into the data warehouse:
- **Batch loading**: Optimized batch inserts for large datasets
- **Incremental updates**: Change detection and delta processing
- **Schema evolution**: Automatic schema migration handling
- **Consistency checks**: Validation against warehouse constraints

### Real-time Processing
Staging zone supports near real-time processing for critical data:
- **Stream processing**: Integration with Apache Kafka or similar
- **Change data capture**: Real-time detection of data changes
- **Event-driven processing**: Trigger-based processing workflows
- **Low-latency pipelines**: Optimized processing for time-sensitive data

## Next Steps
Data successfully processed in the staging zone proceeds to the **curated zone** where it undergoes:
1. **Business logic application**: Domain-specific transformations and calculations
2. **Final aggregations**: Summary statistics and roll-up calculations
3. **Performance optimization**: Indexing and partitioning for query performance
4. **Analytics preparation**: Format optimization for consumption by BI tools and dashboards

## Related Documentation
- See `src/*/cleaners/*_raw2staging.py` for platform-specific staging logic
- Reference `data_lake/docs/transformation_rules.md` for detailed transformation specifications
- Check `data_lake/utils/validation/` for data quality validation utilities
- Review `data_lake/config/schemas/` for schema definitions and validation rules
