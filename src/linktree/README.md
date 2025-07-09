# Linktree ETL Pipeline

## Overview
The Linktree ETL pipeline provides automated extraction and processing of click analytics, traffic source data, and audience engagement metrics from the Linktree platform. This pipeline delivers comprehensive insights into link performance, visitor behavior, and conversion tracking for BEDROT's social media and marketing campaigns.

## Architecture & Components

### Directory Structure
```
linktree/
├── extractors/
│   ├── linktree_analytics_extractor.py  # Main Playwright extraction script
│   ├── session_manager.py              # Authentication and session handling
│   └── data_parser.py                  # JSON response parsing utilities
├── cleaners/
│   ├── linktree_landing2raw.py         # Landing to raw validation
│   ├── linktree_raw2staging.py         # Raw to staging transformation
│   └── linktree_staging2curated.py     # Staging to curated finalization
├── cookies/
│   ├── linktree_session.json           # Saved authentication state
│   └── browser_state.json              # Browser context preservation
└── schemas/
    ├── analytics_schema.json           # Expected analytics data structure
    └── click_data_schema.json          # Click tracking data schema
```

## Data Sources & Metrics

### Click Analytics
- **Total clicks**: Aggregate click counts across all links
- **Individual link performance**: Click counts per link/button
- **Time-based analysis**: Hourly, daily, weekly, monthly trends
- **Click-through rates**: Performance ratios and conversion metrics
- **Geographic distribution**: Visitor location and regional performance

### Traffic Sources
- **Referrer analysis**: Source platform identification (Instagram, TikTok, Twitter, etc.)
- **Direct traffic**: Direct Linktree profile visits
- **Search traffic**: Organic search and discovery metrics
- **Campaign attribution**: UTM parameter tracking and campaign performance
- **Social media breakdown**: Platform-specific traffic analysis

### Audience Insights
- **Visitor demographics**: Age, gender, location insights where available
- **Device analytics**: Mobile vs desktop usage patterns
- **Engagement patterns**: Time spent, scroll behavior, interaction rates
- **Conversion tracking**: Click-to-action completion rates
- **Return visitor analysis**: New vs returning visitor behavior

### Link Performance Data
- **Individual link metrics**: Performance by specific links and buttons
- **Content type analysis**: Music links vs social media vs merchandise performance
- **Seasonal trends**: Performance variations over time
- **A/B testing data**: Comparative performance of different link configurations

## Extraction Process

### Automated Data Collection
```python
# Main extraction workflow
from src.linktree.extractors.linktree_analytics_extractor import LinktreeExtractor

# Initialize extractor
extractor = LinktreeExtractor(
    profile_url='https://linktr.ee/bedrotproductions',
    headless=True,
    extract_historical=True,
    date_range_days=30
)

# Execute extraction
analytics_data = await extractor.extract_analytics()

# Data includes:
# - Click metrics and trends
# - Traffic source breakdowns
# - Link performance analytics
# - Audience engagement data
```

### Authentication & Access
- **Creator account access**: Full analytics dashboard access
- **Session persistence**: Maintained login state across extractions
- **API endpoint monitoring**: Direct API call interception for real-time data
- **Rate limiting compliance**: Respectful request pacing
- **Error handling**: Robust failure recovery and retry logic

### Data Capture Methods
- **API response interception**: Capture analytics API calls
- **Dashboard scraping**: Extract visible analytics data
- **Export functionality**: Utilize built-in data export features
- **Real-time monitoring**: Continuous data collection for trending analysis

## Data Processing Pipeline

### Landing to Raw Zone
```python
# Validation and promotion
python src/linktree/cleaners/linktree_landing2raw.py

# Validation includes:
# - JSON structure validation
# - Data completeness checks
# - Timestamp consistency verification
# - API response integrity validation
```

### Raw to Staging Zone
```python
# Data cleaning and standardization
python src/linktree/cleaners/linktree_raw2staging.py

# Transformations:
# - Date/time standardization
# - Click metric normalization
# - Traffic source categorization
# - Geographic data standardization
# - URL and link name cleaning
```

### Staging to Curated Zone
```python
# Business logic and analytics preparation
python src/linktree/cleaners/linktree_staging2curated.py

# Business transformations:
# - Click-through rate calculations
# - Traffic source attribution
# - Performance trend analysis
# - Conversion funnel metrics
# - Campaign performance attribution
```

## Output Datasets

### Daily Click Analytics
**File**: `curated/social_media/linktree/linktree_analytics_curated_YYYYMMDD_HHMMSS.csv`

**Schema**:
```csv
date,link_name,link_url,clicks,click_rate,traffic_source,device_type,location,timestamp
2024-05-22,Spotify Profile,https://open.spotify.com/artist/...,45,0.034,instagram,mobile,US,2024-05-22 12:00:00
```

### Traffic Source Analysis
**File**: `curated/social_media/linktree/traffic_sources_daily.csv`

**Schema**:
```csv
date,source_platform,total_clicks,unique_visitors,click_rate,conversion_rate,top_link
2024-05-22,instagram,234,198,0.045,0.12,Spotify Profile
```

### Link Performance Summary
**File**: `curated/social_media/linktree/link_performance_monthly.parquet`

**Metrics**:
- Monthly click totals by link
- Performance trends and growth rates
- Traffic source attribution by link
- Geographic performance distribution
- Device and platform breakdowns

## Configuration & Environment

### Environment Variables
```bash
# Core configuration
PROJECT_ROOT=/path/to/data_lake
LINKTREE_USERNAME=your_username
LINKTREE_PASSWORD=your_password
LINKTREE_PROFILE_URL=https://linktr.ee/your_profile

# Extraction settings
LT_EXTRACTION_INTERVAL_HOURS=24
LT_HISTORICAL_DAYS=30
LT_HEADLESS_MODE=true

# Processing configuration
LT_CLICK_AGGREGATION_ENABLED=true
LT_TRAFFIC_SOURCE_MAPPING=true
LT_GEOGRAPHIC_ANALYSIS=true
```

### Dependencies
```bash
# Required packages
playwright>=1.30.0
pandas>=1.5.0
requests>=2.28.0
numpy>=1.21.0
dateutil>=2.8.0
```

## Usage Examples

### Complete Pipeline Execution
```bash
# Full extraction and processing
cd "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake"

python src/linktree/extractors/linktree_analytics_extractor.py
python src/linktree/cleaners/linktree_landing2raw.py
python src/linktree/cleaners/linktree_raw2staging.py
python src/linktree/cleaners/linktree_staging2curated.py
```

### Custom Analytics Processing
```python
# Custom analysis example
import pandas as pd
from src.linktree.utils.analytics_processor import LinktreeAnalyzer

# Load and analyze data
analyzer = LinktreeAnalyzer()
click_data = analyzer.load_click_data(date_range='last_30_days')

# Generate insights
performance_report = analyzer.generate_performance_report(click_data)
traffic_analysis = analyzer.analyze_traffic_sources(click_data)
conversion_metrics = analyzer.calculate_conversion_rates(click_data)

# Export results
analyzer.export_insights(performance_report, 'monthly_performance.xlsx')
```

## Analytics & Insights

### Key Performance Indicators
- **Total clicks**: Overall link engagement
- **Click-through rate**: Engagement efficiency
- **Traffic source diversity**: Platform distribution health
- **Conversion rate**: Action completion percentage
- **Growth rate**: Period-over-period performance improvement

### Performance Analysis
```python
# Performance calculation examples
def calculate_link_performance_score(clicks, ctr, conversion_rate):
    """Calculate composite performance score"""
    return (clicks * 0.4) + (ctr * 0.35) + (conversion_rate * 0.25)

def analyze_traffic_source_effectiveness(traffic_data):
    """Analyze which platforms drive highest quality traffic"""
    return traffic_data.groupby('source_platform').agg({
        'clicks': 'sum',
        'unique_visitors': 'sum',
        'conversion_rate': 'mean',
        'click_rate': 'mean'
    }).sort_values('conversion_rate', ascending=False)
```

### Trend Analysis
- **Daily trend tracking**: Click patterns throughout the day
- **Weekly performance cycles**: Day-of-week performance variations
- **Monthly growth analysis**: Long-term performance trends
- **Seasonal patterns**: Performance variations by time of year
- **Campaign impact analysis**: Link performance during specific campaigns

## Data Quality & Monitoring

### Validation Rules
- **Click count reasonableness**: Validation against expected ranges
- **Traffic source consistency**: Source platform validation
- **Timestamp accuracy**: Extraction time validation
- **Link URL validity**: URL format and accessibility checks
- **Data completeness**: Required field presence verification

### Quality Metrics
```python
# Quality assessment framework
class LinktreeDataQuality:
    def assess_data_quality(self, data):
        quality_scores = {
            'completeness': self.check_completeness(data),
            'validity': self.check_data_validity(data),
            'consistency': self.check_temporal_consistency(data),
            'accuracy': self.check_click_accuracy(data)
        }
        
        overall_score = sum(quality_scores.values()) / len(quality_scores)
        return overall_score, quality_scores
```

## Integration Points

### Social Media Analytics Integration
- **Cross-platform correlation**: Link clicks vs social media engagement
- **Campaign attribution**: Social media campaign to Linktree performance
- **Audience overlap analysis**: Shared audience across platforms
- **Content performance correlation**: Social content to link click correlation

### Marketing Campaign Integration
- **UTM parameter tracking**: Campaign-specific performance measurement
- **A/B testing support**: Link performance testing and optimization
- **Conversion funnel analysis**: Complete customer journey tracking
- **ROI calculation**: Marketing spend to link performance attribution

### Dashboard Integration
- **Real-time metrics**: Live click tracking and performance monitoring
- **Performance alerts**: Notification for significant performance changes
- **Comparative analysis**: Historical performance comparison
- **Geographic insights**: Location-based performance visualization

## Troubleshooting

### Common Issues

#### Authentication Problems
```bash
# Check session validity
python src/linktree/utils/check_session.py

# Refresh authentication
python src/linktree/extractors/session_manager.py --refresh
```

#### Data Extraction Failures
```bash
# Validate page structure
python src/linktree/utils/validate_page_structure.py

# Debug extraction process
python src/linktree/extractors/linktree_analytics_extractor.py --debug
```

#### Processing Errors
```bash
# Validate extracted data
python src/linktree/utils/validate_analytics_data.py

# Test processing pipeline
python src/linktree/cleaners/linktree_raw2staging.py --test-mode
```

## Future Enhancements

### Planned Improvements
- **Real-time analytics**: Live click tracking and instant insights
- **Advanced attribution**: Multi-touch attribution across platforms
- **Predictive analytics**: Click performance forecasting
- **A/B testing automation**: Automated link optimization testing

### Integration Enhancements
- **API integration**: Direct Linktree API access when available
- **Webhook support**: Real-time event processing
- **Advanced segmentation**: Detailed audience analysis and segmentation
- **Cross-platform optimization**: Automated link placement optimization

## Related Documentation
- See `data_lake/docs/linktree_integration.md` for detailed setup guide
- Reference `data_lake/schemas/linktree/` for complete schema documentation
- Check `data_lake/tests/linktree/` for test suite and validation
- Review `data_lake/examples/linktree/` for usage examples and best practices
