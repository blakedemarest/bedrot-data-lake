# DistroKid ETL Pipeline

## Overview
The DistroKid ETL pipeline provides comprehensive automation for extracting, validating, and processing streaming analytics and sales data from the DistroKid platform. This pipeline handles the complete data flow from web scraping through to analytics-ready datasets, supporting both streaming statistics and financial reporting requirements.

## Architecture & Components

### Directory Structure
```
distrokid/
├── extractors/
│   ├── dk_auth.py                    # Main Playwright automation script
│   ├── validate_dk_html.py          # HTML validation and quality checks
│   └── cookie_manager.py            # Session and authentication management
├── cleaners/
│   ├── distrokid_landing2raw.py     # Landing to raw zone promotion
│   ├── distrokid_raw2staging.py     # Raw to staging transformation
│   └── distrokid_staging2curated.py # Staging to curated finalization
├── cookies/
│   ├── distrokid_session.json       # Saved authentication cookies
│   └── session_backup.json          # Backup authentication state
└── schemas/
    ├── streaming_data_schema.json    # Expected streaming data structure
    └── sales_data_schema.json        # Expected sales data structure
```

## Data Sources & Extraction

### Streaming Statistics
- **Source**: DistroKid dashboard streaming statistics pages
- **Data Types**: Daily streaming counts, revenue, platform breakdowns
- **Platforms Covered**: Spotify, Apple Music, YouTube Music, Amazon Music, and others
- **Update Frequency**: Daily (automated via cron job)
- **File Format**: HTML pages saved with timestamp

### Sales Reports
- **Source**: DistroKid sales reporting section
- **Data Types**: Revenue, payouts, territory breakdowns, transaction details
- **Platforms Covered**: All digital music platforms in DistroKid network
- **Update Frequency**: Monthly or on-demand
- **File Format**: TSV/CSV downloads

### Artist Performance Data
- **Source**: Artist-specific performance dashboards
- **Data Types**: Track-level performance, audience demographics, geographic data
- **Metrics**: Streams, saves, playlist additions, listener demographics
- **Granularity**: Track-level and artist-level aggregations

## Extraction Process

### Automated Web Scraping
```python
# Main extraction workflow
from src.distrokid.extractors.dk_auth import DistroKidExtractor

# Initialize extractor with configuration
extractor = DistroKidExtractor(
    headless=True,
    save_cookies=True,
    timeout=30000
)

# Execute extraction
results = await extractor.extract_streaming_data()

# Results include:
# - HTML files saved to landing zone
# - Extraction metadata and statistics
# - Error reports and validation status
```

### Authentication Management
- **Cookie-based sessions**: Persistent login state across extractions
- **2FA handling**: Automated two-factor authentication flow
- **Session validation**: Pre-extraction authentication verification
- **Credential security**: Secure storage of login credentials
- **Session recovery**: Automatic re-authentication on session expiry

### Error Handling & Resilience
- **Network timeouts**: Configurable timeout and retry logic
- **Page load failures**: Dynamic waiting and retry mechanisms
- **Authentication failures**: Automatic credential refresh and re-login
- **Rate limiting**: Respectful request pacing and delay management
- **Partial failures**: Graceful handling of incomplete data extraction

## Data Processing Pipeline

### Landing to Raw Zone (validation)
```python
# Validation and promotion script
python src/distrokid/cleaners/distrokid_landing2raw.py

# Validation steps:
# 1. HTML structure validation
# 2. Required data element presence check
# 3. Data consistency verification
# 4. Timestamp and freshness validation
# 5. File integrity and size checks
```

### Raw to Staging Zone (cleaning)
```python
# Data cleaning and standardization
python src/distrokid/cleaners/distrokid_raw2staging.py

# Transformation steps:
# 1. HTML parsing and data extraction
# 2. Date/time standardization
# 3. Numeric value cleaning and conversion
# 4. Artist and track name normalization
# 5. Platform code standardization
# 6. Currency conversion to USD
```

### Staging to Curated Zone (business logic)
```python
# Business logic application and finalization
python src/distrokid/cleaners/distrokid_staging2curated.py

# Business transformations:
# 1. Revenue allocation and attribution
# 2. Performance metric calculations
# 3. Trend analysis and rolling averages
# 4. Cross-platform aggregations
# 5. Artist performance scoring
```

## Output Datasets

### Daily Streaming Data
**File**: `curated/streaming/daily_streams_distrokid.csv`

**Schema**:
```csv
date,artist_name,track_name,platform,streams,revenue_usd,country,source_timestamp
2024-05-22,Artist Name,Track Title,spotify,1250,2.45,US,2024-05-22 14:30:22
```

**Key Metrics**:
- Daily stream counts by track and platform
- Revenue attribution per stream
- Geographic distribution
- Platform performance comparison

### Monthly Sales Summary
**File**: `curated/financial/distrokid_sales_monthly.csv`

**Schema**:
```csv
month,artist_name,total_revenue_usd,total_streams,avg_revenue_per_stream,top_platform,top_country
2024-05,Artist Name,156.78,12450,0.0126,spotify,US
```

### Artist Performance Analytics
**File**: `curated/analytics/distrokid_artist_performance.parquet`

**Metrics**:
- Monthly growth rates
- Platform diversification scores
- Audience engagement metrics
- Revenue trend analysis
- Comparative performance benchmarks

## Configuration & Environment

### Required Environment Variables
```bash
# Core configuration
PROJECT_ROOT=/path/to/data_lake
DISTROKID_USERNAME=your_username
DISTROKID_PASSWORD=your_secure_password

# Extraction settings
DK_EXTRACTION_TIMEOUT=30000
DK_HEADLESS_MODE=true
DK_SAVE_SCREENSHOTS=false

# Data processing
DK_VALIDATION_STRICT=true
DK_CURRENCY_CONVERSION=true
DK_ARTIST_NORMALIZATION=true
```

### Dependencies
```bash
# Required Python packages
playwright>=1.30.0
pandas>=1.5.0
beautifulsoup4>=4.11.0
requests>=2.28.0
numpy>=1.21.0

# Playwright browser installation
playwright install chromium
```

## Usage Examples

### Manual Extraction
```bash
# Navigate to data lake directory
cd "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake"

# Run complete extraction pipeline
python src/distrokid/extractors/dk_auth.py
python src/distrokid/cleaners/distrokid_landing2raw.py
python src/distrokid/cleaners/distrokid_raw2staging.py
python src/distrokid/cleaners/distrokid_staging2curated.py
```

### Automated Scheduling
```bash
# Scheduled via Windows Task Scheduler
# Runs Monday, Wednesday, Friday at 6:00 AM
# See cronjob/run_datalake_cron.bat for full pipeline
```

### Custom Data Processing
```python
# Custom processing example
import pandas as pd
from src.distrokid.cleaners.data_processor import DistroKidProcessor

# Load raw data
processor = DistroKidProcessor()
raw_data = processor.load_raw_streaming_data('2024-05-22')

# Apply custom transformations
cleaned_data = processor.clean_streaming_data(raw_data)
enhanced_data = processor.add_performance_metrics(cleaned_data)

# Save to custom location
enhanced_data.to_csv('custom_output/enhanced_streaming_data.csv')
```

## Data Quality & Monitoring

### Validation Rules
- **HTML structure**: Required elements and data sections present
- **Data completeness**: All expected fields populated
- **Data ranges**: Streaming counts and revenue within reasonable ranges
- **Date consistency**: Extraction dates align with expected reporting periods
- **Cross-validation**: Data consistency across related fields

### Quality Metrics
```python
# Quality assessment example
from src.distrokid.utils.quality_checker import QualityChecker

checker = QualityChecker()
quality_report = checker.assess_data_quality('2024-05-22')

# Quality report includes:
# - Completeness score (0-1)
# - Validity score (0-1)
# - Consistency score (0-1)
# - Freshness score (0-1)
# - Overall quality score
```

### Monitoring & Alerting
- **Extraction failures**: Immediate alerts for failed extractions
- **Data quality issues**: Notifications for quality score drops
- **Volume anomalies**: Alerts for unexpected data volume changes
- **Processing delays**: Monitoring for pipeline processing time increases

## Troubleshooting

### Common Issues

#### Authentication Problems
```bash
# Check cookie validity
python src/distrokid/utils/check_authentication.py

# Clear and refresh cookies
python src/distrokid/extractors/cookie_manager.py --refresh

# Manual login verification
python src/distrokid/extractors/dk_auth.py --manual-login
```

#### Data Extraction Failures
```bash
# Check page structure changes
python src/distrokid/utils/validate_page_structure.py

# Run extraction with debug mode
python src/distrokid/extractors/dk_auth.py --debug --save-screenshots

# Validate extracted HTML
python src/distrokid/extractors/validate_dk_html.py --file=landing/distrokid/latest.html
```

#### Processing Errors
```bash
# Validate raw data structure
python src/distrokid/utils/validate_raw_data.py

# Test cleaning pipeline
python src/distrokid/cleaners/distrokid_raw2staging.py --test-mode

# Check schema compliance
python src/distrokid/utils/schema_validator.py
```

### Performance Optimization
- **Extraction speed**: Optimize Playwright settings and selectors
- **Processing efficiency**: Implement parallel processing for large datasets
- **Memory usage**: Optimize pandas operations and data types
- **Storage optimization**: Compress output files and implement efficient formats

## Integration Points

### Data Warehouse Integration
- **Automatic loading**: Curated data automatically loaded into SQLite warehouse
- **Schema synchronization**: Database schemas updated with data structure changes
- **Incremental updates**: Efficient delta processing for large datasets

### Dashboard Integration
- **Real-time feeds**: Live streaming data for dashboard displays
- **API endpoints**: RESTful APIs for dashboard data consumption
- **WebSocket updates**: Real-time notifications for new data availability

### Analytics Platform Integration
- **Business intelligence**: Prepared datasets for BI tool consumption
- **Machine learning**: Feature-ready data for predictive modeling
- **Reporting automation**: Automated report generation and distribution

## Future Enhancements

### Planned Improvements
- **Real-time streaming**: Move from batch to real-time data extraction
- **Advanced analytics**: Implement predictive streaming performance models
- **Multi-account support**: Support for multiple DistroKid accounts
- **Enhanced validation**: ML-based anomaly detection for data quality

### Scalability Considerations
- **Cloud deployment**: Migration to cloud-based extraction infrastructure
- **Horizontal scaling**: Distributed processing for multiple accounts/artists
- **API integration**: Direct API access when available from DistroKid
- **Stream processing**: Real-time data processing and analytics

## Related Documentation
- See `data_lake/docs/distrokid_integration.md` for detailed integration guide
- Reference `data_lake/schemas/distrokid/` for complete schema documentation
- Check `data_lake/tests/distrokid/` for comprehensive test suite
- Review `data_lake/examples/distrokid/` for usage examples and tutorials
