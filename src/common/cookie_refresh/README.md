# Cookie Refresh Automation System

## Overview

The Cookie Refresh Automation System is designed to prevent pipeline failures due to expired authentication cookies. It provides automated monitoring, alerting, and refresh capabilities for all services in the BEDROT data ecosystem.

## Features

- **Automated Expiration Monitoring**: Tracks cookie expiration dates across all services
- **Multi-Account Support**: Handles services with multiple accounts (e.g., TikTok)
- **Flexible Notification System**: Console, file, and email notifications
- **Browser Automation**: Uses Playwright for automated refresh flows
- **Manual Intervention Support**: Handles 2FA and complex authentication flows
- **Backup & Recovery**: Automatic backups before refresh attempts
- **Storage State Support**: Full session persistence using Playwright's storage state
- **JWT Token Support**: Special handling for services using JWT tokens (TooLost)
- **Screenshot Capture**: Automatic screenshots on failures for debugging

## Architecture

```
cookie_refresh/
├── __init__.py          # Package initialization
├── config.py            # Configuration management
├── storage.py           # Cookie and storage state management
├── notifier.py          # Notification system
├── refresher.py         # Main orchestrator
├── test_strategies.py   # Strategy test suite
├── usage_example.py     # Usage examples
└── strategies/          # Service-specific strategies
    ├── __init__.py
    ├── base.py          # Abstract base strategy
    ├── distrokid.py     # DistroKid (automated with credentials)
    ├── spotify.py       # Spotify (manual login)
    ├── tiktok.py        # TikTok (multi-account, QR/manual)
    ├── toolost.py       # TooLost (CRITICAL - 7 day JWT)
    └── linktree.py      # Linktree (standard cookies)
```

## Implemented Service Strategies

### 1. DistroKid (`distrokid.py`)
- **Authentication**: Automated login with stored credentials
- **Required ENV**: `DK_EMAIL`, `DK_PASSWORD`
- **2FA Support**: Manual intervention when required
- **Success Indicators**: Dashboard URLs (`/dashboard`, `/mymusic`, `/stats`)
- **Expiration**: 90 days

### 2. Spotify (`spotify.py`)
- **Authentication**: Manual login only (no stored credentials)
- **Login Methods**: Email/Password, Facebook, Apple, Google
- **Success Indicators**: User widget elements, artists.spotify.com access
- **Validation**: Checks both Spotify for Artists and web player
- **Expiration**: 30 days

### 3. TikTok (`tiktok.py`)
- **Multi-Account**: Supports `pig1987` and `zone.a0` accounts
- **Login Methods**: QR code, email, phone, social
- **Required Cookies**: `sessionid`, `sid_guard`, `uid_tt`
- **Legacy Support**: Saves cookies in both new and legacy formats
- **Expiration**: 30 days per account

### 4. TooLost (`toolost.py`) - CRITICAL PRIORITY
- **JWT Expiration**: Every 7 days (hardcoded override)
- **Authentication**: Manual login required
- **Token Storage**: Extracts JWT from localStorage
- **API Validation**: Tests Spotify and Apple Music endpoints
- **Critical Alerts**: Special handling for 7-day expiration

### 5. Linktree (`linktree.py`)
- **Authentication**: Standard cookie-based
- **Login URL**: https://linktr.ee/login
- **Success Indicators**: Admin dashboard access
- **Validation**: Checks both dashboard and analytics pages
- **Expiration**: 30 days

## Usage

### Command Line Interface

```bash
# Check cookie status for all services
python -m common.cookie_refresh.refresher --check-only

# Refresh all services that need it
python -m common.cookie_refresh.refresher

# Force refresh all services
python -m common.cookie_refresh.refresher --force

# Refresh specific service
python -m common.cookie_refresh.refresher --service spotify

# Refresh specific TikTok account
python -m common.cookie_refresh.refresher --service tiktok --account pig1987

# Using batch file (Windows)
cronjob\run_cookie_refresh.bat --check-only
```

### Python API

```python
from common.cookie_refresh.refresher import CookieRefresher

# Create refresher instance
refresher = CookieRefresher()

# Check all services
status_list = refresher.check_all_services()
for status in status_list:
    print(f"{status.service}: {status.status} (expires in {status.days_until_expiration} days)")

# Refresh specific service
result = refresher.refresh_service('spotify')
if result.success:
    print("Spotify cookies refreshed successfully")

# Refresh all expired services
results = refresher.refresh_all_needed()
```

### Direct Strategy Usage

```python
from common.cookie_refresh.strategies import TooLostRefreshStrategy
from common.cookie_refresh.storage import CookieStorageManager
from common.cookie_refresh.notifier import CookieRefreshNotifier

# Create components
storage = CookieStorageManager(base_path='./src')
notifier = CookieRefreshNotifier({'console': {'enabled': True}})

# Create and use strategy
strategy = TooLostRefreshStrategy(storage, notifier)

# Check if refresh needed
needs_refresh, reason = strategy.needs_refresh()
if needs_refresh:
    print(f"TooLost needs refresh: {reason}")
    result = strategy.refresh_cookies()
    print(f"Result: {result.message}")
```

## Configuration

### Default Configuration (config/cookie_refresh_config.yaml)

```yaml
general:
  check_interval_hours: 24
  expiration_warning_days: 7
  expiration_critical_days: 3
  backup_retention_days: 30
  max_refresh_attempts: 3
  browser_headless: false  # Show browser for manual login
  browser_timeout_seconds: 300
  screenshot_on_failure: true

services:
  spotify:
    enabled: true
    refresh_strategy: spotify
    expiration_days: 30
    priority: 1
    auth_url: https://accounts.spotify.com/login
    requires_2fa: false

  distrokid:
    enabled: true
    refresh_strategy: distrokid
    expiration_days: 90
    priority: 2
    auth_url: https://distrokid.com/signin
    requires_2fa: false

  tiktok:
    enabled: true
    refresh_strategy: tiktok
    expiration_days: 30
    priority: 3
    auth_url: https://www.tiktok.com/login
    requires_2fa: true
    accounts: ['pig1987', 'zone.a0']

  toolost:
    enabled: true
    refresh_strategy: toolost
    expiration_days: 7  # JWT expires weekly!
    priority: 4
    auth_url: https://app.toolost.com/login
    requires_2fa: false

  linktree:
    enabled: true
    refresh_strategy: linktree
    expiration_days: 30
    priority: 5
    auth_url: https://linktr.ee/login
    requires_2fa: false

notifications:
  enabled: true
  console:
    enabled: true
    log_level: INFO
  file:
    enabled: true
    log_path: logs/cookie_refresh.log
  email:
    enabled: false  # Configure SMTP settings to enable
```

### Environment Variables

```bash
# Required for DistroKid
DK_EMAIL=your-email@example.com
DK_PASSWORD=your-password

# Optional overrides
COOKIE_REFRESH_INTERVAL_HOURS=12
COOKIE_REFRESH_HEADLESS=false
COOKIE_REFRESH_SPOTIFY_ENABLED=true

# Email notifications (if enabled)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=notifications@example.com
SMTP_PASSWORD=app-specific-password
NOTIFICATION_FROM_EMAIL=bedrot-cookies@example.com
NOTIFICATION_TO_EMAILS=admin@example.com,backup@example.com
```

## Service-Specific Notes

### Critical Services
- **TooLost**: JWT expires every 7 days - requires weekly refresh. Set calendar reminders!
- **TikTok Zone A0**: Critical for analytics data

### Authentication Methods
- **Automated**: DistroKid (with credentials)
- **Manual Only**: Spotify, TikTok, TooLost, Linktree
- **2FA Support**: DistroKid, TikTok (when required)

### Storage Locations
- **Cookies**: `src/<service>/cookies/` (legacy) and `src/.cookies/`
- **Storage State**: `src/.storage_state/`
- **Backups**: `backups/cookies/`
- **Screenshots**: `logs/screenshots/`

## Testing

Run the comprehensive test suite:

```bash
# Test all strategies
python src/common/cookie_refresh/test_strategies.py

# Run usage examples
python src/common/cookie_refresh/usage_example.py

# Test specific example
python src/common/cookie_refresh/usage_example.py --example 2
```

## Development Guide

### Adding a New Service

1. **Create Strategy File**: `strategies/myservice.py`

```python
from .base import BaseRefreshStrategy, RefreshResult

class MyServiceRefreshStrategy(BaseRefreshStrategy):
    def __init__(self, storage_manager, notifier=None, config=None):
        super().__init__('myservice', storage_manager, notifier, config)
        self.login_url = 'https://myservice.com/login'
        self.dashboard_url = 'https://myservice.com/dashboard'
        
    def refresh_cookies(self, account=None):
        """Implement service-specific refresh logic."""
        with self.create_browser_context() as (browser, context, page):
            # Navigate to login
            page.goto(self.login_url)
            
            # Handle login (automated or manual)
            if not self.wait_for_manual_login(page, '*://myservice.com/dashboard*'):
                return RefreshResult(success=False, message="Login failed")
            
            # Validate and save
            if self.validate_cookies(context):
                self.save_auth_state(context)
                return RefreshResult(
                    success=True,
                    message="Cookies refreshed successfully",
                    cookies_saved=True,
                    storage_state_saved=True
                )
                
    def validate_cookies(self, context):
        """Verify cookies are working."""
        page = context.new_page()
        page.goto(self.dashboard_url)
        # Check for logged-in indicators
        return 'dashboard' in page.url
```

2. **Update Configuration**: Add to `cookie_refresh_config.yaml`

3. **Update __init__.py**: Export the new strategy

4. **Test**: Add tests to `test_strategies.py`

### Base Strategy Methods

All strategies inherit these methods:

- `refresh_cookies(account=None)` - Main refresh logic (must implement)
- `validate_cookies(context)` - Validate cookies work (must implement)
- `needs_refresh(account, warning_days)` - Check if refresh needed
- `check_expiration(account)` - Get expiration info
- `wait_for_manual_login(page, success_pattern)` - Wait for user login
- `wait_for_2fa(page, timeout)` - Handle 2FA
- `save_auth_state(context, account)` - Save cookies and storage state
- `load_existing_auth(account)` - Load saved auth
- `backup_current_auth(account)` - Backup before refresh

## Troubleshooting

### Common Issues

1. **"No module named 'strategies.spotify'"**
   - Ensure PROJECT_ROOT is set correctly
   - Run from data_lake directory

2. **"Login timeout"**
   - Increase browser_timeout_seconds
   - Check for UI changes on login page
   - Verify network connectivity

3. **"JWT not found" (TooLost)**
   - Ensure you're on the portal page
   - Check localStorage keys: token, jwt, authToken
   - Try refreshing the page after login

4. **"Missing required cookies" (TikTok)**
   - Clear existing cookies and re-login
   - Check account-specific paths
   - Verify all required cookies: sessionid, sid_guard, uid_tt

5. **"Browser not installed"**
   - Run: `playwright install chromium`

### Debug Mode

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('common.cookie_refresh').setLevel(logging.DEBUG)
```

### Manual Cookie Export

For services without strategies yet:

1. Install browser extension: Cookie-Editor, EditThisCookie
2. Login to service manually
3. Export cookies as JSON
4. Save to: `src/<service>/cookies/<service>_cookies.json`

## Maintenance

### Regular Tasks

- **Daily**: Check cookie status (`--check-only`)
- **Weekly**: Refresh TooLost (7-day JWT expiration)
- **Monthly**: Review all cookie expirations
- **As Needed**: Refresh on pipeline failures

### Monitoring

Check the status dashboard:

```bash
python -m common.cookie_refresh.refresher --check-only
```

Output shows:
- Service name and account
- Status (OK, WARNING, CRITICAL, EXPIRED)
- Last refresh date
- Days until expiration

## Future Enhancements

- [ ] Automated scheduling with cron/Task Scheduler
- [ ] Web dashboard for status monitoring
- [ ] Slack/Discord notifications
- [ ] MetaAds strategy implementation
- [ ] YouTube strategy implementation
- [ ] Automated 2FA handling (where possible)
- [ ] Cookie health metrics and analytics