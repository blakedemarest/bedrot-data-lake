# Meta Ads Data Pipeline

## Overview
The Meta Ads Data Pipeline provides comprehensive automation for extracting, processing, and analyzing Facebook and Instagram advertising data through the Facebook Marketing API. This pipeline delivers detailed campaign performance metrics, audience insights, conversion tracking, and ROI analysis to optimize BEDROT's social media advertising strategy and budget allocation.

## Architecture & Components

### Directory Structure
```
metaads/
├── extractors/
│   ├── meta_daily_campaigns_extractor.py   # Enhanced daily performance extractor
│   ├── meta_raw_dump.py                   # Legacy full dump extractor
│   ├── pixel_events_extractor.py           # Meta Pixel event aggregation
│   └── audience_insights_extractor.py      # Detailed audience analytics
├── cleaners/
│   ├── metaads_daily_landing2raw.py        # Daily pipeline: landing to raw
│   ├── metaads_daily_raw2staging.py        # Daily pipeline: raw to staging
│   ├── metaads_daily_staging2curated.py    # Daily pipeline: staging to curated
│   ├── metaads_landing2raw.py              # Legacy pipeline: landing to raw
│   ├── metaads_raw2staging.py              # Legacy pipeline: raw to staging
│   └── metaads_staging2curated.py          # Legacy pipeline: staging to curated
├── cache/
│   ├── campaign_activity.db                # Campaign activity tracking database
│   ├── api_rate_limits.json                # Rate limiting state management
│   └── access_token_cache.json             # Token management and refresh
├── schemas/
│   ├── campaign_data_schema.json           # Campaign data structure
│   ├── pixel_events_schema.json            # Meta Pixel events schema
│   └── audience_insights_schema.json       # Audience data schema
└── utils/
    ├── api_client.py                       # Facebook Marketing API client
    ├── campaign_manager.py                 # Campaign activity management
    └── data_quality_validator.py          # Meta Ads data validation
```

## Data Sources & Metrics

### Campaign Performance Data
- **Core metrics**: Reach, impressions, clicks, spend, cost-per-click (CPC)
- **Engagement metrics**: Post reactions, comments, shares, video views
- **Conversion metrics**: Link clicks, landing page views, purchases
- **Audience metrics**: Frequency, unique reach, audience overlap
- **Placement performance**: Feed, Stories, Reels, Audience Network breakdown

### Meta Pixel Events & Conversions
- **E-commerce events**: ViewContent, AddToCart, Purchase, CompleteRegistration
- **Custom events**: Lead generation, newsletter signups, music streaming clicks
- **Conversion values**: Revenue attribution and value per conversion
- **Funnel analysis**: Customer journey from impression to conversion
- **Attribution windows**: 1-day, 7-day, 28-day attribution analysis

### Audience Insights
- **Demographics**: Age, gender, location, language preferences
- **Interests**: Music genres, artist preferences, lifestyle interests
- **Behaviors**: Purchase behavior, device usage, platform engagement
- **Custom audiences**: Lookalike audience performance and expansion
- **Retargeting metrics**: Website visitors, video viewers, engagement audiences

### Financial & ROI Metrics
- **Cost analysis**: Detailed spend breakdown by campaign, ad set, and ad
- **Return on ad spend (ROAS)**: Revenue generated per dollar spent
- **Cost per result**: CPC, cost per conversion, cost per acquisition
- **Lifetime value**: Customer lifetime value from Facebook/Instagram traffic
- **Budget utilization**: Spend pacing and budget efficiency analysis

## Extraction Methods

### Enhanced Daily Extractor (Recommended)
```python
# Advanced daily campaign performance extraction
from src.metaads.extractors.meta_daily_campaigns_extractor import MetaDailyExtractor

# Initialize with comprehensive configuration
extractor = MetaDailyExtractor(
    ad_account_id='act_your_account_id',
    extract_pixel_events=True,
    activity_tracking=True,
    rate_limit_optimization=True
)

# Execute daily extraction with full analytics
results = await extractor.extract_daily_performance()

# Enhanced extraction includes:
# - Daily reach, CPC, spend, clicks, impressions per campaign
# - Aggregated Meta Pixel events with conversion tracking
# - Campaign activity management with automatic exclusions
# - Robust error handling and rate limit retry logic
```

### Campaign Activity Intelligence
- **SQLite-based tracking**: Local database maintains campaign activity history
- **Automatic exclusions**: Campaigns inactive for 7+ consecutive days excluded from API calls
- **Activity detection**: Intelligent identification of active vs paused campaigns
- **Performance optimization**: Reduced API quota usage through smart filtering
- **Cache updates**: Real-time activity status updates and historical tracking

### Legacy Full Dump Extractor
```python
# Comprehensive data dump for historical analysis
from src.metaads.extractors.meta_raw_dump import MetaRawDumper

# Extract complete campaign, ad set, ads, and insights data
dumper = MetaRawDumper(api_version='v19.0')
results = dumper.extract_complete_account_data()

# Legacy extraction outputs:
# - campaigns.json: All campaign metadata and settings
# - adsets.json: Ad set configurations and targeting
# - ads.json: Individual ad creative and performance
# - insights.json: Detailed performance insights and metrics
```

## Data Processing Pipelines

### Enhanced Daily Pipeline (Primary)

#### Landing to Raw Zone
```python
# Process daily campaign CSV to validated NDJSON
python src/metaads/cleaners/metaads_daily_landing2raw.py

# Processing includes:
# - CSV to NDJSON format conversion
# - Data structure validation and schema compliance
# - Campaign ID consistency verification
# - Timestamp and date validation
# - Pixel event data integrity checks
```

#### Raw to Staging Zone
```python
# Convert to staging CSV with enhanced pixel event columns
python src/metaads/cleaners/metaads_daily_raw2staging.py

# Transformations include:
# - NDJSON to structured CSV conversion
# - Pixel event column expansion and normalization
# - Metric calculation and derived field creation
# - Currency standardization and conversion
# - Geographic and demographic data enrichment
```

#### Staging to Curated Zone
```python
# Create dual CSV outputs optimized for analytics
python src/metaads/cleaners/metaads_daily_staging2curated.py

# Generates two complementary datasets:
# 1. Campaign metadata with lifetime statistics
# 2. Daily performance log with rolling 28-day history
```

### Legacy Full Dump Pipeline

#### Complete Historical Processing
```bash
# Process full account dump through all zones
python src/metaads/cleaners/metaads_landing2raw.py     # JSON validation and promotion
python src/metaads/cleaners/metaads_raw2staging.py     # Consolidation to tidy_metaads.csv
python src/metaads/cleaners/metaads_staging2curated.py # Final curated output preparation
```

## Output Datasets

### Primary Curated Outputs (curated/metaads/)

#### 1. Campaign Metadata Summary
**File**: `metaads_campaigns_daily.csv`

**Schema**:
```csv
campaign_id,campaign_name,total_spend_usd,total_impressions,total_clicks,max_daily_reach,is_currently_active,avg_cpc,avg_ctr,total_conversions,roas
act_123456789_campaignid,Spring Music Campaign,456.78,125430,3421,8934,true,0.134,0.0273,89,3.45
```

**Key Fields**:
- **Lifetime aggregations**: Total spend, impressions, clicks across campaign lifecycle
- **Performance indicators**: Average CPC, CTR, conversion rates, ROAS
- **Activity status**: Current campaign status and recent activity indicators
- **Peak performance**: Maximum daily reach and best-performing metrics

#### 2. Daily Performance Log
**File**: `metaads_campaigns_performance_log.csv`

**Schema**:
```csv
date,campaign_id,campaign_name,reach,cpc,spend_usd,impressions,clicks,meta_pixel_events,conversions,roas_daily
2024-05-22,act_123456789_campaignid,Spring Music Campaign,2134,0.145,23.45,5430,162,"{""ViewContent"": 45, ""Purchase"": 3}",3,2.89
```

**Key Features**:
- **Rolling 28-day window**: Automatic maintenance of recent performance history
- **JSON pixel events**: Structured Meta Pixel event data with counts and values
- **Daily granularity**: Day-by-day performance tracking for trend analysis
- **Conversion attribution**: Direct linking of ad performance to business outcomes

### Analytical Datasets

#### Campaign ROI Analysis
**File**: `curated/marketing/metaads/campaign_roi_analysis.parquet`

**Metrics**:
- Return on ad spend (ROAS) by campaign and time period
- Customer acquisition cost (CAC) analysis
- Lifetime value to CAC ratio calculations
- Attribution analysis across multiple touchpoints
- Budget efficiency and optimization recommendations

#### Audience Performance Insights
**File**: `curated/marketing/metaads/audience_insights_aggregated.csv`

**Metrics**:
- Demographic performance breakdowns
- Interest and behavior targeting effectiveness
- Custom audience performance comparisons
- Lookalike audience expansion analysis
- Geographic performance and market penetration

## Configuration & Environment

### Required Environment Variables
```bash
# Core Meta Ads API configuration
META_ACCESS_TOKEN=your_long_lived_access_token
META_AD_ACCOUNT_ID=act_your_numeric_account_id
META_APP_ID=your_facebook_app_id
META_APP_SECRET=your_facebook_app_secret

# Data lake configuration
PROJECT_ROOT=/path/to/data_lake

# API optimization settings
META_API_VERSION=v18.0
META_RATE_LIMIT_BUFFER=0.8
META_RETRY_ATTEMPTS=3
META_REQUEST_TIMEOUT=30

# Campaign activity tracking
META_INACTIVE_THRESHOLD_DAYS=7
META_ACTIVITY_CACHE_TTL_HOURS=24
META_ENABLE_ACTIVITY_FILTERING=true
```

### Dependencies
```bash
# Core Facebook Marketing API
facebook-business>=19.0.0
requests>=2.28.0

# Data processing
pandas>=1.5.0
numpy>=1.21.0
pyarrow>=10.0.0

# Database and caching
sqlite3  # Built-in Python module
redis>=4.0.0  # Optional for advanced caching

# Utilities
jsonschema>=4.0.0
dateutil>=2.8.0
cryptography>=3.4.0
```

## Usage Examples

### Daily Extraction Workflow (Recommended)
```bash
# Navigate to data lake directory
cd "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake"

# Execute complete daily pipeline
python src/metaads/extractors/meta_daily_campaigns_extractor.py
python src/metaads/cleaners/metaads_daily_landing2raw.py
python src/metaads/cleaners/metaads_daily_raw2staging.py
python src/metaads/cleaners/metaads_daily_staging2curated.py
```

### Custom Analytics Processing
```python
# Advanced Meta Ads analytics
import pandas as pd
from src.metaads.utils.analytics_processor import MetaAdsAnalyzer

# Initialize analyzer with account configuration
analyzer = MetaAdsAnalyzer(account_id='act_your_account_id')

# Load performance data
campaign_data = analyzer.load_campaign_performance(date_range='last_30_days')
audience_data = analyzer.load_audience_insights(date_range='last_30_days')

# Generate comprehensive insights
roi_analysis = analyzer.calculate_campaign_roi(campaign_data)
audience_insights = analyzer.analyze_audience_performance(audience_data)
optimization_recommendations = analyzer.generate_optimization_recommendations(campaign_data)

# Export detailed reports
analyzer.export_comprehensive_report({
    'roi_analysis': roi_analysis,
    'audience_insights': audience_insights,
    'optimization_recommendations': optimization_recommendations
}, 'meta_ads_comprehensive_analysis.xlsx')
```

### Campaign Performance Analysis
```python
# ROI and performance optimization
def analyze_campaign_performance(campaign_log_data):
    """Comprehensive campaign performance analysis"""
    
    # Calculate key performance metrics
    performance_metrics = campaign_log_data.groupby('campaign_id').agg({
        'spend_usd': 'sum',
        'impressions': 'sum',
        'clicks': 'sum',
        'conversions': 'sum',
        'roas_daily': 'mean'
    })
    
    # Calculate derived metrics
    performance_metrics['total_ctr'] = performance_metrics['clicks'] / performance_metrics['impressions']
    performance_metrics['cost_per_conversion'] = performance_metrics['spend_usd'] / performance_metrics['conversions']
    performance_metrics['conversion_rate'] = performance_metrics['conversions'] / performance_metrics['clicks']
    
    # Identify top performers and optimization opportunities
    top_performers = performance_metrics.nlargest(5, 'roas_daily')
    optimization_targets = performance_metrics[performance_metrics['roas_daily'] < 2.0]
    
    return {
        'overall_metrics': performance_metrics,
        'top_performers': top_performers,
        'optimization_opportunities': optimization_targets
    }
```

## Campaign Activity Management

### Intelligent Activity Tracking
```python
# Campaign activity management system
class CampaignActivityManager:
    def __init__(self, cache_db_path='src/metaads/cache/campaign_activity.db'):
        self.db_path = cache_db_path
        self.inactive_threshold_days = 7
    
    def update_campaign_activity(self, campaign_data):
        """Update campaign activity status based on recent performance"""
        active_campaigns = set()
        
        for campaign in campaign_data:
            if self.has_recent_activity(campaign):
                active_campaigns.add(campaign['campaign_id'])
                self.record_activity(campaign['campaign_id'])
            else:
                self.increment_inactive_days(campaign['campaign_id'])
        
        return self.get_active_campaigns()
    
    def get_api_optimization_filter(self):
        """Get list of campaigns to exclude from API calls"""
        inactive_campaigns = self.get_inactive_campaigns(threshold_days=self.inactive_threshold_days)
        
        # Return filter to exclude long-inactive campaigns
        return {
            'exclude_campaign_ids': inactive_campaigns,
            'optimization_benefit': f"Reducing API calls by {len(inactive_campaigns)} campaigns"
        }
```

### API Efficiency Optimization
- **Quota management**: Intelligent API call reduction through activity filtering
- **Rate limiting**: Built-in rate limit compliance with exponential backoff
- **Error recovery**: Robust error handling with automatic retry logic
- **Cache utilization**: Local caching to minimize redundant API calls

## Data Quality & Monitoring

### Validation Framework
```python
# Meta Ads data quality validation
class MetaAdsDataValidator:
    def validate_campaign_data(self, data):
        """Comprehensive validation of Meta Ads campaign data"""
        validation_results = {
            'schema_compliance': self.validate_schema(data),
            'metric_consistency': self.validate_metric_relationships(data),
            'spending_accuracy': self.validate_spending_data(data),
            'conversion_tracking': self.validate_conversion_data(data),
            'temporal_consistency': self.validate_date_ranges(data)
        }
        
        overall_score = sum(validation_results.values()) / len(validation_results)
        return overall_score, validation_results
    
    def validate_metric_relationships(self, data):
        """Validate logical relationships between metrics"""
        checks = []
        
        # CPC calculation validation
        calculated_cpc = data['spend_usd'] / data['clicks']
        cpc_variance = abs(calculated_cpc - data['cpc']) / data['cpc']
        checks.append(cpc_variance.mean() < 0.05)  # Less than 5% variance
        
        # CTR calculation validation
        calculated_ctr = data['clicks'] / data['impressions']
        ctr_variance = abs(calculated_ctr - data['ctr']) / data['ctr']
        checks.append(ctr_variance.mean() < 0.05)
        
        # Conversion rate validation
        if 'conversions' in data.columns:
            conversion_rate = data['conversions'] / data['clicks']
            checks.append((conversion_rate <= 1.0).all())  # Conversion rate <= 100%
        
        return sum(checks) / len(checks)
```

## Integration Points

### Cross-Platform Marketing Integration
- **Unified campaign tracking**: Meta Ads performance vs other advertising platforms
- **Attribution modeling**: Multi-touch attribution across Meta and other channels
- **Audience overlap**: Cross-platform audience analysis and optimization
- **Budget allocation**: Data-driven budget distribution across marketing channels

### Business Intelligence Integration
- **Revenue attribution**: Direct linking of Meta Ads spend to streaming and sales revenue
- **Customer journey analysis**: Complete funnel from Meta Ads impression to conversion
- **Lifetime value tracking**: Long-term customer value from Meta Ads acquisition
- **ROI optimization**: Automated recommendations for campaign optimization

### Real-time Dashboard Integration
- **Live performance monitoring**: Real-time campaign performance tracking
- **Budget alerts**: Automated notifications for budget pacing and overspend
- **Performance alerts**: Notifications for significant performance changes
- **Optimization suggestions**: AI-driven recommendations for campaign improvements

## Troubleshooting

### Common Issues

#### API Authentication Problems
```bash
# Validate Meta Ads API access
python src/metaads/utils/validate_api_access.py

# Refresh access token
python src/metaads/utils/refresh_access_token.py

# Test API permissions
python src/metaads/utils/test_api_permissions.py
```

#### Data Extraction Failures
```bash
# Check campaign activity and API quota
python src/metaads/utils/check_campaign_status.py

# Debug extraction with detailed logging
python src/metaads/extractors/meta_daily_campaigns_extractor.py --debug

# Validate API response structure
python src/metaads/utils/validate_api_responses.py
```

#### Processing Pipeline Errors
```bash
# Validate extracted data structure
python src/metaads/utils/validate_campaign_data.py

# Test processing pipeline
python src/metaads/cleaners/metaads_daily_raw2staging.py --test-mode

# Check schema compliance
python src/metaads/utils/schema_validator.py
```

## Future Enhancements

### Planned Improvements
- **Real-time optimization**: Live campaign optimization based on performance data
- **Advanced attribution modeling**: Multi-touch attribution with machine learning
- **Predictive analytics**: Campaign performance prediction and budget forecasting
- **Automated A/B testing**: Systematic creative and targeting optimization

### Integration Enhancements
- **Advanced audience insights**: Deeper demographic and psychographic analysis
- **Cross-platform attribution**: Unified attribution across all marketing channels
- **Dynamic budget allocation**: AI-driven budget optimization across campaigns
- **Creative performance analysis**: Automated creative testing and optimization

## Related Documentation
- See `data_lake/docs/meta_ads_integration.md` for detailed API setup and configuration
- Reference `data_lake/schemas/metaads/` for complete schema documentation
- Check `data_lake/tests/metaads/` for comprehensive test suite and validation
- Review `data_lake/examples/metaads/` for usage examples and advanced analytics patterns
