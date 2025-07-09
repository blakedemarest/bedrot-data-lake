# Landing Zone

## Purpose
The landing zone serves as the initial entry point and staging area for all incoming data into the BEDROT Data Lake. This zone captures data in its original, unprocessed form directly from source systems, APIs, and third-party platforms. The landing zone acts as a buffer that isolates source system variability from downstream processing, ensuring reliable data ingestion regardless of source system changes or temporary outages.

## What Goes Here
- **Raw data files**: Direct exports from external platforms and APIs
- **API responses**: Complete JSON payloads from REST and GraphQL APIs
- **Web scraping outputs**: HTML pages, JSON responses from automated browser sessions
- **File uploads**: Manual data uploads and bulk imports
- **Third-party data feeds**: External data provider deliveries
- **System exports**: Database dumps and application exports
- **Streaming data**: Real-time event feeds and message queue data

## Platform-Specific Data Sources

### Meta Ads Platform
- **Campaign data**: Raw Facebook/Instagram advertising campaigns
- **Performance metrics**: Daily campaign performance and audience insights
- **Financial data**: Spend, cost-per-click, and conversion metrics
- **Pixel events**: E-commerce tracking and conversion data
- **Files**: `meta_ads/YYYYMMDD_HHMMSS/campaigns.json`, `adsets.json`, `ads.json`, `insights.json`

### DistroKid Platform
- **Streaming statistics**: HTML pages from DistroKid dashboard
- **Sales reports**: TSV/Excel files with revenue and payout data
- **Apple Music stats**: Platform-specific performance metrics
- **Files**: `distrokid/streams_stats_YYYYMMDD_HHMMSS.html`, `sales_report_YYYYMMDD.tsv`

### TooLost Analytics
- **Analytics JSON**: Complete platform analytics API responses
- **Spotify metrics**: Streaming data and audience demographics
- **Apple Music data**: Platform-specific engagement metrics
- **Sales notifications**: Revenue and payout notifications
- **Files**: `toolost/analytics_YYYYMMDD_HHMMSS.json`, `spotify_metrics_YYYYMMDD.json`

### TikTok Creator Studio
- **Video analytics**: Individual video performance metrics
- **Account analytics**: Overall account performance and growth
- **Audience data**: Follower demographics and engagement patterns
- **Trend data**: Hashtag and sound performance information
- **Files**: `tiktok/analytics_YYYYMMDD_HHMMSS.json`, `video_performance_YYYYMMDD.csv`

### Social Media Platforms
- **Linktree analytics**: Click-through rates and traffic sources
- **YouTube metrics**: Video and channel performance data
- **Spotify for Artists**: Streaming metrics and listener insights
- **Instagram insights**: Post performance and follower analytics
- **Files**: Platform-specific JSON and CSV formats with timestamp prefixes

## Directory Structure
```
landing/
├── metaads/
│   ├── 20240522_083045/
│   │   ├── campaigns.json
│   │   ├── adsets.json
│   │   ├── ads.json
│   │   └── insights.json
│   └── daily/
│       └── metaads_campaign_daily_20240522_083045.csv
├── distrokid/
│   ├── streams/
│   │   ├── streams_stats_20240522_143022.html
│   │   └── streams_stats_20240523_091500.html
│   └── sales/
│       └── sales_report_20240601.tsv
├── toolost/
│   ├── analytics/
│   │   ├── toolost_analytics_20240522_140530.json
│   │   └── toolost_analytics_20240523_140730.json
│   └── notifications/
│       └── sales_notifications_20240522.json
├── tiktok/
│   ├── analytics/
│   │   └── tiktok_analytics_20240522.json
│   └── videos/
│       └── video_performance_20240522.csv
├── social_media/
│   ├── linktree/
│   │   └── linktree_analytics_20240522_120000.json
│   ├── youtube/
│   │   └── channel_analytics_20240522.json
│   └── spotify/
│       └── artist_metrics_20240522.json
└── manual_uploads/
    ├── financial_data/
    └── external_reports/
```

## Data Ingestion Rules & Standards

### File Integrity Requirements
- **Original format preservation**: Data must remain in source system format
- **No modifications**: Zero alterations or preprocessing allowed
- **Read-only status**: Files become immutable once written
- **Complete captures**: Full API responses and complete file downloads
- **Metadata inclusion**: Source system, extraction timestamp, and method

### Naming Conventions
- **Timestamp format**: `YYYYMMDD_HHMMSS` for precise chronological ordering
- **Platform prefixes**: Clear identification of source system
- **File extensions**: Preserve original extensions (`.json`, `.html`, `.csv`, `.tsv`)
- **No spaces**: Use underscores for readability and system compatibility
- **Version indicators**: Include version numbers for schema changes

### Quality Assurance
- **Checksum validation**: SHA-256 hashes for file integrity verification
- **Size validation**: Minimum and maximum file size checks
- **Format validation**: Basic format verification (valid JSON, readable HTML)
- **Completeness checks**: Verification of required fields and data structures
- **Duplicate detection**: Hash-based duplicate identification

## Recent Updates & Changelog

### 2025-06-05: TooLost Extractor Flow Refactor
- **Enhanced extraction flow**: TooLost Playwright extractor now completes analytics extraction (Spotify/Apple) before sales report navigation
- **Improved robustness**: All Playwright-based extractors handle login/2FA gracefully
- **Modular architecture**: Standardized extraction patterns for future platform additions
- **Path standardization**: All outputs use PROJECT_ROOT and follow zone conventions

### 2025-05-22: DistroKid Automation Enhancement
- **Automated streaming data**: Playwright automation for DistroKid streaming and Apple Music statistics
- **Timestamp integration**: HTML page sources saved with datetime-stamped filenames
- **Validation pipeline**: Automated validation before promotion to raw zone
- **Error handling**: Robust error handling for authentication and page load issues

### 2025-05-22: Meta Ads API Integration
- **Daily campaign extraction**: Enhanced daily-level performance extraction with campaign activity tracking
- **Pixel event aggregation**: Meta Pixel events (ViewContent, AddToCart, Purchase) extraction
- **Activity management**: Campaign activity tracking with automatic exclusion of inactive campaigns
- **Rate limit handling**: Robust API rate limit management and retry logic

## Data Flow & Processing

### Extraction Methods

#### API-Based Extraction
```python
# Meta Ads API extraction example
import requests
from datetime import datetime

def extract_meta_campaigns():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    landing_path = f'landing/metaads/{timestamp}/'
    
    # Extract campaigns, adsets, ads, insights
    # Save to timestamped directory
    # Include metadata and checksums
```

#### Web Scraping Extraction  
```python
# DistroKid Playwright extraction example
from playwright.sync_api import sync_playwright

def extract_distrokid_stats():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # Navigate to DistroKid dashboard
        # Extract streaming statistics
        # Save HTML with timestamp
        # Handle authentication and 2FA
```

#### Manual Upload Processing
```python
# Manual file upload handling
def process_manual_upload(file_path, platform, data_type):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    destination = f'landing/{platform}/{data_type}_{timestamp}'
    # Validate file format and size
    # Calculate checksums
    # Move to landing zone with metadata
```

### Validation Pipeline
Before promotion to raw zone, data undergoes platform-specific validation:

#### DistroKid Validation
- **HTML structure validation**: Ensure required elements and data fields present
- **Content verification**: Validate streaming statistics and financial data
- **Timestamp consistency**: Verify data freshness and chronological order
- **Schema compliance**: Check against expected DistroKid data structure

#### TooLost Validation
- **JSON schema validation**: Verify API response structure and required fields
- **Data completeness**: Ensure all expected metrics and dimensions present
- **Platform consistency**: Validate cross-platform data alignment
- **Freshness checks**: Confirm data is within acceptable age limits

#### Meta Ads Validation
- **API response validation**: Verify campaign, adset, and ad data structure
- **Metric completeness**: Ensure all required performance metrics present
- **Date range consistency**: Validate temporal data alignment
- **Account integrity**: Verify data belongs to correct ad account

## Integration with ETL Pipeline

### Automated Promotion
Valid data is automatically promoted from landing to raw zone through:
1. **Scheduled validation**: Regular validation runs via cron job
2. **Real-time monitoring**: File system watchers for immediate processing
3. **Quality gates**: Multi-stage validation before promotion
4. **Error handling**: Failed validations logged and quarantined

### Data Lineage Tracking
Each landing zone file includes comprehensive metadata:
- **Source system**: Platform or API endpoint
- **Extraction method**: API, web scraping, manual upload
- **Extraction timestamp**: Precise capture time
- **Extractor version**: Script version for reproducibility
- **Data freshness**: Source system data timestamp
- **File integrity**: SHA-256 checksum for validation

## Monitoring & Observability

### Health Checks
- **Data freshness monitoring**: Alerts for missing or delayed data
- **Extraction failure detection**: Monitoring for failed extraction jobs
- **Storage utilization**: Tracking landing zone disk usage
- **Validation pipeline health**: Monitoring validation success rates

### Performance Metrics
- **Extraction latency**: Time from source to landing zone
- **File processing rate**: Number of files processed per hour
- **Error rates**: Frequency of extraction and validation failures
- **Storage efficiency**: Compression ratios and space utilization

### Alerting System
- **Real-time notifications**: Immediate alerts for critical failures
- **Daily summary reports**: Comprehensive processing summaries
- **Trend analysis**: Long-term pattern identification
- **Capacity planning**: Proactive resource management alerts

## Troubleshooting Common Issues

### Authentication Problems
- **Cookie expiration**: Update authentication cookies for web scraping
- **API token issues**: Refresh OAuth tokens and API credentials
- **2FA challenges**: Handle two-factor authentication flows
- **Rate limiting**: Implement proper backoff and retry strategies

### Data Quality Issues
- **Format changes**: Adapt to source system schema changes
- **Missing data**: Investigate source system outages or changes
- **Duplicate data**: Enhance deduplication logic and hash validation
- **Incomplete extractions**: Improve error handling and retry mechanisms

### Performance Problems
- **Slow extractions**: Optimize API calls and web scraping performance
- **Storage bottlenecks**: Implement efficient file I/O and compression
- **Network issues**: Add robust network error handling and retries
- **Resource constraints**: Monitor and optimize system resource usage

## Security & Compliance

### Data Protection
- **Encryption at rest**: All sensitive data encrypted in storage
- **Access controls**: Role-based access to landing zone data
- **Audit logging**: Complete audit trail of data access and modifications
- **Data masking**: Automatic masking of PII and sensitive information

### Compliance Requirements
- **GDPR compliance**: Data subject rights and privacy protection
- **Data retention**: Automated retention policy enforcement
- **Cross-border transfers**: Appropriate safeguards for international data
- **Regulatory reporting**: Compliance reporting and documentation

## Next Steps
Data successfully landing in this zone proceeds through the following pipeline:
1. **Validation**: Platform-specific validation rules and quality checks
2. **Raw zone promotion**: Validated data moved to immutable raw storage
3. **Processing pipeline**: Structured data cleaning and transformation
4. **Business intelligence**: Analytics-ready data for reporting and insights

## Related Documentation
- See `src/*/extractors/` for platform-specific extraction scripts
- Reference `src/*/cleaners/` for validation and promotion logic
- Check `data_lake/docs/extraction_guidelines.md` for extraction best practices
- Review `data_lake/scripts/landing_zone_monitoring.py` for monitoring tools
