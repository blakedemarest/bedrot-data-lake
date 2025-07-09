# TikTok ETL Pipeline

## Overview
The TikTok ETL pipeline provides comprehensive automation for extracting, processing, and analyzing TikTok Creator Studio analytics data. This pipeline captures video performance metrics, audience insights, trending data, and engagement analytics to support content strategy optimization and performance tracking for BEDROT's TikTok presence.

## Architecture & Components

### Directory Structure
```
tiktok/
├── extractors/
│   ├── tiktok_analytics_extractor.py   # Main Creator Studio extraction
│   ├── video_performance_extractor.py  # Individual video metrics
│   ├── audience_insights_extractor.py  # Audience demographics and behavior
│   └── trending_data_extractor.py      # Hashtag and sound trends
├── cleaners/
│   ├── tiktok_landing2raw.py           # Landing to raw validation
│   ├── tiktok_raw2staging.py           # Raw to staging transformation
│   └── tiktok_staging2curated.py       # Staging to curated analytics
├── cookies/
│   ├── tiktok_creator_session.json     # Creator Studio authentication
│   ├── mobile_session.json             # Mobile app session backup
│   └── session_metadata.json           # Session management metadata
└── schemas/
    ├── video_analytics_schema.json     # Video performance data structure
    ├── audience_schema.json            # Audience insights schema
    └── trending_data_schema.json       # Trending content schema
```

## Data Sources & Metrics

### Video Performance Analytics
- **View metrics**: Total views, unique views, average watch time
- **Engagement metrics**: Likes, comments, shares, completion rates
- **Discovery metrics**: Impressions, reach, profile views from videos
- **Traffic sources**: For You Page, Following, Hashtags, Sounds, Search
- **Geographic data**: Video performance by country and region
- **Temporal analysis**: Performance over time, peak viewing hours

### Audience Insights
- **Demographics**: Age distribution, gender breakdown, location data
- **Activity patterns**: When followers are most active
- **Content preferences**: Top videos among different audience segments
- **Growth metrics**: Follower growth rate, audience retention
- **Engagement behavior**: Comment patterns, share behavior, interaction rates

### Content Performance Data
- **Individual video analytics**: Per-video detailed performance metrics
- **Content category analysis**: Performance by content type/theme
- **Hashtag performance**: Hashtag reach and engagement effectiveness
- **Sound performance**: Audio track usage and viral potential
- **Trending analysis**: Content alignment with platform trends

### Creator Studio Metrics
- **Overall account performance**: Account-level analytics and trends
- **Video publishing analytics**: Optimal posting times and frequency
- **Creator Fund metrics**: Monetization and revenue data
- **Live streaming analytics**: Live video performance and engagement
- **Cross-promotion effectiveness**: Link clicks and external traffic

## Extraction Process

### Automated Data Collection
```python
# Main extraction workflow
from src.tiktok.extractors.tiktok_analytics_extractor import TikTokExtractor

# Initialize extractor with account configuration
extractor = TikTokExtractor(
    account_username='bedrotproductions',
    extract_historical=True,
    days_back=30,
    include_audience_insights=True
)

# Execute comprehensive extraction
analytics_data = await extractor.extract_all_analytics()

# Extracted data includes:
# - Video performance metrics
# - Audience demographic data
# - Trending hashtag and sound data
# - Creator Studio insights
```

### Authentication & Session Management
- **Creator Studio access**: Full analytics dashboard privileges
- **Multi-factor authentication**: Automated 2FA handling
- **Session persistence**: Long-term session maintenance
- **Cookie management**: Secure storage and rotation of authentication cookies
- **Account switching**: Support for multiple TikTok accounts

### Data Extraction Methods
- **API interception**: Capture Creator Studio API calls
- **Dashboard scraping**: Extract visual analytics data
- **Bulk export utilization**: Use built-in export functionality where available
- **Real-time monitoring**: Continuous tracking of new content performance

## Data Processing Pipeline

### Landing to Raw Zone
```python
# Validation and quality assurance
python src/tiktok/cleaners/tiktok_landing2raw.py

# Validation steps:
# - JSON structure validation
# - Creator Studio data completeness
# - Video ID consistency checks
# - Timestamp and date validation
# - Metric range validation
```

### Raw to Staging Zone
```python
# Data cleaning and standardization
python src/tiktok/cleaners/tiktok_raw2staging.py

# Transformations:
# - Video metadata normalization
# - Engagement rate calculations
# - Geographic data standardization
# - Hashtag and mention extraction
# - Time zone standardization
```

### Staging to Curated Zone
```python
# Analytics preparation and business logic
python src/tiktok/cleaners/tiktok_staging2curated.py

# Business transformations:
# - Performance scoring algorithms
# - Trend analysis calculations
# - Audience segmentation
# - Content optimization insights
# - Cross-platform performance correlation
```

## Output Datasets

### Daily Video Performance
**File**: `curated/social_media/tiktok/video_performance_daily.csv`

**Schema**:
```csv
date,video_id,video_title,views,likes,comments,shares,completion_rate,engagement_rate,hashtags,sounds
2024-05-22,7234567890123456789,Latest Track Preview,15420,1234,89,234,0.67,0.089,#newmusic #bedrot,original_sound_123
```

### Audience Analytics
**File**: `curated/social_media/tiktok/audience_insights_weekly.parquet`

**Schema**:
```csv
week,age_group,gender,country,percentage,engagement_rate,growth_rate,activity_peak_hour
2024-W21,18-24,female,US,35.2,0.067,0.045,20:00
```

### Content Performance Summary
**File**: `curated/social_media/tiktok/content_performance_monthly.csv`

**Metrics**:
- Monthly view totals and trends
- Top performing content categories
- Hashtag performance analysis
- Audience growth and engagement trends
- Cross-platform traffic attribution

## Configuration & Environment

### Environment Variables
```bash
# Core configuration
PROJECT_ROOT=/path/to/data_lake
TIKTOK_USERNAME=your_username
TIKTOK_PASSWORD=your_password
TIKTOK_ACCOUNT_ID=your_account_id

# Extraction settings
TT_EXTRACTION_FREQUENCY_HOURS=24
TT_HISTORICAL_DAYS=30
TT_INCLUDE_DRAFTS=false
TT_EXTRACT_AUDIENCE_INSIGHTS=true

# Processing configuration
TT_ENGAGEMENT_CALCULATION=true
TT_HASHTAG_ANALYSIS=true
TT_TRENDING_DETECTION=true
```

### Dependencies
```bash
# Required packages
playwright>=1.30.0
pandas>=1.5.0
numpy>=1.21.0
requests>=2.28.0
beautifulsoup4>=4.11.0
dateutil>=2.8.0
```

## Usage Examples

### Complete Pipeline Execution
```bash
# Full TikTok analytics extraction and processing
cd "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake"

python src/tiktok/extractors/tiktok_analytics_extractor.py
python src/tiktok/cleaners/tiktok_landing2raw.py
python src/tiktok/cleaners/tiktok_raw2staging.py
python src/tiktok/cleaners/tiktok_staging2curated.py
```

### Custom Analytics Processing
```python
# Advanced analytics example
import pandas as pd
from src.tiktok.utils.analytics_processor import TikTokAnalyzer

# Initialize analyzer
analyzer = TikTokAnalyzer()
video_data = analyzer.load_video_performance(date_range='last_30_days')

# Generate insights
viral_potential = analyzer.calculate_viral_potential(video_data)
optimal_posting = analyzer.find_optimal_posting_times(video_data)
content_recommendations = analyzer.generate_content_recommendations(video_data)

# Export analysis
analyzer.export_insights({
    'viral_potential': viral_potential,
    'posting_optimization': optimal_posting,
    'content_strategy': content_recommendations
}, 'tiktok_insights_report.xlsx')
```

## Analytics & Insights

### Key Performance Indicators
- **View velocity**: Rate of view accumulation in first 24 hours
- **Engagement rate**: (Likes + Comments + Shares) / Views
- **Completion rate**: Percentage of video watched to end
- **Share rate**: Shares per view ratio
- **Profile visit rate**: Profile visits generated per video view

### Performance Analysis
```python
# Performance calculation examples
def calculate_viral_score(views, engagement_rate, completion_rate, time_since_post):
    """Calculate viral potential score"""
    velocity_score = views / max(time_since_post, 1)  # Views per hour
    engagement_weight = engagement_rate * 100
    completion_weight = completion_rate * 50
    
    return (velocity_score * 0.4) + (engagement_weight * 0.35) + (completion_weight * 0.25)

def analyze_content_performance_by_category(video_data):
    """Analyze performance by content type"""
    return video_data.groupby('content_category').agg({
        'views': ['mean', 'median', 'sum'],
        'engagement_rate': 'mean',
        'completion_rate': 'mean',
        'viral_score': 'mean'
    }).round(4)
```

### Trend Analysis
- **Hashtag trend tracking**: Performance of specific hashtags over time
- **Sound trend analysis**: Viral sound identification and usage optimization
- **Content category trends**: Which content types are gaining traction
- **Audience behavior trends**: Changes in viewing patterns and preferences
- **Cross-platform correlation**: TikTok performance impact on other platforms

## Data Quality & Monitoring

### Validation Rules
- **View count reasonableness**: Validation against historical patterns
- **Engagement rate bounds**: Realistic engagement rate validation
- **Video metadata completeness**: Required field presence checks
- **Timestamp consistency**: Posting time and analytics time alignment
- **Creator Studio data integrity**: Cross-validation of related metrics

### Quality Metrics
```python
# Quality assessment framework
class TikTokDataQuality:
    def assess_analytics_quality(self, data):
        quality_checks = {
            'completeness': self.check_data_completeness(data),
            'consistency': self.check_metric_consistency(data),
            'validity': self.check_value_ranges(data),
            'freshness': self.check_data_freshness(data),
            'accuracy': self.cross_validate_metrics(data)
        }
        
        overall_score = sum(quality_checks.values()) / len(quality_checks)
        return overall_score, quality_checks
```

## Integration Points

### Cross-Platform Analytics
- **Content correlation**: TikTok video performance vs other platform engagement
- **Audience overlap**: Shared followers across TikTok and other platforms
- **Traffic attribution**: TikTok-driven traffic to streaming platforms
- **Campaign integration**: TikTok content as part of broader marketing campaigns

### Content Strategy Integration
- **Performance prediction**: ML models for predicting video performance
- **Optimal timing**: Data-driven posting schedule optimization
- **Content recommendations**: Trend-based content suggestions
- **Hashtag optimization**: Data-driven hashtag strategy

### Dashboard Integration
- **Real-time performance tracking**: Live video performance monitoring
- **Trend alerts**: Notifications for viral content and trending opportunities
- **Performance comparisons**: Historical and peer comparison analytics
- **Content planning**: Data-driven content calendar integration

## Troubleshooting

### Common Issues

#### Authentication Problems
```bash
# Check Creator Studio access
python src/tiktok/utils/check_creator_access.py

# Refresh authentication cookies
python src/tiktok/extractors/session_manager.py --refresh-cookies

# Validate 2FA setup
python src/tiktok/utils/validate_2fa.py
```

#### Data Extraction Failures
```bash
# Validate Creator Studio page structure
python src/tiktok/utils/validate_creator_studio.py

# Debug extraction with screenshots
python src/tiktok/extractors/tiktok_analytics_extractor.py --debug --screenshots

# Test API endpoint availability
python src/tiktok/utils/test_api_endpoints.py
```

#### Processing Errors
```bash
# Validate extracted analytics data
python src/tiktok/utils/validate_analytics_data.py

# Test data transformation pipeline
python src/tiktok/cleaners/tiktok_raw2staging.py --test-mode

# Check schema compliance
python src/tiktok/utils/schema_validator.py
```

## Future Enhancements

### Planned Improvements
- **Real-time analytics**: Live performance tracking and instant insights
- **Advanced trend prediction**: ML-based viral content prediction
- **Automated content optimization**: AI-driven hashtag and timing recommendations
- **Creator collaboration analytics**: Performance impact of collaborations

### Integration Enhancements
- **TikTok for Business API**: Direct API integration when available
- **Advanced audience segmentation**: Detailed audience analysis and targeting
- **Cross-platform content optimization**: Unified content strategy across platforms
- **Influencer network analysis**: Collaboration opportunity identification

## Related Documentation
- See `data_lake/docs/tiktok_integration.md` for detailed setup and configuration
- Reference `data_lake/schemas/tiktok/` for complete schema documentation
- Check `data_lake/tests/tiktok/` for comprehensive test suite
- Review `data_lake/examples/tiktok/` for usage examples and best practices
