# Curated Zone

## Purpose
The curated zone represents the gold standard of the BEDROT Data Lake, containing business-ready, analytics-optimized datasets that serve as the primary consumption layer for end-users, applications, dashboards, and machine learning models. This zone provides clean, consistent, and reliable data products that enable high-quality business intelligence and data-driven decision making.

## What Goes Here
- **Business-ready datasets**: Production-quality data optimized for analytics consumption
- **Aggregated metrics**: Summarized data with business logic and calculations applied
- **Enriched datasets**: Data enhanced with derived fields, business rules, and contextual information
- **Data marts**: Domain-specific datasets organized for particular business use cases
- **Cross-platform aggregations**: Unified views combining data from multiple source platforms
- **Performance-optimized tables**: Indexed and partitioned datasets for fast query performance
- **Master data**: Authoritative reference datasets (artists, tracks, campaigns)
- **Time-series datasets**: Historical trends and temporal analytics

## Platform-Specific Curated Outputs

### Streaming Analytics
- **`daily_streams_distrokid.csv`**: Daily streaming metrics from DistroKid platform
- **`daily_streams_toolost.csv`**: Daily streaming metrics from TooLost analytics
- **`streaming_performance_unified.parquet`**: Cross-platform streaming aggregations
- **`artist_performance_trends.parquet`**: Long-term artist performance analytics
- **`platform_comparison_metrics.csv`**: Comparative performance across streaming platforms

### Social Media Analytics
- **`linktree_analytics_curated_YYYYMMDD_HHMMSS.csv`**: Daily Linktree click analytics
- **`tiktok_performance_summary.parquet`**: Video and account performance metrics
- **`social_media_engagement_unified.csv`**: Cross-platform social media metrics
- **`influencer_performance_kpis.parquet`**: Creator and influencer analytics

### Marketing & Advertising
- **`metaads_campaigns_daily.csv`**: Campaign metadata and lifetime statistics
- **`metaads_campaigns_performance_log.csv`**: Daily performance metrics with 28-day history
- **`campaign_roi_analysis.parquet`**: Return on investment calculations
- **`audience_insights_aggregated.csv`**: Demographic and behavioral targeting analysis

### Financial Analytics
- **`revenue_summary_monthly.parquet`**: Monthly revenue aggregations by platform
- **`payout_tracking.csv`**: Payment processing and reconciliation data
- **`financial_performance_kpis.parquet`**: Key financial performance indicators
- **`cost_analysis_campaigns.csv`**: Marketing spend analysis and optimization

## Directory Structure
```
curated/
├── streaming/
│   ├── daily/
│   │   ├── daily_streams_distrokid.csv
│   │   ├── daily_streams_toolost.csv
│   │   └── streaming_performance_unified.parquet
│   ├── monthly/
│   │   ├── monthly_streaming_summary_2024.parquet
│   │   └── artist_performance_trends.parquet
│   └── analytics/
│       ├── platform_comparison_metrics.csv
│       └── streaming_forecasts.parquet
├── social_media/
│   ├── linktree/
│   │   └── linktree_analytics_curated_20240522_120000.csv
│   ├── tiktok/
│   │   ├── tiktok_performance_summary.parquet
│   │   └── video_analytics_detailed.csv
│   └── unified/
│       ├── social_media_engagement_unified.csv
│       └── cross_platform_audience_analysis.parquet
├── marketing/
│   ├── metaads/
│   │   ├── metaads_campaigns_daily.csv
│   │   ├── metaads_campaigns_performance_log.csv
│   │   └── campaign_roi_analysis.parquet
│   ├── campaigns/
│   │   ├── campaign_performance_summary.parquet
│   │   └── audience_insights_aggregated.csv
│   └── analytics/
│       ├── marketing_attribution.parquet
│       └── customer_acquisition_cost.csv
├── financial/
│   ├── revenue/
│   │   ├── revenue_summary_monthly.parquet
│   │   ├── revenue_by_platform.csv
│   │   └── revenue_forecasting.parquet
│   ├── payouts/
│   │   ├── payout_tracking.csv
│   │   └── payment_reconciliation.parquet
│   └── analytics/
│       ├── financial_performance_kpis.parquet
│       └── profitability_analysis.csv
├── master_data/
│   ├── artists/
│   │   ├── artist_master.parquet
│   │   └── artist_metadata_enriched.csv
│   ├── tracks/
│   │   ├── track_catalog.parquet
│   │   └── track_performance_history.csv
│   └── campaigns/
│       ├── campaign_master.parquet
│       └── campaign_taxonomy.csv
└── business_intelligence/
    ├── executive_dashboard/
    │   ├── executive_kpis_daily.csv
    │   ├── performance_scorecard.parquet
    │   └── trend_analysis.csv
    ├── operational_reports/
    │   ├── daily_operations_summary.parquet
    │   └── weekly_performance_report.csv
    └── predictive_analytics/
        ├── streaming_forecasts.parquet
        ├── revenue_predictions.csv
        └── audience_growth_models.parquet
```

## Data Quality Standards

### Schema Management
- **Version control**: All schemas tracked with semantic versioning
- **Backward compatibility**: Changes maintain compatibility with existing consumers
- **Documentation**: Comprehensive data dictionaries and field descriptions
- **Validation**: Automated schema validation and compliance checking

### Data Governance
- **Business rules**: Consistent application of business logic across datasets
- **Data lineage**: Complete traceability from source to curated datasets
- **Quality metrics**: Automated data quality scoring and monitoring
- **Access control**: Role-based access with appropriate security controls

### Performance Optimization
- **Partitioning**: Strategic data partitioning for query performance
- **Indexing**: Optimized indexing for common query patterns
- **Compression**: Efficient storage with minimal query impact
- **Caching**: Intelligent caching for frequently accessed datasets

## Business Logic & Transformations

### Metric Calculations
```sql
-- Example: Cross-platform engagement rate calculation
SELECT 
    platform,
    date,
    SUM(interactions) / NULLIF(SUM(impressions), 0) as engagement_rate,
    SUM(revenue) / NULLIF(SUM(spend), 0) as return_on_ad_spend
FROM staging_unified_metrics
GROUP BY platform, date
```

### Data Enrichment
```python
# Example: Artist performance classification
def classify_artist_performance(streams, engagement, revenue):
    if revenue > 1000 and engagement > 0.05:
        return 'High Performer'
    elif streams > 10000 and engagement > 0.02:
        return 'Rising Star'
    elif revenue > 100:
        return 'Monetizing'
    else:
        return 'Developing'
```

### Aggregation Rules
- **Temporal aggregations**: Daily, weekly, monthly, quarterly summaries
- **Dimensional aggregations**: By platform, artist, campaign, geography
- **Statistical calculations**: Averages, percentiles, growth rates, trends
- **Business metrics**: ROI, CAC, LTV, engagement rates, conversion rates

## Data Products & Use Cases

### Executive Dashboard Feeds
- **Real-time KPIs**: Streaming performance, revenue, audience growth
- **Trend analysis**: Month-over-month, year-over-year comparisons
- **Performance scorecards**: Artist, campaign, and platform rankings
- **Predictive insights**: Forecasting and trend projections

### Operational Analytics
- **Campaign optimization**: Performance analysis and recommendations
- **Content strategy**: Track and artist performance insights
- **Audience development**: Fan engagement and growth strategies
- **Financial planning**: Revenue forecasting and budget allocation

### Machine Learning Features
- **Feature engineering**: ML-ready feature sets for predictive models
- **Training datasets**: Labeled data for supervised learning models
- **Model outputs**: Predictions, recommendations, and classifications
- **A/B testing**: Experimental data and statistical analysis

## Data Consumption Patterns

### Dashboard Integration
```python
# Example: Real-time dashboard data feed
import pandas as pd
from datetime import datetime, timedelta

def get_daily_kpis(date=None):
    if not date:
        date = datetime.now().date()
    
    # Load curated datasets
    streaming_data = pd.read_csv(f'curated/streaming/daily/daily_streams_{date}.csv')
    social_data = pd.read_parquet(f'curated/social_media/unified/daily_summary_{date}.parquet')
    
    # Calculate KPIs
    total_streams = streaming_data['streams'].sum()
    engagement_rate = social_data['engagement_rate'].mean()
    
    return {
        'total_streams': total_streams,
        'engagement_rate': engagement_rate,
        'last_updated': datetime.now()
    }
```

### API Endpoints
```python
# Example: FastAPI endpoint for curated data
from fastapi import FastAPI
import pandas as pd

app = FastAPI()

@app.get("/api/artist-performance/{artist_id}")
async def get_artist_performance(artist_id: str, days: int = 30):
    # Load curated artist performance data
    data = pd.read_parquet('curated/streaming/analytics/artist_performance_trends.parquet')
    artist_data = data[data['artist_id'] == artist_id].tail(days)
    
    return {
        'artist_id': artist_id,
        'performance_data': artist_data.to_dict('records'),
        'summary_stats': {
            'avg_daily_streams': artist_data['streams'].mean(),
            'total_revenue': artist_data['revenue'].sum(),
            'growth_rate': calculate_growth_rate(artist_data['streams'])
        }
    }
```

### Automated Reporting
```python
# Example: Automated weekly report generation
def generate_weekly_report():
    # Load curated datasets
    streaming_summary = pd.read_parquet('curated/streaming/weekly/summary.parquet')
    marketing_performance = pd.read_csv('curated/marketing/weekly/campaign_summary.csv')
    
    # Generate insights
    top_performers = streaming_summary.nlargest(10, 'streams')
    campaign_roi = marketing_performance['roi'].mean()
    
    # Create report
    report = {
        'period': get_last_week_dates(),
        'highlights': {
            'top_performing_tracks': top_performers.to_dict('records'),
            'average_campaign_roi': campaign_roi,
            'total_streams': streaming_summary['streams'].sum()
        },
        'generated_at': datetime.now()
    }
    
    return report
```

## Monitoring & Quality Assurance

### Data Quality Metrics
- **Completeness**: Percentage of expected records present
- **Accuracy**: Data validation against business rules
- **Consistency**: Cross-dataset consistency checks
- **Timeliness**: Data freshness and update frequency monitoring
- **Validity**: Schema compliance and data type validation

### Performance Monitoring
- **Query performance**: Response time tracking for common queries
- **Storage utilization**: Disk usage and growth monitoring
- **Access patterns**: User query analysis and optimization opportunities
- **Error rates**: Data processing and transformation error tracking

### Automated Quality Checks
```python
# Example: Daily data quality validation
def validate_daily_curated_data(date):
    checks = []
    
    # Check data completeness
    streaming_data = pd.read_csv(f'curated/streaming/daily/daily_streams_{date}.csv')
    if len(streaming_data) < expected_record_count:
        checks.append({'status': 'FAIL', 'check': 'completeness', 'message': 'Missing records'})
    
    # Check data freshness
    last_update = streaming_data['last_updated'].max()
    if (datetime.now() - last_update).hours > 24:
        checks.append({'status': 'FAIL', 'check': 'freshness', 'message': 'Data outdated'})
    
    # Check business rules
    if streaming_data['streams'].min() < 0:
        checks.append({'status': 'FAIL', 'check': 'validity', 'message': 'Negative stream counts'})
    
    return checks
```

## Integration with Broader Ecosystem

### Data Warehouse Integration
Curated datasets are automatically synchronized with the SQLite data warehouse:
- **Incremental loading**: Efficient updates for large datasets
- **Schema evolution**: Automated schema migration and versioning
- **Performance optimization**: Optimized table structures for analytical queries
- **Data validation**: Consistency checks between lake and warehouse

### Real-time Dashboard Feeds
Curated data powers real-time analytics dashboards:
- **WebSocket updates**: Live data streaming to dashboard components
- **Caching layers**: Redis caching for high-frequency queries
- **API gateways**: RESTful APIs for dashboard data consumption
- **Event-driven updates**: Real-time notifications for data changes

### Machine Learning Pipeline
Curated datasets serve as input for ML models:
- **Feature stores**: Centralized feature management for ML models
- **Training pipelines**: Automated model training with curated data
- **Model deployment**: Integration with ML serving infrastructure
- **Experiment tracking**: A/B testing and model performance monitoring

## Future Enhancements

### Advanced Analytics
- **Real-time processing**: Stream processing for immediate insights
- **Advanced segmentation**: Customer and audience clustering
- **Predictive modeling**: Forecasting and recommendation systems
- **Anomaly detection**: Automated outlier identification and alerting

### Data Product Expansion
- **Industry benchmarking**: Comparative analysis with industry standards
- **Competitive intelligence**: Market analysis and competitor tracking
- **Customer journey mapping**: End-to-end customer experience analytics
- **Attribution modeling**: Multi-touch attribution for marketing campaigns

## Related Documentation
- See `data_lake/src/*/cleaners/*_staging2curated.py` for curation logic
- Reference `data_warehouse/etl/` for warehouse integration scripts
- Check `data_dashboard/backend/api/` for data consumption endpoints
- Review `data_lake/docs/business_rules.md` for transformation specifications
