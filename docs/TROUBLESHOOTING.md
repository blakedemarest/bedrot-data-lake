# Cookie Refresh System Troubleshooting Guide

This guide helps diagnose and resolve common issues with the BEDROT cookie refresh automation system.

## Table of Contents
- [Quick Diagnostics](#quick-diagnostics)
- [Common Issues](#common-issues)
- [Service-Specific Issues](#service-specific-issues)
- [2FA Troubleshooting](#2fa-troubleshooting)
- [Performance Issues](#performance-issues)
- [Recovery Procedures](#recovery-procedures)
- [Debug Mode](#debug-mode)
- [Contact Support](#contact-support)

## Quick Diagnostics

Run these commands to quickly diagnose system health:

```bash
# Check overall system status
python src/common/cookie_refresh/check_health.py

# Verify specific service
python src/common/cookie_refresh/check_service.py --service spotify

# Test authentication without refresh
python src/common/cookie_refresh/test_auth.py --service tiktok --dry-run

# View recent logs
python src/common/cookie_refresh/view_logs.py --tail 100
```

## Common Issues

### Issue: "Cookie refresh failed for all services"

**Symptoms:**
- All services show as failed in logs
- No cookies are being updated
- Notifications report complete failure

**Diagnosis:**
```bash
# Check if refresh system is running
python src/common/cookie_refresh/check_health.py --verbose

# Verify configuration
python src/common/cookie_refresh/validate_config.py

# Test network connectivity
python src/common/cookie_refresh/test_network.py
```

**Solutions:**
1. **Configuration Issues:**
   ```bash
   # Regenerate default config
   python src/common/cookie_refresh/init_config.py --reset
   
   # Validate JSON syntax
   python -m json.tool < config/cookie_refresh_config.json
   ```

2. **Permission Issues:**
   ```bash
   # Fix file permissions (Windows)
   icacls "src\*" /grant Everyone:F /T
   
   # Fix file permissions (Linux/WSL)
   chmod -R 755 src/
   ```

3. **Environment Variables:**
   ```bash
   # Check all required variables
   python src/common/cookie_refresh/check_env.py
   
   # Set missing variables
   set SPOTIFY_CLIENT_ID=your_client_id
   set SPOTIFY_CLIENT_SECRET=your_secret
   ```

### Issue: "Specific service keeps failing"

**Symptoms:**
- One service consistently fails
- Other services work fine
- Service-specific error in logs

**Diagnosis:**
```bash
# Check service status
python src/common/cookie_refresh/check_service.py --service [SERVICE_NAME] --detailed

# View service-specific logs
python src/common/cookie_refresh/view_logs.py --service [SERVICE_NAME] --last-24h

# Test credentials
python src/common/cookie_refresh/test_credentials.py --service [SERVICE_NAME]
```

**Solutions:**
1. **Expired Credentials:**
   ```bash
   # Update service credentials
   python src/common/cookie_refresh/update_credentials.py --service [SERVICE_NAME]
   ```

2. **Strategy Issues:**
   ```bash
   # Test strategy directly
   python src/common/cookie_refresh/test_strategy.py --service [SERVICE_NAME] --verbose
   
   # Try alternative strategy
   python src/common/cookie_refresh/config_editor.py --service [SERVICE_NAME] --strategy alternative
   ```

3. **Cookie Corruption:**
   ```bash
   # Clear service cookies
   python src/common/cookie_refresh/clear_cookies.py --service [SERVICE_NAME]
   
   # Restore from backup
   python src/common/cookie_refresh/restore_backup.py --service [SERVICE_NAME] --latest
   ```

### Issue: "Notifications not being sent"

**Symptoms:**
- No email/Slack notifications received
- Logs show "notification failed"
- Manual test notifications don't work

**Solutions:**
```bash
# Test notification configuration
python src/common/cookie_refresh/test_notifications.py

# Send test notification
python src/common/cookie_refresh/send_test_notification.py --channel email

# Reconfigure notifications
python src/common/cookie_refresh/setup_notifications.py
```

## Service-Specific Issues

### Spotify

**Issue: "OAuth callback timeout"**

**Solution:**
```bash
# Check OAuth configuration
python src/common/cookie_refresh/check_oauth.py --service spotify

# Manually refresh OAuth token
python src/spotify/auth/manual_oauth_refresh.py

# Reset OAuth state
rm -rf .oauth_state/spotify/
```

**Issue: "Invalid client credentials"**

**Solution:**
1. Verify Spotify App settings at https://developer.spotify.com/dashboard
2. Update credentials:
   ```bash
   set SPOTIFY_CLIENT_ID=new_client_id
   set SPOTIFY_CLIENT_SECRET=new_secret
   ```
3. Test authentication:
   ```bash
   python src/common/cookie_refresh/test_auth.py --service spotify
   ```

### TikTok

**Issue: "Captcha detected"**

**Solution:**
```bash
# Enable headful mode for manual captcha solving
python src/common/cookie_refresh/config_editor.py --service tiktok --headless false

# Use alternative login method
python src/tiktok/auth/qr_code_login.py
```

**Issue: "Multiple accounts not refreshing"**

**Solution:**
```bash
# Check account configuration
python src/common/cookie_refresh/list_accounts.py --service tiktok

# Refresh specific account
python src/common/cookie_refresh/refresh_account.py --service tiktok --account zone.a0

# Debug account switching
python src/tiktok/debug_multi_account.py
```

### DistroKid

**Issue: "JWT token expired immediately"**

**Diagnosis:**
```bash
# Check JWT expiration
python src/distrokid/check_jwt_expiry.py

# View JWT claims
python src/distrokid/decode_jwt.py
```

**Solution:**
1. Clear existing tokens:
   ```bash
   rm src/distrokid/cookies/*.json
   ```
2. Force refresh:
   ```bash
   python src/common/cookie_refresh/force_refresh.py --service distrokid
   ```

### TooLost

**Issue: "7-day JWT expiration cycle"**

**Solution:**
```bash
# Set up more frequent refresh
python src/common/cookie_refresh/config_editor.py --service toolost --refresh-interval 144

# Enable expiration warnings
python src/common/cookie_refresh/enable_warnings.py --service toolost --warning-days 2
```

### Linktree

**Issue: "Login page changed"**

**Solution:**
```bash
# Update selectors
python src/linktree/update_selectors.py

# Test new selectors
python src/linktree/test_login_flow.py --debug
```

## 2FA Troubleshooting

### Issue: "2FA timeout"

**Symptoms:**
- "Waiting for 2FA code" message appears
- Process times out before code entry
- Service marked as failed due to 2FA

**Solutions:**

1. **Increase Timeout:**
   ```json
   {
     "services": {
       "tiktok": {
         "2fa_timeout_seconds": 120
       }
     }
   }
   ```

2. **Enable 2FA Notifications:**
   ```bash
   python src/common/cookie_refresh/setup_2fa_alerts.py
   ```

3. **Use App-Specific Passwords:**
   - Generate app passwords when available
   - Store in secure credential manager

### Issue: "2FA code not accepted"

**Solutions:**
1. **Time Sync Issues:**
   ```bash
   # Check system time
   w32tm /query /status  # Windows
   timedatectl status    # Linux
   
   # Sync time
   w32tm /resync
   ```

2. **Wrong 2FA Method:**
   ```bash
   # Configure preferred 2FA method
   python src/common/cookie_refresh/config_2fa.py --service tiktok --method sms
   ```

## Performance Issues

### Issue: "Refresh takes too long"

**Diagnosis:**
```bash
# Profile refresh performance
python src/common/cookie_refresh/profile_refresh.py --service all

# Check resource usage
python src/common/cookie_refresh/resource_monitor.py
```

**Solutions:**

1. **Optimize Concurrency:**
   ```json
   {
     "global": {
       "concurrent_refreshes": 3,
       "thread_pool_size": 5
     }
   }
   ```

2. **Disable Unnecessary Services:**
   ```bash
   python src/common/cookie_refresh/disable_service.py --service rarely_used_service
   ```

3. **Use Caching:**
   ```bash
   python src/common/cookie_refresh/enable_caching.py --ttl 3600
   ```

### Issue: "High CPU/Memory usage"

**Solutions:**
1. **Limit Playwright Instances:**
   ```json
   {
     "playwright": {
       "max_browsers": 2,
       "reuse_context": true
     }
   }
   ```

2. **Enable Resource Limits:**
   ```bash
   python src/common/cookie_refresh/set_limits.py --cpu 50 --memory 1024
   ```

## Recovery Procedures

### Complete System Recovery

If the system is completely broken:

```bash
# 1. Backup current state
python src/common/cookie_refresh/backup_all.py --output backup_$(date +%Y%m%d)

# 2. Reset to defaults
python src/common/cookie_refresh/factory_reset.py --confirm

# 3. Restore services one by one
python src/common/cookie_refresh/restore_service.py --service spotify --from-backup
python src/common/cookie_refresh/restore_service.py --service tiktok --from-backup
# ... repeat for each service

# 4. Test system
python src/common/cookie_refresh/test_all.py
```

### Corrupted Cookie Recovery

```bash
# 1. List available backups
python src/common/cookie_refresh/list_backups.py --service [SERVICE]

# 2. Validate backup
python src/common/cookie_refresh/validate_backup.py --file [BACKUP_FILE]

# 3. Restore from backup
python src/common/cookie_refresh/restore_backup.py --service [SERVICE] --file [BACKUP_FILE]

# 4. Verify restoration
python src/common/cookie_refresh/verify_cookies.py --service [SERVICE]
```

### Database Recovery

```bash
# 1. Check database integrity
python src/common/cookie_refresh/check_db.py

# 2. Repair if needed
python src/common/cookie_refresh/repair_db.py

# 3. Rebuild from cookies
python src/common/cookie_refresh/rebuild_db.py --from-cookies
```

## Debug Mode

### Enable Verbose Logging

```bash
# Set debug level
set COOKIE_REFRESH_LOG_LEVEL=DEBUG

# Enable specific module debugging
set DEBUG_SPOTIFY=1
set DEBUG_PLAYWRIGHT=1

# Run with debug output
python src/common/cookie_refresh/refresher.py --debug
```

### Interactive Debugging

```bash
# Start interactive debug session
python src/common/cookie_refresh/debug_console.py

# Available commands in console:
# > status all
# > refresh spotify --step-through
# > inspect cookies tiktok
# > test strategy distrokid
```

### Capture Debug Information

```bash
# Generate debug report
python src/common/cookie_refresh/generate_debug_report.py --full

# Includes:
# - System information
# - Configuration dump
# - Recent logs
# - Cookie status
# - Network diagnostics
# - Performance metrics
```

## Decision Trees

### "Service Won't Refresh" Decision Tree

```
Service refresh failing?
├─ Are credentials set correctly?
│  ├─ No → Update credentials → Test again
│  └─ Yes → Continue
├─ Is network accessible?
│  ├─ No → Check firewall/proxy → Test connection
│  └─ Yes → Continue
├─ Are cookies corrupted?
│  ├─ Yes → Clear cookies → Retry refresh
│  └─ No → Continue
├─ Is strategy working?
│  ├─ No → Try alternative strategy
│  └─ Yes → Continue
└─ Check service-specific issues
   ├─ 2FA required? → Handle 2FA
   ├─ API changes? → Update strategy
   └─ Rate limited? → Add delays
```

### "System Performance" Decision Tree

```
System running slowly?
├─ Check CPU usage
│  ├─ High → Reduce concurrent refreshes
│  └─ Normal → Continue
├─ Check memory usage
│  ├─ High → Enable browser context reuse
│  └─ Normal → Continue
├─ Check disk I/O
│  ├─ High → Enable cookie caching
│  └─ Normal → Continue
└─ Check network latency
   ├─ High → Optimize request batching
   └─ Normal → Review logs for bottlenecks
```

## Contact Support

If you're still experiencing issues:

1. **Generate Support Bundle:**
   ```bash
   python src/common/cookie_refresh/create_support_bundle.py
   ```

2. **Information to Include:**
   - Error messages and stack traces
   - Service name and configuration
   - Time of last successful refresh
   - Recent changes to system
   - Debug report output

3. **Log Locations:**
   - Main logs: `logs/cookie_refresh/`
   - Service logs: `logs/cookie_refresh/services/`
   - Error logs: `logs/cookie_refresh/errors/`

4. **Before Contacting Support:**
   - Review this troubleshooting guide
   - Check for recent updates
   - Try the recovery procedures
   - Generate a debug report

## Preventive Maintenance

### Daily Checks
```bash
# Morning health check
python src/common/cookie_refresh/daily_check.py
```

### Weekly Maintenance
```bash
# Clean old logs and backups
python src/common/cookie_refresh/cleanup.py --older-than 30

# Optimize database
python src/common/cookie_refresh/optimize_db.py

# Update strategies
python src/common/cookie_refresh/update_strategies.py
```

### Monthly Review
```bash
# Generate monthly report
python src/common/cookie_refresh/monthly_report.py

# Review and update:
# - Credential expiration dates
# - Strategy effectiveness
# - Performance metrics
# - Error patterns
```

## Quick Reference

### Common Commands

```bash
# Force refresh single service
python src/common/cookie_refresh/force_refresh.py --service [SERVICE]

# Disable problematic service
python src/common/cookie_refresh/disable_service.py --service [SERVICE]

# View real-time logs
python src/common/cookie_refresh/tail_logs.py --follow

# Emergency stop
python src/common/cookie_refresh/emergency_stop.py

# Resume after stop
python src/common/cookie_refresh/resume.py
```

### Environment Variables

```bash
# Core settings
COOKIE_REFRESH_BASE_PATH      # Base directory for cookies
COOKIE_REFRESH_LOG_LEVEL      # DEBUG, INFO, WARNING, ERROR
COOKIE_REFRESH_CONFIG_FILE    # Path to config file

# Feature flags
COOKIE_REFRESH_DRY_RUN        # Test without saving
COOKIE_REFRESH_HEADLESS       # Run browsers headless
COOKIE_REFRESH_PARALLEL       # Enable parallel refresh

# Debugging
DEBUG_[SERVICE_NAME]          # Enable service debugging
COOKIE_REFRESH_PROFILE        # Enable performance profiling
COOKIE_REFRESH_TRACE          # Enable trace logging
```

### Service Status Codes

- `HEALTHY` - Cookies valid and recent
- `WARNING` - Cookies aging, refresh recommended
- `EXPIRED` - Cookies expired, refresh required
- `FAILING` - Recent refresh attempts failed
- `DISABLED` - Service disabled in config
- `UNKNOWN` - No status information available

Remember: Most issues can be resolved by checking credentials, clearing cookies, and ensuring network connectivity. When in doubt, run the diagnostic tools before attempting manual fixes.