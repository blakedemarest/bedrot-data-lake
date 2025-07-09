# Service URL Requirements

This document defines the URL requirements for each service in the BEDROT data ecosystem to ensure cookie refresh strategies are compatible with their corresponding extractors.

## ⚠️ **CRITICAL**: URL Compatibility

**Cookie refresh strategies MUST use URLs that are compatible with their service extractors.** Using the wrong URLs will cause authentication failures during the cron job pipeline.

### Example of the Problem We Solved

**❌ WRONG**: Cookie refresh using `https://accounts.spotify.com/login` → Opens consumer login  
**✅ CORRECT**: Cookie refresh using `https://artists.spotify.com` → Opens Spotify for Artists login  

**WHY THIS MATTERS**: If the cookie refresh opens the wrong login page, the saved cookies won't work with the extractor that expects a different type of account.

---

## 🎵 Spotify for Artists

### Purpose
Extract audience analytics for artist accounts (ZONE A0, PIG1987)

### Required URLs
- **Domain**: `artists.spotify.com`
- **Login URL**: `https://artists.spotify.com`
- **Target URLs**: 
  - `https://artists.spotify.com/c/en/artist/{ARTIST_ID}`
  - `https://artists.spotify.com/home`

### Forbidden URLs
- ❌ `https://accounts.spotify.com/login` (consumer login)
- ❌ `https://accounts.spotify.com/en/status` (status page)
- ❌ `https://open.spotify.com` (web player)
- ❌ `https://spotify.com/login` (generic login)

### Extractor File
- `src/spotify/extractors/spotify_audience_extractor.py`

### Artist IDs
- **ZONE A0**: `62owJQCD2XzVB2o19CVsFM`
- **PIG1987**: `1Eu67EqPy2NutiM0lqCarw`

---

## 🎥 TikTok Creator Center

### Purpose
Extract analytics for creator accounts (pig1987, zonea0)

### Required URLs
- **Domain**: `tiktok.com`
- **Login URL**: `https://www.tiktok.com/login`
- **Target URLs**:
  - `https://www.tiktok.com/creator-center`
  - `https://www.tiktok.com/tiktokstudio/creator_center/homepage`

### Forbidden URLs
- ❌ `https://accounts.tiktok.com` (separate accounts system)

### Extractor Files
- `src/tiktok/extractors/tiktok_analytics_extractor_pig1987.py`
- `src/tiktok/extractors/tiktok_analytics_extractor_zonea0.py`

### Supported Accounts
- **pig1987**
- **zonea0**

---

## 🎯 TooLost Music Analytics

### Purpose
Extract music streaming analytics via JWT API

### Required URLs
- **Domain**: `toolost.com`
- **Login URL**: `https://toolost.com/login`
- **Target URLs**:
  - `https://toolost.com/user-portal/analytics/platform`
  - `https://toolost.com/api/portal/*`

### Special Requirements
- ⚠️ **JWT expires every 7 days** - requires weekly refresh
- Uses localStorage for JWT token storage
- API access requires valid JWT

### Extractor Files
- `src/toolost/extractors/toolost_scraper.py`
- `src/toolost/extractors/toolost_scraper_cron.py`

---

## 🔗 Linktree Analytics

### Purpose
Extract link click analytics from Linktree dashboard

### Required URLs
- **Domain**: `linktr.ee`
- **Login URL**: `https://linktr.ee/login`
- **Target URLs**:
  - `https://linktr.ee/admin`
  - `https://linktr.ee/admin/analytics`

### Extractor File
- `src/linktree/extractors/linktree_analytics_extractor.py`

---

## 🎵 DistroKid Music Distribution

### Purpose
Extract music distribution analytics and earnings

### Required URLs
- **Domain**: `distrokid.com`
- **Login URL**: `https://distrokid.com/signin`
- **Target URLs**:
  - `https://distrokid.com/dashboard`
  - `https://distrokid.com/bank`

### Extractor Files
- `src/distrokid/extractors/dk_auth.py`

---

## 🛡️ Validation System

### Automatic Validation
The system now automatically validates URLs before running cookie refresh strategies:

```python
# This happens automatically in the cookie refresh system
validate_service_strategy('spotify', strategy)
```

### Manual Validation
To manually test a service configuration:

```python
from common.cookie_refresh.service_validator import ServiceURLValidator

validator = ServiceURLValidator()
result = validator.validate_strategy_urls('spotify', {
    'login_url': 'https://artists.spotify.com',
    'artists_url': 'https://artists.spotify.com'
})
```

### Error Examples
```
❌ URL validation failed for spotify:
  - login_url 'https://accounts.spotify.com/login' contains forbidden domain: accounts.spotify.com/login
  - login_url 'https://accounts.spotify.com/login' must contain one of: ['artists.spotify.com']
```

---

## 🚀 Adding New Services

When adding a new service, follow these steps:

### 1. Define URL Requirements
Add configuration to `src/common/cookie_refresh/service_validator.py`:

```python
configs['newservice'] = ServiceURLConfig(
    service_name='newservice',
    required_domains=['newservice.com'],
    forbidden_domains=['wrong-domain.com'],
    extractor_urls=[
        'https://newservice.com/dashboard',
        'https://newservice.com/api'
    ],
    expected_patterns=[
        r'newservice\.com',
        r'newservice\.com/dashboard'
    ]
)
```

### 2. Create Strategy
Implement refresh strategy in `src/common/cookie_refresh/strategies/newservice.py`:

```python
class NewServiceRefreshStrategy(BaseRefreshStrategy):
    def __init__(self, service_name: str, storage_manager: CookieStorageManager, ...):
        super().__init__(service_name, storage_manager, notifier, config)
        
        # CRITICAL: Use URLs compatible with extractor
        self.login_url = 'https://newservice.com/login'
        self.dashboard_url = 'https://newservice.com/dashboard'
```

### 3. Create Extractor
Implement extractor in `src/newservice/extractors/newservice_extractor.py`:

```python
# CRITICAL: Use same domain as refresh strategy
DASHBOARD_URL = 'https://newservice.com/dashboard'
LOGIN_URL = 'https://newservice.com/login'
```

### 4. Test Compatibility
```bash
python -c "
from common.cookie_refresh.strategies.newservice import NewServiceRefreshStrategy
from common.cookie_refresh.service_validator import validate_service_strategy
strategy = NewServiceRefreshStrategy('newservice', storage_manager)
validate_service_strategy('newservice', strategy)
print('✅ URLs validated!')
"
```

---

## 🔍 Troubleshooting

### Problem: "Wrong login page opens"
**Cause**: Cookie refresh strategy uses different domain than extractor  
**Solution**: Check that both use the same base domain and login flow

### Problem: "Cookies not working after refresh"
**Cause**: Strategy saved cookies for wrong domain/subdomain  
**Solution**: Verify domain filtering in cookie saving logic

### Problem: "Validation errors on startup"
**Cause**: URL configuration mismatch  
**Solution**: Check service URL configuration against actual extractor URLs

### Problem: "Authentication works but extractor fails"
**Cause**: Different authentication scopes (e.g., consumer vs. business account)  
**Solution**: Ensure both use the same type of account/access level

---

## 📋 Pre-Launch Checklist

Before deploying any service changes:

- [ ] ✅ Cookie refresh strategy URLs validated
- [ ] ✅ Extractor URLs match strategy domains  
- [ ] ✅ Test login flow end-to-end
- [ ] ✅ Verify cookie domain filtering
- [ ] ✅ Check account type compatibility
- [ ] ✅ Test cron job integration
- [ ] ✅ Document any special requirements

---

## 🚨 Emergency Recovery

If wrong URLs get deployed:

1. **Immediate**: Update strategy URLs to correct domains
2. **Validate**: Run validation tests
3. **Test**: Manual cookie refresh for affected service
4. **Deploy**: Update cron job with fixed configuration
5. **Monitor**: Check next automated run

Remember: **Always test URL compatibility before deploying to production!** 