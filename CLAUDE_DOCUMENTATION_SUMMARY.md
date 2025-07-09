# Data Lake CLAUDE.md Documentation Summary

This document summarizes all CLAUDE.md files created throughout the data_lake directory structure to help developers navigate and work efficiently with the BEDROT Data Lake.

## Files Created

### 1. `/data_lake/src/CLAUDE.md`
**Purpose**: Main source code documentation
- Overview of all platform integrations
- Common development patterns
- Adding new data sources guide
- Key utilities and conventions
- Import troubleshooting

### 2. `/data_lake/src/spotify/CLAUDE.md`
**Purpose**: Spotify pipeline documentation
- Spotify for Artists data extraction
- Audience analytics processing
- Authentication with Playwright
- Data schema and metrics
- Rate limiting considerations

### 3. `/data_lake/src/tiktok/CLAUDE.md`
**Purpose**: TikTok pipeline documentation
- Multi-account analytics extraction
- ZIP file processing
- Schema migration handling
- Engagement metrics calculation
- Advanced follower analysis

### 4. `/data_lake/src/distrokid/CLAUDE.md`
**Purpose**: DistroKid pipeline documentation
- Streaming and financial data extraction
- HTML parsing techniques
- Multi-currency handling
- Platform consolidation
- Revenue tracking

### 5. `/data_lake/src/metaads/CLAUDE.md`
**Purpose**: Meta Ads pipeline documentation
- Facebook/Instagram advertising data
- API and manual CSV processing
- Campaign performance metrics
- Attribution window configuration
- ROAS calculations

### 6. `/data_lake/src/linktree/CLAUDE.md`
**Purpose**: Linktree pipeline documentation
- Link analytics extraction
- GraphQL interception
- Traffic source analysis
- Click-through rate optimization
- Cross-platform correlation

### 7. `/data_lake/src/toolost/CLAUDE.md`
**Purpose**: TooLost pipeline documentation
- Multi-platform streaming aggregation
- Cross-platform validation
- Historical data import
- Platform comparison analytics
- Data reconciliation

### 8. `/data_lake/tests/CLAUDE.md`
**Purpose**: Testing framework documentation
- Test organization and structure
- Writing effective tests
- Mocking external dependencies
- Performance and integration testing
- CI/CD integration

### 9. `/data_lake/cronjob/CLAUDE.md`
**Purpose**: Automation and scheduling documentation
- Pipeline orchestration
- Batch file configuration
- Error handling strategies
- Monitoring and health checks
- Scheduling best practices

### 10. `/data_lake/zones/CLAUDE.md`
**Purpose**: Data Lake architecture documentation
- Zone-based data flow
- Promotion criteria
- Data quality standards
- Access control policies
- Archive management

## Key Themes Across Documentation

### 1. **Consistent Structure**
All service directories follow the same pattern:
- `extractors/` - Data collection scripts
- `cleaners/` - Three-stage processing pipeline
- `cookies/` - Authentication management

### 2. **Common Patterns**
- Environment variable configuration
- Rate limiting implementation
- Error handling strategies
- Data quality validation
- Testing approaches

### 3. **Data Flow**
Standard progression through zones:
```
landing → raw → staging → curated → archive
```

### 4. **Authentication Methods**
- Cookie-based (Spotify, TikTok, Linktree)
- API key (Meta Ads, TooLost)
- Browser automation (DistroKid)

### 5. **Quality Standards**
- Completeness checks
- Consistency validation
- Accuracy verification
- Timeliness monitoring

## Quick Reference Guide

### Running Extractors
```bash
cd /mnt/c/Users/Earth/BEDROT\ PRODUCTIONS/bedrot-data-ecosystem/data_lake
export PROJECT_ROOT=$(pwd)
python src/<service>/extractors/<extractor_name>.py
```

### Processing Data
```bash
python src/<service>/cleaners/<service>_landing2raw.py
python src/<service>/cleaners/<service>_raw2staging.py
python src/<service>/cleaners/<service>_staging2curated.py
```

### Running Full Pipeline
```bash
.\cronjob\run_datalake_cron.bat
```

### Testing
```bash
pytest tests/<service>/ -v
```

## Best Practices Summary

1. **Always set PROJECT_ROOT** before running scripts
2. **Follow naming conventions** for cleaners
3. **Implement rate limiting** for external APIs
4. **Validate data** at each zone transition
5. **Document service-specific quirks**
6. **Test with sample data** before production
7. **Monitor pipeline health** regularly
8. **Archive old data** to manage storage

## Integration Points

All data ultimately flows to:
- **Data Warehouse**: SQLite database with structured tables
- **Data Dashboard**: Real-time visualization
- **Archive Storage**: Long-term data preservation

## Future Enhancements

Common themes for improvement:
- Real-time/webhook integrations
- Advanced analytics features
- Cross-platform correlations
- Automated optimization
- Enhanced monitoring

---

This comprehensive documentation ensures that developers can efficiently work with any component of the BEDROT Data Lake, understanding both the specific details of each service and the overall patterns that unite them.