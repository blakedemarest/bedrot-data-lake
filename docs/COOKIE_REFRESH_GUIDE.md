# Cookie Refresh System Guide

## Overview

The Cookie Refresh System is an automated solution for managing authentication cookies across all BEDROT data sources. It monitors cookie expiration dates and provides both automated and manual refresh capabilities.

## Quick Start

### 1. Check Cookie Status
```bash
# From data_lake directory
cronjob\refresh_cookies.bat

# Or directly with Python
python -m common.cookie_refresh --check
```

### 2. Refresh Expired Cookies
```bash
# Interactive mode (recommended)
python -m common.cookie_refresh --refresh

# Automated mode (no prompts)
python -m common.cookie_refresh --refresh --no-interactive

# Refresh specific service
python -m common.cookie_refresh --refresh --service spotify
```

### 3. Backup Cookies
```bash
# Backup all services
python -m common.cookie_refresh --backup

# Backup specific service
python -m common.cookie_refresh --backup --service tiktok
```

## Cookie Status Indicators

- ✅ **VALID**: Cookies are fresh and working
- ⚡ **WARNING**: Cookies expire in 4-7 days
- ⚠️ **CRITICAL**: Cookies expire in less than 3 days
- ❌ **EXPIRED**: Cookies have expired and need immediate refresh
- ❓ **UNKNOWN**: Cannot determine expiration status

## Service-Specific Notes

### TikTok
- **Multiple Accounts**: Supports both `pig1987` and `zone.a0` accounts
- **2FA Required**: May need manual QR code scanning during refresh
- **Storage**: Separate cookie files for each account

### TooLost
- **JWT Tokens**: Expire every 7 days (most frequent refresh needed)
- **Manual Process**: Requires browser interaction
- **Priority**: High - check weekly

### Spotify
- **OAuth Tokens**: Generally stable for 30+ days
- **Refresh Process**: Automated through Playwright
- **Fallback**: Can use manual browser if automation fails

### DistroKid
- **Long-lived**: Cookies typically valid for 90 days
- **Simple Auth**: No 2FA required
- **Stable**: Rarely needs refresh

### Linktree
- **Standard Auth**: 30-day expiration
- **Quick Refresh**: Simple login process
- **No 2FA**: Straightforward automation

## Configuration

Edit `config/cookie_refresh_config.yaml` to customize:

```yaml
general:
  check_interval_hours: 24      # How often to check
  expiration_warning_days: 7    # When to warn
  expiration_critical_days: 3   # When to mark critical
  browser_headless: false       # Show browser during refresh

services:
  toolost:
    expiration_days: 7          # Service-specific expiration
    priority: 4                 # Refresh order
    enabled: true              # Enable/disable service
```

## Troubleshooting

### "No cookies found"
- Run the service's extractor first to generate initial cookies
- Check if cookie file exists in `src/{service}/cookies/`

### "Failed to refresh"
1. Check internet connection
2. Verify credentials are correct
3. Try manual refresh: `python src/{service}/extractors/{service}_auth.py`
4. Check for service-specific login changes

### "expirationDate" field error
- The system now handles both 'expires' and 'expirationDate' fields
- Old cookie files are automatically compatible

## Integration with Pipeline

The cookie refresh system is integrated into the main pipeline:

```bash
# Run full pipeline with cookie checks
cronjob\run_bedrot_pipeline.bat
```

The pipeline will:
1. Check authentication status
2. Check cookie expiration
3. Prompt for refresh if needed
4. Continue with data extraction

## Manual Cookie Management

### View Raw Cookie Files
```bash
# Example paths
src\spotify\cookies\spotify_cookies.json
src\tiktok\cookies\pig1987_cookies.json
src\toolost\cookies\toolost_cookies.json
```

### Restore from Backup
```bash
# Backups are stored with timestamps
copy backups\cookies\spotify\cookies_20250108_143022.json src\spotify\cookies\spotify_cookies.json
```

## Best Practices

1. **Daily Checks**: Run `refresh_cookies.bat` daily to monitor status
2. **Weekly Review**: Check TooLost specifically every week
3. **Pre-emptive Refresh**: Refresh cookies showing WARNING status
4. **Backup Before Refresh**: System auto-backs up, but manual backup is good practice
5. **Monitor Logs**: Check `logs/cookie_refresh.log` for issues

## Advanced Usage

### Python API
```python
from common.cookie_refresh.storage import CookieStorageManager
from common.cookie_refresh.config import CookieRefreshConfig

# Check status programmatically
storage = CookieStorageManager('src')
status = storage.get_expiration_info('spotify')
print(f"Spotify expires in {status.days_until_expiration} days")

# Get all expired services
all_status = storage.get_all_services_status()
expired = [s.service for s in all_status if s.is_expired]
```

### Environment Variables
```bash
# Override configuration
set COOKIE_REFRESH_INTERVAL_HOURS=12
set COOKIE_REFRESH_HEADLESS=true
set COOKIE_REFRESH_SPOTIFY_ENABLED=false
```

### Notifications
Configure email notifications in the config file:
```yaml
notifications:
  email:
    enabled: true
    smtp_host: smtp.gmail.com
    smtp_port: 587
```

## Maintenance Schedule

| Task | Frequency | Command |
|------|-----------|---------|
| Status Check | Daily | `cronjob\refresh_cookies.bat` |
| TooLost Refresh | Weekly | `python -m common.cookie_refresh --refresh --service toolost` |
| Full Refresh | Monthly | `python -m common.cookie_refresh --refresh --no-interactive` |
| Backup Cleanup | Monthly | Check `backups/cookies/` for old files |

## Security Notes

- Cookies contain sensitive authentication tokens
- Never commit cookie files to version control
- Backups are kept for 30 days by default
- Use encrypted storage for production environments

## Support

For issues:
1. Check this guide
2. Review `logs/cookie_refresh.log`
3. Run `python scripts/deploy_cookie_refresh.py` to validate setup
4. Check service-specific documentation in `src/{service}/README.md`