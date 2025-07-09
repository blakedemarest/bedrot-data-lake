# Data Lake Master Cron Job

## Overview
The BEDROT Data Lake Master Cron Job is a comprehensive automation system that orchestrates the entire ETL pipeline for the data ecosystem. This system ensures reliable, sequential execution of all data extraction, validation, cleaning, and curation processes across multiple platforms and data sources.

## Architecture & Design

### Automated Cron Job Generation
**IMPORTANT: Only edit `run_datalake_cron.bat`!**

The system uses a dual-cron architecture to provide operational flexibility:
- **Primary cron job**: `run_datalake_cron.bat` - Full pipeline including extractors
- **Secondary cron job**: `run_datalake_cron_no_extractors.bat` - Processing-only pipeline

The secondary cron job is automatically generated from the primary using `generate_no_extractors_cron.py`, which runs as the final step of the master cron job. This ensures:
- **Single source of truth**: Only one file to maintain
- **Automatic synchronization**: No manual duplication required
- **Consistent updates**: Both versions always remain in sync
- **Centralized maintenance**: Robust pipeline management

### Pipeline Execution Flow
The master cron job orchestrates a comprehensive workflow:

#### 1. Data Extraction Phase
- **Meta Ads extraction**: Facebook/Instagram advertising data via API
- **DistroKid extraction**: Streaming statistics and sales data via Playwright
- **TooLost extraction**: Analytics and sales reports via web scraping
- **TikTok extraction**: Creator Studio analytics and performance data
- **Linktree extraction**: Click analytics and traffic source data
- **Social media extraction**: Cross-platform engagement metrics

#### 2. Data Validation Phase
- **Schema validation**: Ensuring data structure consistency
- **Quality checks**: Completeness and accuracy verification
- **Freshness validation**: Confirming data currency and relevance
- **Deduplication**: Hash-based duplicate detection and removal

#### 3. Data Processing Phase
- **Landing to raw promotion**: Validated data moved to raw zone
- **Raw to staging transformation**: Data cleaning and standardization
- **Staging to curated promotion**: Business-ready dataset creation
- **Cross-platform aggregation**: Unified analytics dataset generation

#### 4. Analytics and Reporting Phase
- **Performance metrics calculation**: KPI computation and trending
- **Dashboard data preparation**: Real-time analytics feed generation
- **Report generation**: Automated insights and summary reports
- **Data quality monitoring**: Health checks and anomaly detection

## Directory Structure
```
cronjob/
├── run_datalake_cron.bat              # Master cron job (EDIT THIS ONLY)
├── run_datalake_cron_no_extractors.bat # Auto-generated secondary cron
├── generate_no_extractors_cron.py     # Auto-generation script
├── data_lake_cron_flow.dot            # Graphviz pipeline visualization
├── logs/
│   ├── cron_execution_YYYYMMDD.log    # Daily execution logs
│   ├── error_logs/                    # Error and exception logs
│   └── performance_metrics/           # Pipeline performance data
└── config/
    ├── schedule_config.json           # Scheduling configuration
    └── pipeline_dependencies.json     # Task dependency mapping
```

## Scheduling Configuration

### Windows Task Scheduler Setup
The cron job is configured to run using Windows Task Scheduler with the following schedule:
- **Frequency**: Every Monday, Wednesday, and Friday
- **Time**: Random time between 6:00 AM - 9:00 AM
- **Program**: `run_datalake_cron.bat`
- **Working directory**: Project root directory (`PROJECT_ROOT`)

### Schedule Configuration Example
```json
{
  "schedule": {
    "frequency": "tri-weekly",
    "days": ["monday", "wednesday", "friday"],
    "time_window": {
      "start": "06:00",
      "end": "09:00",
      "randomize": true
    },
    "timezone": "UTC"
  },
  "retry_policy": {
    "max_retries": 3,
    "retry_delay_minutes": 30,
    "exponential_backoff": true
  },
  "notifications": {
    "on_success": true,
    "on_failure": true,
    "email_recipients": ["admin@bedrotproductions.com"]
  }
}
```

## Pipeline Dependencies & Execution Order

### Platform-Specific Processing Order
1. **Meta Ads Pipeline**
   - `meta_daily_campaigns_extractor.py` → Landing zone
   - `metaads_daily_landing2raw.py` → Raw zone
   - `metaads_daily_raw2staging.py` → Staging zone
   - `metaads_daily_staging2curated.py` → Curated zone

2. **DistroKid Pipeline**
   - `dk_auth.py` → Landing zone
   - `validate_dk_html.py` → Validation
   - `distrokid_landing2raw.py` → Raw zone
   - `distrokid_raw2staging.py` → Staging zone
   - `distrokid_staging2curated.py` → Curated zone

3. **TooLost Pipeline**
   - `toolost_extractor.py` → Landing zone
   - `validate_toolost_json.py` → Validation
   - `toolost_landing2raw.py` → Raw zone
   - `toolost_raw2staging.py` → Staging zone
   - `toolost_staging2curated.py` → Curated zone

4. **Cross-Platform Integration**
   - Data aggregation across platforms
   - Unified analytics dataset creation
   - Dashboard data feed generation
   - Performance metric calculation

### Dependency Visualization
The execution order and dependencies are documented in `data_lake_cron_flow.dot`:
```bash
# Render the pipeline visualization
dot -Tpng data_lake_cron_flow.dot -o pipeline_flow.png
```

## Environment Configuration

### Required Environment Variables
```bash
# Core configuration
PROJECT_ROOT=C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake
PYTHONPATH=%PROJECT_ROOT%\src

# Platform API credentials
META_ACCESS_TOKEN=your_meta_access_token
META_AD_ACCOUNT_ID=act_your_account_id
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

# Database configuration
DATABASE_PATH=%PROJECT_ROOT%\..\data-warehouse\bedrot_analytics.db

# Logging configuration
LOG_LEVEL=INFO
LOG_DIRECTORY=%PROJECT_ROOT%\cronjob\logs
```

### Dependencies & Prerequisites
- **Python 3.8+**: Required for all ETL scripts
- **Playwright**: For web scraping automation (DistroKid, TooLost, TikTok)
- **Pandas/NumPy**: For data processing and analysis
- **Requests**: For API integrations (Meta Ads, Spotify)
- **SQLite**: For local data storage and caching
- **Graphviz**: For pipeline visualization (optional)

## Error Handling & Recovery

### Error Management Strategy
- **Graceful failures**: Individual platform failures don't stop entire pipeline
- **Retry mechanisms**: Automatic retry for transient failures
- **Error logging**: Comprehensive error tracking and reporting
- **Recovery procedures**: Manual intervention procedures for critical failures

### Common Issues & Solutions

#### Authentication Failures
```bash
# DistroKid/TooLost login issues
- Check cookie files in src/*/cookies/
- Verify 2FA tokens and session validity
- Update login credentials in secure storage

# Meta Ads API issues
- Verify META_ACCESS_TOKEN validity
- Check API rate limits and quotas
- Ensure ad account permissions
```

#### Data Quality Issues
```bash
# Validation failures
- Review platform-specific validation rules
- Check for source system changes
- Update schema definitions if needed

# Missing data
- Verify extractor execution logs
- Check network connectivity
- Review platform availability status
```

#### Storage Issues
```bash
# Disk space problems
- Monitor storage utilization
- Execute archive cleanup procedures
- Implement data retention policies

# Permission issues
- Verify file system permissions
- Check PROJECT_ROOT accessibility
- Ensure write permissions for all zones
```

## Monitoring & Observability

### Performance Metrics
- **Execution time**: Total pipeline duration tracking
- **Success rate**: Percentage of successful executions
- **Data volume**: Amount of data processed per run
- **Error rate**: Frequency and types of errors encountered

### Health Checks
- **Data freshness**: Verification of recent data availability
- **Pipeline completion**: Confirmation of all stages completion
- **Data quality**: Validation of processed data integrity
- **Resource utilization**: Monitoring of system resource usage

### Alerting System
- **Email notifications**: Success/failure notifications to administrators
- **Log monitoring**: Automated log analysis for error patterns
- **Performance alerts**: Notifications for degraded performance
- **Capacity alerts**: Warnings for resource constraints

## Operational Procedures

### Manual Execution
```bash
# Run full pipeline manually
cd "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake"
cronjob\run_datalake_cron.bat

# Run processing-only pipeline (skip extractors)
cronjob\run_datalake_cron_no_extractors.bat

# Run individual platform pipeline
python src\metaads\extractors\meta_daily_campaigns_extractor.py
python src\metaads\cleaners\metaads_daily_landing2raw.py
python src\metaads\cleaners\metaads_daily_raw2staging.py
python src\metaads\cleaners\metaads_daily_staging2curated.py
```

### Troubleshooting Commands
```bash
# Check recent execution logs
type cronjob\logs\cron_execution_20240522.log

# Verify environment configuration
echo %PROJECT_ROOT%
echo %PYTHONPATH%

# Test individual components
python src\common\utils\test_connectivity.py
python src\common\utils\validate_environment.py
```

### Maintenance Tasks
- **Weekly**: Review execution logs and performance metrics
- **Monthly**: Update dependency versions and security patches
- **Quarterly**: Review and optimize pipeline performance
- **Annually**: Comprehensive security and compliance audit

## Integration with Broader Ecosystem

### Data Warehouse Integration
- **Automatic loading**: Curated data loaded into SQLite warehouse
- **Schema synchronization**: Warehouse schemas updated with data lake changes
- **Performance optimization**: Optimized data formats for analytical queries

### Dashboard Integration
- **Real-time feeds**: Live data streams to dashboard backend
- **API endpoints**: RESTful APIs for dashboard data consumption
- **WebSocket updates**: Real-time dashboard updates via WebSocket connections

### External System Integration
- **MinIO storage**: Optional object storage for large datasets
- **Cloud backup**: Automated backup to cloud storage providers
- **Third-party APIs**: Integration with external analytics platforms

## Future Enhancements

### Planned Improvements
- **Containerization**: Docker-based deployment for improved portability
- **Cloud migration**: AWS/Azure deployment with managed services
- **Stream processing**: Real-time data processing capabilities
- **Machine learning**: Automated anomaly detection and predictive analytics

### Scalability Considerations
- **Multi-node deployment**: Distributed processing capabilities
- **Load balancing**: Request distribution across multiple instances
- **Auto-scaling**: Dynamic resource allocation based on demand
- **Performance optimization**: Continuous performance monitoring and optimization

## Related Documentation
- See `data_lake/docs/pipeline_architecture.md` for detailed technical architecture
- Reference `data_lake/docs/troubleshooting_guide.md` for comprehensive troubleshooting
- Check `data_lake/scripts/pipeline_monitoring.py` for monitoring utilities
- Review `data_lake/config/` for configuration templates and examples

---
**Remember to update this documentation as the pipeline evolves and new features are added!**