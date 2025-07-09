# Cookie Refresh System Deployment Guide

This guide provides step-by-step instructions for deploying the BEDROT cookie refresh automation system in a production environment.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Installation Steps](#installation-steps)
- [Configuration](#configuration)
- [Windows Task Scheduler Setup](#windows-task-scheduler-setup)
- [Validation](#validation)
- [Monitoring Setup](#monitoring-setup)
- [Backup Procedures](#backup-procedures)
- [Rollback Plan](#rollback-plan)
- [Maintenance](#maintenance)

## Prerequisites

### System Requirements
- **OS**: Windows 10/11 or Windows Server 2016+
- **Python**: 3.8 or higher
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 10GB free space for logs and backups
- **Network**: Stable internet connection
- **Permissions**: Administrator access for Task Scheduler

### Software Dependencies
```bash
# Required Python packages (installed automatically)
- playwright>=1.40.0
- requests>=2.31.0
- python-dotenv>=1.0.0
- cryptography>=41.0.0
- apscheduler>=3.10.0
- flask>=3.0.0
- pandas>=2.0.0
- pydantic>=2.0.0
```

### Service Credentials
Ensure you have credentials for all services:
- Spotify: Client ID and Secret
- TikTok: Username and Password
- DistroKid: Username and Password  
- TooLost: Username and Password
- Linktree: Username and Password
- Meta Ads: Access Token (if applicable)

## Pre-Deployment Checklist

Run the pre-deployment check script:

```bash
cd data_lake
python scripts/deployment/check_deployment_readiness.py
```

This script verifies:
- [ ] Python version compatibility
- [ ] All required packages installed
- [ ] Environment variables set
- [ ] Write permissions in required directories
- [ ] Network connectivity to service endpoints
- [ ] Existing cookie backup created
- [ ] Current system state documented

Manual checks:
- [ ] Review and update service credentials
- [ ] Confirm maintenance window scheduled
- [ ] Notify team of deployment
- [ ] Backup current production cookies
- [ ] Document current cookie ages

## Installation Steps

### 1. Clone Repository and Navigate to Directory

```bash
# Clone repository (if not already done)
git clone https://github.com/your-org/bedrot-data-ecosystem.git

# Navigate to data lake directory
cd "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake"
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip
```

### 3. Install Dependencies

```bash
# Install production requirements
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
playwright install-deps
```

### 4. Set Up Environment Variables

```bash
# Copy example environment file
copy .env.example .env

# Edit .env file with production values
notepad .env
```

Required environment variables:
```env
# Spotify OAuth
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret

# TikTok Credentials
TIKTOK_USERNAME=your_username
TIKTOK_PASSWORD=your_password

# DistroKid Credentials
DISTROKID_USERNAME=your_username
DISTROKID_PASSWORD=your_password

# TooLost Credentials
TOOLOST_USERNAME=your_username
TOOLOST_PASSWORD=your_password

# Linktree Credentials
LINKTREE_USERNAME=your_username
LINKTREE_PASSWORD=your_password

# System Configuration
PROJECT_ROOT=C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake
COOKIE_REFRESH_LOG_LEVEL=INFO
COOKIE_REFRESH_CONFIG_FILE=config/cookie_refresh_config.json

# Notification Settings (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFICATION_EMAIL=admin@company.com

# Slack Webhook (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 5. Initialize Configuration

```bash
# Create configuration directory
mkdir config

# Initialize default configuration
python scripts/deployment/init_config.py --production

# Review and customize configuration
notepad config\cookie_refresh_config.json
```

### 6. Migrate Existing Cookies

```bash
# Backup existing cookies
python scripts/deployment/backup_existing_cookies.py

# Migrate cookies to new structure
python scripts/deployment/migrate_cookies.py --verify

# If verification passes, run actual migration
python scripts/deployment/migrate_cookies.py --execute
```

### 7. Set Up Directory Structure

```bash
# Create required directories
python scripts/deployment/setup_directories.py

# Verify directory permissions
python scripts/deployment/verify_permissions.py
```

## Configuration

### Main Configuration File

Edit `config/cookie_refresh_config.json`:

```json
{
  "global": {
    "check_interval_minutes": 60,
    "max_retry_attempts": 3,
    "retry_delay_seconds": 300,
    "notification_channels": ["email", "slack"],
    "concurrent_refreshes": 2,
    "business_hours_only": false,
    "quiet_hours": {
      "enabled": true,
      "start": "22:00",
      "end": "06:00"
    }
  },
  "services": {
    "spotify": {
      "enabled": true,
      "refresh_interval_hours": 168,
      "max_age_days": 10,
      "strategy": "oauth",
      "priority": 1,
      "notification_channels": ["email"]
    },
    "tiktok": {
      "enabled": true,
      "refresh_interval_hours": 168,
      "max_age_days": 10,
      "strategy": "playwright",
      "priority": 2,
      "requires_2fa": true,
      "accounts": ["pig1987", "zone.a0"]
    },
    "distrokid": {
      "enabled": true,
      "refresh_interval_hours": 240,
      "max_age_days": 12,
      "strategy": "jwt",
      "priority": 3,
      "jwt_expiry_days": 12
    },
    "toolost": {
      "enabled": true,
      "refresh_interval_hours": 144,
      "max_age_days": 7,
      "strategy": "jwt",
      "priority": 4,
      "jwt_expiry_days": 7
    },
    "linktree": {
      "enabled": true,
      "refresh_interval_hours": 336,
      "max_age_days": 14,
      "strategy": "playwright",
      "priority": 5
    }
  },
  "notifications": {
    "email": {
      "enabled": true,
      "smtp_server": "${SMTP_SERVER}",
      "smtp_port": "${SMTP_PORT}",
      "username": "${SMTP_USERNAME}",
      "password": "${SMTP_PASSWORD}",
      "from_address": "${SMTP_USERNAME}",
      "to_addresses": ["${NOTIFICATION_EMAIL}"]
    },
    "slack": {
      "enabled": true,
      "webhook_url": "${SLACK_WEBHOOK_URL}"
    }
  },
  "monitoring": {
    "enabled": true,
    "port": 8080,
    "metrics_retention_days": 30
  }
}
```

### Security Configuration

```bash
# Encrypt sensitive configuration
python scripts/deployment/encrypt_config.py --key-file config/master.key

# Set file permissions (Windows)
icacls config\*.json /inheritance:r /grant:r "%USERNAME%":F /grant:r "SYSTEM":F

# Create secure credential store
python scripts/deployment/setup_credential_store.py
```

## Windows Task Scheduler Setup

### 1. Create Scheduled Task

Run PowerShell as Administrator:

```powershell
# Create main refresh task
$action = New-ScheduledTaskAction -Execute "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake\.venv\Scripts\python.exe" -Argument "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake\src\common\cookie_refresh\scheduler.py" -WorkingDirectory "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake"

$trigger = New-ScheduledTaskTrigger -Daily -At 3:00AM

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5)

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType S4U -RunLevel Highest

Register-ScheduledTask -TaskName "BEDROT Cookie Refresh" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Automated cookie refresh for BEDROT data ecosystem"
```

### 2. Create Health Check Task

```powershell
# Create health check task (runs every hour)
$healthAction = New-ScheduledTaskAction -Execute "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake\.venv\Scripts\python.exe" -Argument "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake\src\common\cookie_refresh\health_check.py" -WorkingDirectory "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake"

$healthTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 365)

Register-ScheduledTask -TaskName "BEDROT Cookie Refresh Health Check" -Action $healthAction -Trigger $healthTrigger -Settings $settings -Principal $principal -Description "Health monitoring for BEDROT cookie refresh system"
```

### 3. Create Manual Trigger Script

Create `scripts/deployment/trigger_manual_refresh.bat`:

```batch
@echo off
echo Starting manual cookie refresh...
cd /d "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake"

call .venv\Scripts\activate
python src\common\cookie_refresh\manual_refresh.py %*

echo.
echo Manual refresh completed. Check logs for details.
pause
```

## Validation

### 1. Run Validation Script

```bash
# Comprehensive validation
python scripts/deployment/validate_deployment.py --full

# This checks:
# - Configuration validity
# - Service connectivity
# - Credential verification
# - Directory permissions
# - Task Scheduler setup
# - Notification delivery
```

### 2. Test Individual Services

```bash
# Test each service without actual refresh
python src/common/cookie_refresh/test_service.py --service spotify --dry-run
python src/common/cookie_refresh/test_service.py --service tiktok --dry-run
python src/common/cookie_refresh/test_service.py --service distrokid --dry-run
python src/common/cookie_refresh/test_service.py --service toolost --dry-run
python src/common/cookie_refresh/test_service.py --service linktree --dry-run
```

### 3. Run Test Cycle

```bash
# Run a complete test cycle
python src/common/cookie_refresh/run_test_cycle.py --verbose

# Monitor output
python src/common/cookie_refresh/monitor_logs.py --follow
```

### 4. Verify Notifications

```bash
# Send test notifications
python src/common/cookie_refresh/test_notifications.py --all-channels
```

## Monitoring Setup

### 1. Start Monitoring Dashboard

```bash
# Start dashboard service
python src/common/cookie_refresh/start_dashboard.py --port 8080

# Access dashboard at http://localhost:8080
```

### 2. Configure Alerts

```bash
# Set up alert rules
python scripts/deployment/configure_alerts.py

# Alert conditions:
# - Service failure (3 consecutive failures)
# - Cookie age exceeding threshold
# - System errors
# - Performance degradation
```

### 3. Enable Metrics Collection

```bash
# Initialize metrics database
python scripts/deployment/init_metrics_db.py

# Start metrics collector
python src/common/cookie_refresh/metrics_collector.py --daemon
```

## Backup Procedures

### Automated Backups

```bash
# Set up automated backups
python scripts/deployment/setup_backups.py --schedule daily --retention 30

# Backup locations:
# - Cookies: backups/cookies/
# - Configuration: backups/config/
# - Logs: backups/logs/
# - Metrics: backups/metrics/
```

### Manual Backup

```bash
# Create manual backup
python scripts/deployment/create_backup.py --full --tag pre-update

# Verify backup
python scripts/deployment/verify_backup.py --latest
```

## Rollback Plan

### Quick Rollback (< 5 minutes)

```bash
# 1. Stop scheduled tasks
python scripts/deployment/stop_all_tasks.py

# 2. Restore from backup
python scripts/deployment/quick_rollback.py --backup latest

# 3. Restart services
python scripts/deployment/start_all_tasks.py

# 4. Verify system health
python scripts/deployment/verify_health.py
```

### Full Rollback (10-15 minutes)

```bash
# 1. Document current state
python scripts/deployment/document_state.py --output rollback_state.json

# 2. Stop all services
python scripts/deployment/emergency_stop.py

# 3. Restore previous version
python scripts/deployment/restore_version.py --version previous

# 4. Restore data from backup
python scripts/deployment/restore_data.py --backup pre-deployment

# 5. Validate restoration
python scripts/deployment/validate_rollback.py

# 6. Resume operations
python scripts/deployment/resume_operations.py
```

## Maintenance

### Daily Maintenance

```batch
REM daily_maintenance.bat
@echo off
cd /d "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake"

echo Running daily maintenance...
call .venv\Scripts\activate

REM Check system health
python src\common\cookie_refresh\daily_health_check.py

REM Clean old logs
python src\common\cookie_refresh\cleanup_logs.py --older-than 7

REM Optimize database
python src\common\cookie_refresh\optimize_db.py

echo Daily maintenance completed.
```

### Weekly Maintenance

```batch
REM weekly_maintenance.bat
@echo off
cd /d "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake"

echo Running weekly maintenance...
call .venv\Scripts\activate

REM Full system check
python src\common\cookie_refresh\weekly_system_check.py

REM Update Playwright browsers
playwright install chromium --with-deps

REM Clean old backups
python src\common\cookie_refresh\cleanup_backups.py --older-than 30

REM Generate weekly report
python src\common\cookie_refresh\generate_weekly_report.py

echo Weekly maintenance completed.
```

### Monthly Maintenance

```bash
# Review and update credentials
python src/common/cookie_refresh/review_credentials.py

# Performance analysis
python src/common/cookie_refresh/analyze_performance.py --last-month

# Update strategies if needed
python src/common/cookie_refresh/update_strategies.py --check-updates

# Security audit
python src/common/cookie_refresh/security_audit.py
```

## Performance Tuning

### Optimize for Production

```bash
# Run performance analysis
python scripts/deployment/analyze_performance.py

# Apply optimizations
python scripts/deployment/apply_optimizations.py --profile production

# Optimizations include:
# - Browser context reuse
# - Connection pooling
# - Caching strategies
# - Parallel processing limits
```

### Resource Limits

```powershell
# Set process priority (PowerShell)
$process = Get-Process python | Where-Object {$_.CommandLine -like "*cookie_refresh*"}
$process.PriorityClass = "BelowNormal"

# Set CPU affinity (limit to specific cores)
$process.ProcessorAffinity = 0x0F  # First 4 cores
```

## Security Hardening

### 1. Credential Protection

```bash
# Encrypt stored credentials
python scripts/deployment/encrypt_credentials.py

# Set up credential rotation reminders
python scripts/deployment/setup_rotation_reminders.py --days 90
```

### 2. Access Control

```powershell
# Restrict access to sensitive directories
$acl = Get-Acl "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake\config"
$acl.SetAccessRuleProtection($true, $false)
$accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule("$env:USERNAME", "FullControl", "Allow")
$acl.SetAccessRule($accessRule)
Set-Acl -Path "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake\config" -AclObject $acl
```

### 3. Audit Logging

```bash
# Enable comprehensive audit logging
python scripts/deployment/enable_audit_logging.py

# Configure log shipping (optional)
python scripts/deployment/setup_log_shipping.py --destination syslog://logserver:514
```

## Troubleshooting Deployment

### Common Deployment Issues

1. **Task Scheduler Not Running**
   ```powershell
   # Check task status
   Get-ScheduledTask -TaskName "BEDROT Cookie Refresh" | Select-Object State, LastRunTime, LastTaskResult
   
   # View task history
   Get-WinEvent -LogName Microsoft-Windows-TaskScheduler/Operational | Where-Object {$_.Message -like "*BEDROT*"} | Select-Object -First 10
   ```

2. **Permission Errors**
   ```bash
   # Fix permissions
   python scripts/deployment/fix_permissions.py --recursive
   ```

3. **Missing Dependencies**
   ```bash
   # Reinstall dependencies
   pip install -r requirements.txt --force-reinstall
   ```

## Post-Deployment Checklist

- [ ] All services showing "healthy" status
- [ ] Scheduled tasks running successfully  
- [ ] Notifications being received
- [ ] Monitoring dashboard accessible
- [ ] Backups configured and tested
- [ ] Documentation updated
- [ ] Team notified of completion
- [ ] Handover documentation provided
- [ ] Support contacts updated

## Support Information

### Log Locations
- Main logs: `logs/cookie_refresh/`
- Service logs: `logs/cookie_refresh/services/`
- Deployment logs: `logs/deployment/`
- Error logs: `logs/cookie_refresh/errors/`

### Configuration Files
- Main config: `config/cookie_refresh_config.json`
- Service configs: `config/services/`
- Credentials: `config/credentials/` (encrypted)

### Monitoring URLs
- Dashboard: http://localhost:8080
- Health check: http://localhost:8080/health
- Metrics: http://localhost:8080/metrics

### Emergency Contacts
- Create `config/emergency_contacts.json` with your team's contact information

Remember: Always test in a non-production environment first. Keep backups of all configuration and cookies before making changes.