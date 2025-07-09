# TooLost ETL Pipeline

## Overview
The TooLost ETL pipeline provides comprehensive automation for extracting and processing streaming analytics and sales data from the TooLost platform. This pipeline captures detailed Spotify and Apple Music performance metrics, revenue tracking, and audience insights, delivering critical intelligence for streaming strategy optimization and revenue management.

## Architecture & Components

### Directory Structure
```
toolost/
├── extractors/
│   ├── toolost_extractor.py             # Main TooLost platform extractor
│   ├── spotify_analytics_extractor.py   # Spotify-specific metrics
│   ├── apple_music_extractor.py         # Apple Music analytics
│   └── sales_notifications_extractor.py # Revenue and payout data
├── cleaners/
│   ├── toolost_landing2raw.py           # Landing to raw validation
│   ├── toolost_raw2staging.py           # Raw to staging transformation
│   └── toolost_staging2curated.py       # Staging to curated analytics
├── cookies/
│   ├── toolost_session.json             # Platform authentication state
│   └── browser_context.json            # Browser session preservation
├── schemas/
│   ├── analytics_schema.json            # TooLost analytics data structure
│   ├── spotify_metrics_schema.json      # Spotify-specific schema
│   └── sales_data_schema.json           # Sales and revenue schema
└── utils/
    ├── validate_toolost_json.py         # JSON validation utilities
    └── data_quality_checker.py         # Quality assurance tools
```

## Data Sources & Metrics

### Spotify Analytics
- **Streaming metrics**: Daily, weekly, monthly stream counts
- **Revenue tracking**: Streaming royalties and payout calculations
- **Geographic performance**: Country and region-level streaming data
- **Playlist analytics**: Playlist additions, removals, and performance impact
- **Discovery metrics**: How listeners find tracks (search, radio, playlists)
- **Audience insights**: Listener demographics and behavior patterns

### Apple Music Analytics
- **Streaming performance**: Play counts and completion rates
- **Revenue data**: Apple Music royalty calculations
- **Geographic distribution**: Regional performance and market penetration
- **Chart performance**: Chart positions and ranking trends
- **Shazam integration**: Shazam discovery and identification metrics
- **Radio play tracking**: Apple Music radio and station play counts

### Sales & Revenue Tracking
- **Payout notifications**: Revenue alerts and payment tracking
- **Sales reports**: Digital sales across all platforms
- **Royalty calculations**: Detailed breakdown of revenue sources
- **Performance rights**: PRO (Performance Rights Organization) collections
- **Sync licensing**: Synchronization license revenue tracking
- **Merchandise sales**: Physical and digital merchandise performance

### Platform Analytics Dashboard
- **Cross-platform summaries**: Unified view of all streaming platforms
- **Performance comparisons**: Platform-to-platform performance analysis
- **Growth tracking**: Follower and audience growth across platforms
- **Release performance**: New release tracking and impact analysis

## Extraction Process

### Enhanced Automated Extraction
```python
# Main extraction workflow (2025-06-05 refactor)
from src.toolost.extractors.toolost_extractor import TooLostExtractor

# Initialize with improved flow management
extractor = TooLostExtractor(
    extract_spotify=True,
    extract_apple_music=True,
    extract_sales_notifications=True,
    robust_2fa_handling=True
)

# Execute optimized extraction sequence
results = await extractor.extract_all_analytics()

# Enhanced extraction includes:
# - Complete analytics extraction before sales navigation
# - Robust login and 2FA handling
# - Modular extraction for future platform additions
# - Correct PROJECT_ROOT and zone conventions
```

### Authentication & Session Management
- **Persistent login**: Long-term session maintenance across extractions
- **2FA automation**: Automated two-factor authentication handling
- **Session validation**: Pre-extraction authentication verification
- **Cookie management**: Secure cookie storage and rotation
- **Multi-platform authentication**: Unified login for all TooLost services

### Improved Extraction Flow (2025-06-05 Update)
- **Sequential completion**: Analytics extraction fully completed before sales navigation
- **Robust error handling**: Enhanced resilience to login and page load issues
- **Modular architecture**: Standardized patterns for future platform integrations
- **Path standardization**: All outputs use PROJECT_ROOT environment variable

## Data Processing Pipeline

### Landing to Raw Zone
```python
# Enhanced validation with JSON schema compliance
python src/toolost/cleaners/toolost_landing2raw.py

# Validation improvements:
# - JSON schema validation against predefined structures
# - API response completeness verification
# - Data freshness and currency validation
# - Platform consistency verification across Spotify/Apple data
```

### Raw to Staging Zone
```python
# Advanced data cleaning and standardization
python src/toolost/cleaners/toolost_raw2staging.py

# Enhanced transformations:
# - Platform-specific metric extraction and normalization
# - Cross-platform data harmonization
# - Revenue calculation standardization
# - Geographic data normalization
# - Artist and track metadata enrichment
```

### Staging to Curated Zone
```python
# Business intelligence and analytics preparation
python src/toolost/cleaners/toolost_staging2curated.py

# Advanced business logic:
# - Performance scoring and ranking algorithms
# - Revenue attribution and forecasting
# - Cross-platform performance correlation
# - Audience growth and engagement analysis
# - Market penetration and opportunity identification
```

## Output Datasets

### Daily Streaming Data
**File**: `curated/streaming/daily_streams_toolost.csv`

**Schema**:
```csv
date,artist_name,track_name,platform,streams,revenue_usd,country,playlist_adds,discovery_source
2024-05-22,Artist Name,Track Title,spotify,2145,4.89,US,23,discover_weekly
```

### Revenue Analytics
**File**: `curated/financial/toolost_revenue_monthly.csv`

**Schema**:
```csv
month,platform,total_streams,gross_revenue_usd,net_revenue_usd,avg_payout_per_stream,top_country
2024-05,spotify,45230,125.67,101.34,0.00224,US
```

### Cross-Platform Performance Summary
**File**: `curated/analytics/toolost_platform_comparison.parquet`

**Metrics**:
- Platform-specific performance rankings
- Revenue per stream comparisons
- Geographic performance distribution
- Audience overlap analysis
- Growth rate comparisons

## Configuration & Environment

### Environment Variables
```bash
# Core configuration
PROJECT_ROOT=/path/to/data_lake
TOOLOST_USERNAME=your_username
TOOLOST_PASSWORD=your_password
TOOLOST_2FA_SECRET=your_2fa_secret

# Extraction settings
TL_EXTRACTION_FREQUENCY_HOURS=24
TL_EXTRACT_SPOTIFY=true
TL_EXTRACT_APPLE_MUSIC=true
TL_EXTRACT_SALES_NOTIFICATIONS=true
TL_HEADLESS_MODE=true

# Processing configuration
TL_REVENUE_CALCULATION=true
TL_CROSS_PLATFORM_ANALYSIS=true
TL_GEOGRAPHIC_ANALYSIS=true
```

### Dependencies
```bash
# Core requirements
playwright>=1.30.0
pandas>=1.5.0
numpy>=1.21.0
requests>=2.28.0
beautifulsoup4>=4.11.0
jsonschema>=4.0.0

# Additional utilities
pyotp>=2.6.0  # For 2FA handling
cryptography>=3.4.0  # For secure credential storage
```

## Usage Examples

### Complete Pipeline Execution
```bash
# Full TooLost extraction and processing
cd "C:\Users\Earth\BEDROT PRODUCTIONS\bedrot-data-ecosystem\data_lake"

python src/toolost/extractors/toolost_extractor.py
python src/toolost/cleaners/toolost_landing2raw.py
python src/toolost/cleaners/toolost_raw2staging.py
python src/toolost/cleaners/toolost_staging2curated.py
```

### Advanced Analytics Processing
```python
# Custom analytics and insights generation
import pandas as pd
from src.toolost.utils.analytics_processor import TooLostAnalyzer

# Initialize analyzer
analyzer = TooLostAnalyzer()
streaming_data = analyzer.load_streaming_data(platforms=['spotify', 'apple_music'])

# Generate comprehensive insights
revenue_analysis = analyzer.analyze_revenue_trends(streaming_data)
platform_comparison = analyzer.compare_platform_performance(streaming_data)
market_opportunities = analyzer.identify_growth_opportunities(streaming_data)

# Export detailed reports
analyzer.export_comprehensive_report({
    'revenue_trends': revenue_analysis,
    'platform_performance': platform_comparison,
    'growth_opportunities': market_opportunities
}, 'toolost_insights_comprehensive.xlsx')
```

## Analytics & Insights

### Key Performance Indicators
- **Revenue per stream**: Platform-specific monetization efficiency
- **Stream velocity**: Rate of stream accumulation for new releases
- **Platform market share**: Distribution of streams across platforms
- **Geographic penetration**: Market coverage and opportunity identification
- **Audience growth rate**: Monthly active listener growth

### Advanced Analytics
```python
# Revenue optimization analysis
def calculate_revenue_optimization_score(platform_data):
    """Calculate potential revenue optimization opportunities"""
    scores = {}
    for platform in platform_data['platform'].unique():
        platform_subset = platform_data[platform_data['platform'] == platform]
        
        # Calculate metrics
        avg_revenue_per_stream = platform_subset['revenue_usd'].sum() / platform_subset['streams'].sum()
        geographic_diversity = platform_subset['country'].nunique()
        growth_rate = calculate_growth_rate(platform_subset['streams'])
        
        # Composite optimization score
        scores[platform] = {
            'revenue_efficiency': avg_revenue_per_stream,
            'market_diversity': geographic_diversity,
            'growth_momentum': growth_rate,
            'optimization_potential': calculate_optimization_potential(platform_subset)
        }
    
    return scores

# Cross-platform correlation analysis
def analyze_cross_platform_synergies(spotify_data, apple_music_data):
    """Identify cross-platform performance correlations"""
    merged_data = pd.merge(spotify_data, apple_music_data, on=['date', 'track_name'], suffixes=('_spotify', '_apple'))
    
    correlation_metrics = {
        'stream_correlation': merged_data['streams_spotify'].corr(merged_data['streams_apple']),
        'revenue_correlation': merged_data['revenue_usd_spotify'].corr(merged_data['revenue_usd_apple']),
        'geographic_overlap': calculate_geographic_overlap(merged_data),
        'release_impact_correlation': calculate_release_impact_correlation(merged_data)
    }
    
    return correlation_metrics
```

## Data Quality & Monitoring

### Enhanced Validation (2025-05-22 Update)
- **JSON schema compliance**: Validation against predefined TooLost data structures
- **API response completeness**: Verification of all expected data fields
- **Data freshness validation**: Currency and timeliness checks
- **Platform consistency**: Cross-validation between Spotify and Apple Music data

### Quality Metrics
```python
# Comprehensive quality assessment
class TooLostDataQuality:
    def assess_streaming_data_quality(self, data):
        quality_dimensions = {
            'completeness': self.check_data_completeness(data),
            'accuracy': self.validate_revenue_calculations(data),
            'consistency': self.check_cross_platform_consistency(data),
            'timeliness': self.validate_data_freshness(data),
            'validity': self.check_business_rule_compliance(data)
        }
        
        # Calculate weighted quality score
        weights = {'completeness': 0.25, 'accuracy': 0.30, 'consistency': 0.20, 'timeliness': 0.15, 'validity': 0.10}
        overall_score = sum(score * weights[dimension] for dimension, score in quality_dimensions.items())
        
        return overall_score, quality_dimensions
```

## Integration Points

### Cross-Platform Analytics Integration
- **Unified streaming dashboard**: Combined TooLost data with other platform analytics
- **Revenue correlation**: TooLost revenue vs other platform performance
- **Audience overlap analysis**: Shared audience across streaming platforms
- **Marketing attribution**: Campaign impact on TooLost-tracked platforms

### Financial System Integration
- **Revenue forecasting**: Predictive modeling based on TooLost data
- **Payout reconciliation**: Automated verification of platform payouts
- **Tax reporting**: Revenue data formatted for financial and tax reporting
- **ROI calculation**: Marketing spend vs streaming revenue attribution

### Content Strategy Integration
- **Release optimization**: Data-driven release timing and platform strategy
- **Performance prediction**: ML models for predicting track performance
- **Market analysis**: Geographic and demographic insights for content strategy
- **Playlist strategy**: Playlist placement optimization based on performance data

## Troubleshooting

### Common Issues

#### Authentication and Session Problems
```bash
# Validate TooLost authentication
python src/toolost/utils/validate_authentication.py

# Refresh authentication cookies
python src/toolost/extractors/session_manager.py --refresh-session

# Test 2FA functionality
python src/toolost/utils/test_2fa_handling.py
```

#### Data Extraction Failures
```bash
# Check TooLost platform availability
python src/toolost/utils/check_platform_status.py

# Debug extraction with detailed logging
python src/toolost/extractors/toolost_extractor.py --debug --verbose

# Validate page structure and selectors
python src/toolost/utils/validate_page_structure.py
```

#### Data Processing Errors
```bash
# Validate extracted JSON data
python src/toolost/utils/validate_toolost_json.py

# Test data transformation pipeline
python src/toolost/cleaners/toolost_raw2staging.py --test-mode

# Check schema compliance
python src/toolost/utils/schema_compliance_checker.py
```

## Recent Enhancements (2025-05-22 & 2025-06-05)

### 2025-05-22: Reliability Improvements
- Enhanced TooLost analytics scraper for reliable Spotify and Apple Music data extraction
- Improved manual intervention reduction through automated error recovery
- Enhanced data completeness in raw data zone

### 2025-06-05: Extraction Flow Refactor
- **Optimized extraction sequence**: Analytics extraction now always completes before sales navigation
- **Enhanced robustness**: All Playwright-based extractors handle login/2FA gracefully
- **Modular architecture**: Standardized extraction patterns for future platform additions
- **Path management**: All outputs use PROJECT_ROOT for robust, portable path management

## Future Enhancements

### Planned Improvements
- **Real-time analytics**: Live streaming data and instant performance insights
- **Advanced revenue modeling**: Predictive revenue forecasting and optimization
- **Multi-account support**: Support for multiple TooLost accounts and artist profiles
- **API integration**: Direct TooLost API access when available

### Integration Enhancements
- **Advanced cross-platform analytics**: Deeper integration with other streaming platforms
- **Machine learning insights**: AI-driven performance prediction and optimization
- **Automated reporting**: Intelligent report generation and distribution
- **Market intelligence**: Competitive analysis and industry benchmarking

## Related Documentation
- See `data_lake/docs/toolost_integration.md` for detailed setup and configuration guide
- Reference `data_lake/schemas/toolost/` for complete schema documentation and validation rules
- Check `data_lake/tests/toolost/` for comprehensive test suite and validation procedures
- Review `data_lake/examples/toolost/` for usage examples, best practices, and advanced analytics
