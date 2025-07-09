# Authentication Workflow for BEDROT Data Pipeline

This document describes the semi-automated authentication workflow for the BEDROT data pipeline, which handles services requiring login credentials.

## Overview

The pipeline supports both manual and automated modes for services requiring authentication:
- **Manual Mode**: Opens a browser for interactive login and saves cookies
- **Automated Mode**: Uses saved cookies for headless extraction
- **Smart Detection**: Automatically determines when manual authentication is needed

## Quick Start

### 1. Check Pipeline Health
```bash
cd data_lake
python src/common/monitor_pipeline_health.py
```

This shows:
- Data freshness for each service
- Cookie status and expiration
- Required actions

### 2. Run Pipeline with Authentication Checks
```bash
# Interactive mode (prompts for manual auth when needed)
python src/common/run_with_auth_check.py

# Check authentication status only
python src/common/run_with_auth_check.py --check-only

# Force manual authentication for specific services
python src/common/run_with_auth_check.py toolost spotify --manual
```

### 3. Run Full Pipeline
```bash
# With authentication wrapper
cd data_lake
set PYTHONPATH=%CD%\src;%PYTHONPATH%
python src/common/run_with_auth_check.py
cronjob/run_datalake_cron_no_extractors.bat

# Traditional method (may fail if cookies expired)
cronjob/run_datalake_cron.bat
```

## Service-Specific Instructions

### TooLost

**Unified Extractor** (Recommended):
```bash
# Automatic mode detection
python src/toolost/extractors/toolost_unified_extractor.py

# Force manual login
python src/toolost/extractors/toolost_unified_extractor.py --manual

# Run headless (automated only)
python src/toolost/extractors/toolost_unified_extractor.py --headless
```

**Important**: The unified extractor:
- Automatically detects if manual login is needed
- Saves data to `landing/toolost/` (standardized location)
- Supports both manual and automated modes
- Cookie expiration: 7 days

### Spotify

```bash
# Manual login (when cookies expire)
python src/spotify/extractors/spotify_login.py

# Automated extraction
python src/spotify/extractors/spotify_audience_extractor.py
```

Cookie expiration: 30 days

### DistroKid

```bash
# Manual login
python src/distrokid/extractors/distrokid_login.py

# Automated extractors
python src/distrokid/extractors/distrokid_bank_extractor.py
python src/distrokid/extractors/distrokid_streams_extractor.py
```

Cookie expiration: 14 days

### TikTok

```bash
# Manual login
python src/tiktok/extractors/tiktok_login.py

# Automated extraction
python src/tiktok/extractors/tiktok_analytics_extractor.py
```

Cookie expiration: 7 days

## Automation Strategies

### 1. Semi-Automated Daily Pipeline

Create a scheduled task that:
1. Runs the health monitor
2. Sends alerts for services needing manual auth
3. Runs automated extractors for services with valid cookies

Example batch script:
```batch
@echo off
cd /d "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake"

REM Check pipeline health
python src/common/monitor_pipeline_health.py

REM Run with authentication checks in automated mode
set AUTOMATED_MODE=true
python src/common/run_with_auth_check.py

REM Run cleaners regardless
cronjob/run_datalake_cron_no_extractors.bat
```

### 2. Weekly Manual Refresh

Schedule a weekly reminder to:
1. Run the health monitor
2. Manually refresh any expiring cookies
3. Verify all services are operational

```bash
# Weekly refresh command
python src/common/run_with_auth_check.py --check-only
# Then manually refresh any services showing as expired
```

### 3. Cron Job Integration

For Linux/WSL environments:
```bash
# Check and run with notifications
0 8 * * * cd /path/to/data_lake && python src/common/monitor_pipeline_health.py | mail -s "Pipeline Health Report" your@email.com

# Run automated extraction for healthy services
0 9 * * * cd /path/to/data_lake && AUTOMATED_MODE=true python src/common/run_with_auth_check.py >> logs/auth_extraction.log 2>&1
```

## Troubleshooting

### Common Issues

1. **"Not logged in and running in automated mode"**
   - Cookies have expired
   - Run manual authentication: `python src/[service]/extractors/[service]_login.py`

2. **"No data captured"**
   - API endpoints may have changed
   - UI selectors may have changed
   - Try manual mode to debug: `--manual` flag

3. **"Directory mismatch" (TooLost specific)**
   - Use the fixed cleaner: `python src/toolost/cleaners/toolost_raw2staging_fixed.py`
   - Or rename the original and use the fixed version

### Cookie Management

Cookies are stored in: `data_lake/src/common/cookies/[service]_cookies.json`

To manually clear cookies:
```bash
rm src/common/cookies/toolost_cookies.json
```

To backup cookies:
```bash
cp -r src/common/cookies src/common/cookies_backup_$(date +%Y%m%d)
```

## Best Practices

1. **Regular Monitoring**
   - Run health monitor daily
   - Check for warnings weekly
   - Address critical issues immediately

2. **Cookie Refresh Schedule**
   - TooLost: Every 5-6 days
   - TikTok: Every 5-6 days  
   - DistroKid: Every 10-12 days
   - Spotify: Every 25-28 days

3. **Error Handling**
   - Always check monitor output before running full pipeline
   - Use `--check-only` flag to verify status
   - Keep manual authentication scripts updated

4. **Data Validation**
   - Verify data in staging after extraction
   - Check for gaps in time series data
   - Monitor for unexpected format changes

## Integration with Data Warehouse

After successful extraction and cleaning:
```bash
cd ../data-warehouse
python scripts/run_all_etl.py
```

The warehouse ETL will automatically pick up the latest curated files.

## Future Enhancements

1. **Email Notifications**: Send alerts when manual authentication is needed
2. **Web Dashboard**: Visual status of all services and cookie expiration
3. **API Integration**: Some services may offer API keys as alternative to cookies
4. **Automatic Retry**: Retry failed extractions with exponential backoff

## Summary

The authentication workflow provides a balance between automation and security:
- Automated extraction when possible
- Clear prompts for manual intervention when needed
- Comprehensive monitoring and reporting
- Flexible enough for both interactive and scheduled use

For questions or issues, check the logs in `data_lake/logs/` or run the health monitor for detailed diagnostics.