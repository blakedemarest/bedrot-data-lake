# Raw Zone

## Purpose
The raw zone serves as the immutable, validated single source of truth for all data within the BEDROT Data Lake. This zone stores exact copies of source data that have passed initial validation checks, ensuring data integrity and providing a reliable foundation for all downstream processing and analytics.

## What Goes Here
- **Validated landing zone data**: Source data that has passed automated validation checks
- **Immutable data copies**: Exact replicas of source systems with original structure preserved
- **Granular datasets**: Data in its most atomic, unprocessed form
- **Historical data lineage**: Complete audit trail linking back to original sources
- **Platform-specific raw data**: Validated extracts from all integrated platforms

### Platform-Specific Data Types

#### DistroKid
- **HTML snapshots**: Validated streaming statistics pages (e.g., `streams_stats_20240522_143022.html`)
- **TSV downloads**: Raw tabular exports from DistroKid dashboard
- **Sales reports**: Unprocessed financial transaction data
- **Validation requirements**: Only files passing `src/distrokid/extractors/validate_dk_html.py` are promoted

#### TooLost Analytics
- **JSON responses**: Complete API response payloads from TooLost platform
- **Spotify data**: Raw streaming metrics and audience demographics  
- **Apple Music data**: Platform-specific engagement and performance metrics
- **Validation pipeline**: Processed through `src/toolost/validate_toolost_json.py`

#### Meta Ads
- **Campaign data**: Raw Facebook/Instagram advertising campaign information
- **Ad performance**: Unprocessed metrics including reach, impressions, clicks
- **Audience insights**: Demographic and behavioral targeting data
- **Financial data**: Spend, cost-per-click, and conversion metrics

#### TikTok
- **Analytics exports**: Raw TikTok Creator Studio data exports
- **Video performance**: Individual video metrics and engagement data
- **Audience data**: Follower demographics and growth metrics
- **Trend data**: Hashtag and sound performance information

#### Social Media Platforms
- **Linktree analytics**: Click-through rates and traffic source data
- **YouTube metrics**: Video performance and channel analytics
- **Spotify for Artists**: Streaming data and listener demographics

## Directory Structure
```
raw/
├── distrokid/
│   ├── streams/
│   │   └── 2024/
│   │       ├── 05/
│   │       │   ├── streams_stats_20240522_143022.html
│   │       │   └── streams_stats_20240523_091500.html
│   │       └── 06/
│   └── sales/
│       └── 2024/
│           └── sales_report_20240601.tsv
├── toolost/
│   ├── analytics/
│   │   └── 2024/
│   │       ├── toolost_analytics_20240522_140530.json
│   │       └── toolost_analytics_20240523_140730.json
│   └── spotify/
│       └── 2024/
│           └── spotify_metrics_20240522.json
├── metaads/
│   ├── campaigns/
│   │   └── 2024/
│   │       └── 05/
│   │           ├── campaigns_20240522.json
│   │           ├── adsets_20240522.json
│   │           └── insights_20240522.json
│   └── daily/
│       └── 2024/
│           └── metaads_campaign_daily_20240522_083045.csv
├── tiktok/
│   ├── analytics/
│   │   └── 2024/
│   │       └── tiktok_analytics_20240522.json
│   └── videos/
│       └── 2024/
│           └── video_performance_20240522.csv
└── social_media/
    ├── linktree/
    │   └── 2024/
    │       └── linktree_analytics_20240522_120000.json
    └── youtube/
        └── 2024/
            └── channel_analytics_20240522.json
```

## Data Validation & Quality Standards

### Validation Pipeline
Each platform implements specific validation before promotion to raw zone:

#### DistroKid Validation
```python
# Automated validation via src/distrokid/extractors/validate_dk_html.py
- HTML structure validation
- Required fields presence check
- Data type validation
- Timestamp consistency verification
```

#### TooLost Validation  
```python
# Processed through src/toolost/validate_toolost_json.py
- JSON schema validation
- API response completeness check
- Data freshness validation
- Platform consistency verification
```

#### Meta Ads Validation
```python
# Campaign data validation
- API response structure validation
- Metric completeness verification
- Date range consistency check
- Account-level data integrity
```

### Data Quality Requirements
- **Schema compliance**: All data must match predefined schemas
- **Completeness**: Required fields must be present and non-null
- **Freshness**: Data must be within acceptable age limits
- **Consistency**: Cross-platform data must align temporally
- **Integrity**: Checksums and hash validation for all files

## Raw Zone Rules & Standards

### Immutability Principles
- **Append-only**: Data can only be added, never modified or deleted
- **No transformations**: Data must remain in original format and structure
- **Version control**: All changes tracked with timestamps and source information
- **Audit trail**: Complete lineage from source system to raw zone

### Storage Standards
- **Compression**: Files compressed for storage efficiency (gzip, parquet compression)
- **Partitioning**: Data organized by platform, year, month, day for efficient access
- **Naming conventions**: Consistent timestamp-based naming (`platform_type_YYYYMMDD_HHMMSS.ext`)
- **Metadata inclusion**: Source system, extraction timestamp, validation status

### Access Patterns
- **Read-only access**: Raw zone data is immutable once written
- **Batch processing**: Optimized for sequential reading by downstream processes
- **Time-based queries**: Efficient access by date ranges for historical analysis
- **Platform isolation**: Each platform's data independently accessible

## Integration with Data Lake Pipeline

### Promotion from Landing
Data flows to raw zone from landing after:
1. **Initial validation**: Schema and format verification
2. **Quality checks**: Completeness and consistency validation  
3. **Deduplication**: Hash-based duplicate detection and handling
4. **Metadata enrichment**: Addition of processing timestamps and lineage information

### Data Lineage Tracking
Each raw zone file includes comprehensive metadata:
- **Source system**: Original platform or API endpoint
- **Extraction timestamp**: When data was originally captured
- **Validation timestamp**: When data passed quality checks
- **File hash**: SHA-256 checksum for integrity verification
- **Processing pipeline**: Which extractor and validation scripts were used

## Historical Data Management

### Retention Policies
- **Short-term retention**: Recent data (last 90 days) for operational analytics
- **Medium-term retention**: Historical data (1-2 years) for trend analysis
- **Long-term archival**: Older data moved to archive zone per retention policies
- **Compliance requirements**: Legal and regulatory retention mandates

### Change Tracking
- **2025-05-22**: TooLost analytics scraper enhanced for reliable Spotify/Apple Music extraction
- **2025-05-22**: DistroKid validation pipeline implemented with automated HTML validation
- **2025-06-05**: TooLost extractor flow refactored for improved robustness and modularity
- **Ongoing**: Platform-specific validation rules continuously updated based on source changes

## Data Access & Consumption

### Downstream Consumers
- **Staging zone**: Primary consumer for data cleaning and transformation
- **Data warehouse**: Direct loading of validated raw data for analytics
- **Data quality monitoring**: Automated checks and anomaly detection
- **Compliance reporting**: Audit and regulatory reporting requirements

### Query Patterns
- **Time-based access**: Queries typically filter by date ranges
- **Platform-specific analysis**: Single-platform data analysis and reporting
- **Cross-platform joining**: Combining data across platforms for unified analysis
- **Historical trend analysis**: Long-term pattern identification and forecasting

## Performance Optimization

### Storage Optimization
- **Columnar formats**: Parquet for analytical workloads where appropriate
- **Compression ratios**: Regular monitoring and optimization of compression efficiency
- **Partitioning strategy**: Optimized data organization for common query patterns
- **Index maintenance**: Minimal indexing for essential access paths

### Access Performance
- **Caching layer**: Frequently accessed data cached for improved performance
- **Parallel processing**: Multi-threaded access for large dataset processing
- **Network optimization**: Efficient data transfer protocols and compression
- **Resource monitoring**: Continuous performance monitoring and optimization

## Troubleshooting & Monitoring

### Common Issues
- **Validation failures**: Source data format changes breaking validation rules
- **Storage capacity**: Raw zone growth requiring archive management
- **Performance degradation**: Query performance issues due to data volume growth
- **Data quality problems**: Source system issues affecting data completeness

### Monitoring & Alerting
- **Data freshness**: Alerts for missing or delayed data feeds
- **Validation failures**: Notifications for validation pipeline issues
- **Storage utilization**: Monitoring and alerts for capacity management
- **Performance metrics**: Query performance and throughput monitoring

## Next Steps
Data from the raw zone proceeds to the **staging zone** where it undergoes:
1. **Data cleaning**: Standardization and quality improvement
2. **Schema harmonization**: Consistent structure across platforms
3. **Business rule application**: Domain-specific transformations
4. **Aggregation preparation**: Preparation for analytical consumption

## Related Documentation
- See `src/*/extractors/` for platform-specific extraction logic
- Reference `src/*/cleaners/` for validation and promotion scripts
- Check `data_lake/docs/validation_rules.md` for detailed validation requirements
- Review `data_lake/scripts/raw_zone_monitoring.py` for health checks and metrics
