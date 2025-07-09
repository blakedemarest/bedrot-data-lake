# CLAUDE.md - Data Lake Automation & Scheduling

This directory contains the consolidated automation scripts that orchestrate the entire Data Lake ETL pipeline execution.

## Overview

The cronjob system provides automated, scheduled execution of all data lake processes including cookie management, health monitoring, data extraction, cleaning, and warehouse ETL. It supports both full pipeline runs (with data extraction) and cleaner-only runs for reprocessing existing data.

## Directory Structure

```
6_automated_cronjob/
├── run_datalake_cron.bat              # Master consolidated pipeline (Windows)
├── run_datalake_cron_no_extractors.bat # Cleaners only variant (Windows)
├── generate_no_extractors_cron.py     # Generate cleaner-only script
├── data_lake_cron_flow.dot            # Pipeline flow diagram
├── CLAUDE.md                          # This documentation
└── README.md                          # Basic documentation
```

## Key Files

### run_datalake_cron.bat
The master consolidated pipeline that handles EVERYTHING:
- **Cookie Management**: Checks status and auto-refreshes expired cookies
- **Health Monitoring**: Pipeline health check with auto-remediation
- **Individual Extractors**: Calls each service's extractor directly (no integrated_extractor.py)
- **Data Cleaning**: Auto-discovers and runs all cleaners in proper order
- **Data Warehouse ETL**: Seamlessly integrates with data warehouse
- **Comprehensive Reporting**: Generates logs, dashboards, and summaries

Features:
- 6-step execution process with clear progress indicators
- Comprehensive error handling and logging
- Failure tracking and summary reporting
- Automatic virtual environment management
- Old log archival (30-day retention)

### run_datalake_cron_no_extractors.bat
A variant that:
- Skips data extraction phase (Step 3)
- Only runs cleaner scripts and warehouse ETL
- Useful for reprocessing existing data
- Faster execution for testing
- Auto-generated from master script

### generate_no_extractors_cron.py
Utility script that:
- Reads the main cron script
- Removes Step 3 (Data Extraction) entirely
- Adjusts failure counting variables
- Generates the no-extractors variant
- Maintains consistency between versions

## Running the Pipeline

### Full Pipeline Execution
```bash
# From Windows Command Prompt or PowerShell
cd "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake"
.\6_automated_cronjob\run_datalake_cron.bat
```

### Cleaners Only
```bash
# Reprocess existing data without extraction
.\6_automated_cronjob\run_datalake_cron_no_extractors.bat
```

### Linux/Mac Execution
```bash
# Convert batch to shell script
python 6_automated_cronjob/convert_to_shell.py

# Run generated script
./6_automated_cronjob/run_datalake_cron.sh
```

## Execution Order

The pipeline follows this sequence:

1. **Environment Setup**
   - Set PROJECT_ROOT
   - Activate virtual environment
   - Verify Python path

2. **Extractors** (Full pipeline only)
   ```
   distrokid → spotify → tiktok → metaads → linktree → toolost
   ```

3. **Cleaners** (All pipelines)
   ```
   For each service:
   landing2raw → raw2staging → staging2curated
   ```

4. **Post-Processing**
   - Run ETL to data warehouse
   - Archive old files
   - Generate reports

## Scheduling

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily, weekly, etc.)
4. Action: Start a program
5. Program: `C:\path\to\run_datalake_cron.bat`
6. Start in: `C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake`

### Cron (Linux/Mac)
```bash
# Edit crontab
crontab -e

# Run daily at 2 AM
0 2 * * * cd /path/to/data_lake && ./6_automated_cronjob/run_datalake_cron.sh >> logs/cron.log 2>&1

# Run cleaners every 6 hours
0 */6 * * * cd /path/to/data_lake && ./6_automated_cronjob/run_datalake_cron_no_extractors.sh >> logs/cron_cleaners.log 2>&1
```

## Configuration

### Environment Variables
Set in the batch files:
```batch
set PROJECT_ROOT=%CD%
set PYTHONPATH=%PROJECT_ROOT%\src;%PYTHONPATH%
set LOG_LEVEL=INFO
```

### Timeout Settings
Configure max execution time:
```batch
REM Timeout after 2 hours
timeout /t 7200
```

### Service Selection
Comment out services to skip:
```batch
REM python src\spotify\extractors\spotify_audience_extractor.py
```

## Error Handling

### Failure Modes

1. **Extractor Fails**
   - Continues with next extractor
   - Logs error with timestamp
   - Cleaners still run on existing data

2. **Cleaner Fails**
   - Continues with next cleaner
   - Missing dependencies logged
   - Manual intervention may be needed

3. **Environment Issues**
   - Checks for virtual environment
   - Verifies PROJECT_ROOT is set
   - Falls back to global Python if needed

### Log Files
```batch
REM Redirect output to log file
.\6_automated_cronjob\run_datalake_cron.bat > logs\cron_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log 2>&1
```

## Monitoring

### Success Indicators
- All scripts return exit code 0
- No ERROR level logs
- Expected output files created
- Data freshness within threshold

### Health Checks
```python
# Add to end of cron script
python scripts/health_check.py

# Health check script example
def check_pipeline_health():
    checks = {
        'spotify_data_fresh': check_data_age('curated/spotify*.csv', max_days=2),
        'tiktok_data_complete': check_file_exists('curated/tiktok*.csv'),
        'no_error_logs': check_no_errors('logs/'),
    }
    return all(checks.values())
```

## Performance Optimization

### Parallel Execution
For independent services:
```batch
REM Run extractors in parallel
start /B python src\spotify\extractors\spotify_audience_extractor.py
start /B python src\tiktok\extractors\tiktok_analytics_extractor.py
REM Wait for completion
timeout /t 300
```

### Conditional Execution
Skip if data is fresh:
```python
# In extractor
if data_exists_for_today():
    print(f"Data already extracted for {today}")
    sys.exit(0)
```

### Resource Management
```batch
REM Limit CPU usage
start /LOW /B python expensive_script.py

REM Add delays between services
timeout /t 60
```

## Troubleshooting

### Common Issues

**"PROJECT_ROOT not set"**
```batch
REM Ensure you're in the right directory
cd /d "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake"
```

**"Module not found"**
```batch
REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Or install requirements
pip install -r requirements.txt
```

**"Access denied"**
```batch
REM Run as administrator or check file permissions
icacls 6_automated_cronjob\*.bat /grant Users:F
```

### Debug Mode
Add debug flags:
```batch
REM Enable verbose logging
set DEBUG=1
set LOG_LEVEL=DEBUG

REM Dry run mode
set DRY_RUN=1
```

## Maintenance

### Regular Tasks

1. **Log Rotation**
   ```batch
   REM Archive old logs weekly
   move logs\*.log archive\logs\
   ```

2. **Disk Space**
   ```batch
   REM Check available space
   wmic logicaldisk get size,freespace,caption
   ```

3. **Update Scripts**
   ```batch
   REM Regenerate cleaner-only script
   python 6_automated_cronjob\generate_no_extractors_cron.py
   ```

## Extending the Pipeline

### Adding New Service

1. Add extractor command:
   ```batch
   echo Running newservice extractor...
   python src\newservice\extractors\newservice_extractor.py
   if errorlevel 1 echo ERROR: newservice extractor failed
   ```

2. Add cleaner sequence:
   ```batch
   echo Processing newservice data...
   python src\newservice\cleaners\newservice_landing2raw.py
   python src\newservice\cleaners\newservice_raw2staging.py
   python src\newservice\cleaners\newservice_staging2curated.py
   ```

3. Regenerate no-extractors version:
   ```batch
   python cronjob\generate_no_extractors_cron.py
   ```

### Custom Workflows

Create specialized pipelines:
```batch
REM Financial data only
copy cronjob\run_datalake_cron.bat cronjob\run_financial_only.bat
REM Edit to include only distrokid and metaads
```

## Best Practices

1. **Test Changes**: Run manually before scheduling
2. **Monitor Logs**: Check for warnings and errors
3. **Backup Data**: Before major changes
4. **Document Changes**: Update this file
5. **Version Control**: Commit cron script changes

## Integration Points

### Data Warehouse Sync
```batch
REM After curated data is ready
echo Syncing to data warehouse...
cd ..\data-warehouse
python scripts\run_all_etl.py
```

### Notifications
```python
# Add to end of pipeline
if pipeline_success:
    send_slack_notification("✅ Data pipeline completed successfully")
else:
    send_email_alert("❌ Data pipeline errors detected")
```

### Backup and Archive
```batch
REM Weekly archive
if %date:~0,3%==Sun (
    python scripts\archive_old_data.py --days=30
    python scripts\backup_to_cloud.py
)
```