# Data Patterns Directory

## Purpose
This directory serves as the authoritative repository for recurring data patterns, schemas, transformations, and design solutions used throughout the BEDROT Data Lake ecosystem. It provides standardized templates, best practices, and reference implementations that ensure consistency, maintainability, and scalability across all data processing workflows.

## What Goes Here
- **Data schemas and models**: Standardized data structures for different domains and platforms
- **Transformation patterns**: Reusable data processing and cleaning approaches
- **Integration patterns**: Standard approaches for connecting different systems and APIs
- **Quality assurance patterns**: Consistent validation and monitoring approaches
- **Performance optimization patterns**: Proven techniques for improving processing efficiency
- **Error handling patterns**: Standardized approaches for managing failures and recovery
- **Security patterns**: Data protection and privacy preservation techniques
- **Design patterns**: Architectural solutions for common data engineering challenges

## Pattern Categories

### Schema Patterns
- **Platform-specific schemas**: Standardized structures for each data source (Spotify, TikTok, Meta Ads)
- **Cross-platform harmonization**: Unified schemas for multi-platform analytics
- **Temporal schemas**: Time-series and event-based data structures
- **Hierarchical schemas**: Nested and relational data organization patterns
- **Evolution patterns**: Schema versioning and migration approaches

### Transformation Patterns
- **Data cleaning patterns**: Standardized approaches for data quality improvement
- **Normalization patterns**: Consistent data standardization techniques
- **Aggregation patterns**: Common summarization and roll-up approaches
- **Enrichment patterns**: Data enhancement and augmentation techniques
- **Validation patterns**: Quality checking and constraint enforcement

### Integration Patterns
- **API integration patterns**: Standardized approaches for external API consumption
- **Web scraping patterns**: Consistent browser automation and data extraction
- **Database integration patterns**: Efficient data loading and synchronization
- **Real-time processing patterns**: Stream processing and event-driven architectures
- **Batch processing patterns**: Efficient bulk data processing approaches

## Directory Structure
```
patterns/
├── schemas/
│   ├── streaming/
│   │   ├── streaming_data_v2.json
│   │   ├── artist_performance_schema.json
│   │   └── platform_metrics_unified.json
│   ├── marketing/
│   │   ├── campaign_data_schema.json
│   │   ├── ad_performance_schema.json
│   │   └── audience_insights_schema.json
│   ├── social_media/
│   │   ├── engagement_metrics_schema.json
│   │   ├── content_performance_schema.json
│   │   └── audience_demographics_schema.json
│   └── financial/
│       ├── revenue_tracking_schema.json
│       ├── payout_reconciliation_schema.json
│       └── cost_analysis_schema.json
├── transformations/
│   ├── data_cleaning/
│   │   ├── artist_name_normalization.md
│   │   ├── date_standardization.md
│   │   ├── currency_conversion.md
│   │   └── text_processing_patterns.md
│   ├── aggregation/
│   │   ├── time_series_aggregation.md
│   │   ├── cross_platform_rollups.md
│   │   ├── performance_summarization.md
│   │   └── audience_segmentation.md
│   ├── enrichment/
│   │   ├── metadata_augmentation.md
│   │   ├── calculated_metrics.md
│   │   ├── external_data_joining.md
│   │   └── trend_analysis.md
│   └── validation/
│       ├── data_quality_checks.md
│       ├── business_rule_validation.md
│       ├── consistency_verification.md
│       └── completeness_assessment.md
├── integration/
│   ├── api/
│   │   ├── rest_api_patterns.md
│   │   ├── authentication_patterns.md
│   │   ├── rate_limiting_strategies.md
│   │   └── error_handling_patterns.md
│   ├── web_scraping/
│   │   ├── playwright_automation_patterns.md
│   │   ├── cookie_management.md
│   │   ├── dynamic_content_handling.md
│   │   └── anti_detection_strategies.md
│   ├── database/
│   │   ├── sqlite_optimization_patterns.md
│   │   ├── bulk_loading_strategies.md
│   │   ├── incremental_updates.md
│   │   └── query_optimization.md
│   └── file_processing/
│       ├── csv_processing_patterns.md
│       ├── json_parsing_strategies.md
│       ├── large_file_handling.md
│       └── compression_strategies.md
├── quality/
│   ├── validation_rules/
│   │   ├── streaming_data_validation.json
│   │   ├── campaign_data_validation.json
│   │   ├── social_media_validation.json
│   │   └── financial_data_validation.json
│   ├── monitoring/
│   │   ├── data_freshness_monitoring.md
│   │   ├── quality_score_calculation.md
│   │   ├── anomaly_detection_patterns.md
│   │   └── alerting_strategies.md
│   └── testing/
│       ├── unit_testing_patterns.md
│       ├── integration_testing_approaches.md
│       ├── data_validation_testing.md
│       └── performance_testing_strategies.md
├── performance/
│   ├── optimization/
│   │   ├── pandas_optimization_patterns.md
│   │   ├── memory_management_strategies.md
│   │   ├── parallel_processing_patterns.md
│   │   └── caching_strategies.md
│   ├── scalability/
│   │   ├── data_partitioning_strategies.md
│   │   ├── incremental_processing.md
│   │   ├── resource_scaling_patterns.md
│   │   └── load_balancing_approaches.md
│   └── monitoring/
│       ├── performance_metric_collection.md
│       ├── bottleneck_identification.md
│       ├── capacity_planning_patterns.md
│       └── optimization_tracking.md
└── security/
    ├── data_protection/
    │   ├── pii_anonymization_patterns.md
    │   ├── encryption_strategies.md
    │   ├── access_control_patterns.md
    │   └── audit_logging_approaches.md
    ├── authentication/
    │   ├── api_authentication_patterns.md
    │   ├── session_management.md
    │   ├── credential_storage_patterns.md
    │   └── multi_factor_auth_handling.md
    └── compliance/
        ├── gdpr_compliance_patterns.md
        ├── data_retention_strategies.md
        ├── regulatory_reporting_patterns.md
        └── privacy_by_design_approaches.md
```

## Schema Design Patterns

### Universal Schema Template
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Streaming Data Schema v2",
  "type": "object",
  "properties": {
    "metadata": {
      "type": "object",
      "properties": {
        "schema_version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
        "source_platform": {"type": "string", "enum": ["spotify", "apple_music", "youtube", "tiktok"]},
        "extraction_timestamp": {"type": "string", "format": "date-time"},
        "data_freshness_hours": {"type": "number", "minimum": 0, "maximum": 72},
        "record_count": {"type": "integer", "minimum": 0}
      },
      "required": ["schema_version", "source_platform", "extraction_timestamp"]
    },
    "data": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "date": {"type": "string", "format": "date"},
          "artist_id": {"type": "string", "pattern": "^[a-zA-Z0-9_-]+$"},
          "artist_name": {"type": "string", "minLength": 1, "maxLength": 255},
          "track_id": {"type": "string", "pattern": "^[a-zA-Z0-9_-]+$"},
          "track_name": {"type": "string", "minLength": 1, "maxLength": 255},
          "streams": {"type": "integer", "minimum": 0},
          "revenue_usd": {"type": "number", "minimum": 0},
          "country_code": {"type": "string", "pattern": "^[A-Z]{2}$"},
          "platform_specific": {"type": "object"}
        },
        "required": ["date", "artist_name", "track_name", "streams"]
      }
    }
  },
  "required": ["metadata", "data"]
}
```

### Schema Evolution Pattern
```python
# Example: Schema versioning and migration
class SchemaManager:
    def __init__(self, schema_registry_path):
        self.registry_path = schema_registry_path
        self.schemas = self.load_schema_registry()
    
    def register_schema_version(self, schema_name, version, schema_definition):
        """Register a new schema version"""
        if schema_name not in self.schemas:
            self.schemas[schema_name] = {}
        
        # Validate backward compatibility
        if self.schemas[schema_name]:
            latest_version = max(self.schemas[schema_name].keys())
            compatibility_check = self.check_backward_compatibility(
                self.schemas[schema_name][latest_version],
                schema_definition
            )
            
            if not compatibility_check['compatible']:
                raise SchemaIncompatibilityError(
                    f"Schema {schema_name} v{version} breaks compatibility: {compatibility_check['issues']}"
                )
        
        self.schemas[schema_name][version] = {
            'definition': schema_definition,
            'registered_at': datetime.now(),
            'migration_scripts': []
        }
        
        self.save_schema_registry()
    
    def get_migration_path(self, schema_name, from_version, to_version):
        """Get migration path between schema versions"""
        # Implementation for finding migration scripts
        pass
```

## Transformation Pattern Library

### Data Cleaning Patterns

#### Artist Name Normalization
```python
# Standard artist name cleaning pattern
def normalize_artist_name(artist_name):
    """Standardize artist name formatting across platforms"""
    if not artist_name or pd.isna(artist_name):
        return None
    
    # Convert to string and strip whitespace
    name = str(artist_name).strip()
    
    # Remove common platform artifacts
    artifacts_to_remove = [
        ' - Topic',  # YouTube auto-generated channels
        ' (Official)',  # Official channel indicators
        'VEVO',  # VEVO suffix removal
    ]
    
    for artifact in artifacts_to_remove:
        name = name.replace(artifact, '')
    
    # Standardize case (Title Case)
    name = name.title()
    
    # Handle special cases
    special_cases = {
        'Dj ': 'DJ ',
        'Mc ': 'MC ',
        'Ft. ': 'ft. ',
        'Feat. ': 'feat. '
    }
    
    for old, new in special_cases.items():
        name = name.replace(old, new)
    
    # Remove excessive whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name if name else None

# Usage pattern
def apply_artist_normalization(df, artist_column='artist_name'):
    """Apply artist name normalization to DataFrame"""
    df[artist_column] = df[artist_column].apply(normalize_artist_name)
    
    # Log normalization statistics
    normalization_stats = {
        'total_records': len(df),
        'null_names': df[artist_column].isna().sum(),
        'empty_names': (df[artist_column] == '').sum(),
        'normalized_count': len(df[df[artist_column].notna()])
    }
    
    return df, normalization_stats
```

#### Currency Conversion Pattern
```python
# Standard currency conversion pattern
class CurrencyConverter:
    def __init__(self, exchange_rates_source='api'):
        self.rates = self.load_exchange_rates(exchange_rates_source)
        self.rate_cache_ttl = 3600  # 1 hour
        self.last_update = None
    
    def convert_to_usd(self, amount, from_currency, date=None):
        """Convert amount to USD using historical or current rates"""
        if from_currency == 'USD':
            return amount
        
        if date:
            rate = self.get_historical_rate(from_currency, 'USD', date)
        else:
            rate = self.get_current_rate(from_currency, 'USD')
        
        if rate is None:
            raise CurrencyConversionError(f"No rate available for {from_currency} to USD")
        
        return amount * rate
    
    def apply_currency_conversion(self, df, amount_column, currency_column, target_currency='USD'):
        """Apply currency conversion to DataFrame"""
        df['converted_amount'] = df.apply(
            lambda row: self.convert_to_usd(
                row[amount_column], 
                row[currency_column]
            ) if pd.notna(row[amount_column]) and pd.notna(row[currency_column]) else None,
            axis=1
        )
        
        return df
```

### Integration Patterns

#### REST API Integration Pattern
```python
# Standard REST API integration pattern
class APIIntegrator:
    def __init__(self, base_url, auth_config, rate_limit_config):
        self.base_url = base_url
        self.auth = self.setup_authentication(auth_config)
        self.rate_limiter = RateLimiter(**rate_limit_config)
        self.session = requests.Session()
        self.retry_strategy = self.setup_retry_strategy()
    
    def make_request(self, endpoint, method='GET', params=None, data=None):
        """Make rate-limited, authenticated API request with retry logic"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()
        
        # Prepare request
        request_kwargs = {
            'method': method,
            'url': url,
            'params': params,
            'json': data,
            'auth': self.auth,
            'timeout': 30
        }
        
        # Execute with retry logic
        try:
            response = self.session.request(**request_kwargs)
            response.raise_for_status()
            
            # Update rate limiter
            self.rate_limiter.record_request(response)
            
            return response.json()
        
        except requests.exceptions.RequestException as e:
            self.handle_request_error(e, request_kwargs)
            raise
    
    def paginated_request(self, endpoint, page_size=100, max_pages=None):
        """Handle paginated API responses"""
        page = 1
        all_data = []
        
        while True:
            params = {'page': page, 'page_size': page_size}
            response_data = self.make_request(endpoint, params=params)
            
            # Extract data (adapt based on API response structure)
            page_data = response_data.get('data', [])
            all_data.extend(page_data)
            
            # Check for more pages
            if (not page_data or 
                len(page_data) < page_size or 
                (max_pages and page >= max_pages)):
                break
            
            page += 1
        
        return all_data
```

#### Web Scraping Pattern
```python
# Standard Playwright web scraping pattern
class WebScrapingPattern:
    def __init__(self, browser_config):
        self.browser_config = browser_config
        self.playwright = None
        self.browser = None
        self.context = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(**self.browser_config)
        self.context = await self.browser.new_context()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def scrape_with_authentication(self, login_url, credentials, target_url):
        """Scrape data requiring authentication"""
        page = await self.context.new_page()
        
        try:
            # Load cookies if available
            cookies = self.load_saved_cookies()
            if cookies:
                await self.context.add_cookies(cookies)
            
            # Navigate to target URL
            await page.goto(target_url)
            
            # Check if authentication is needed
            if await self.is_login_required(page):
                await self.perform_login(page, login_url, credentials)
                await page.goto(target_url)
            
            # Wait for content to load
            await page.wait_for_load_state('networkidle')
            
            # Extract data
            data = await self.extract_data(page)
            
            # Save cookies for future use
            cookies = await self.context.cookies()
            self.save_cookies(cookies)
            
            return data
        
        finally:
            await page.close()
    
    async def extract_data(self, page):
        """Extract data from page - to be implemented by specific scrapers"""
        raise NotImplementedError("Subclasses must implement extract_data method")
```

## Quality Assurance Patterns

### Data Validation Pattern
```python
# Standard data validation pattern
class DataValidator:
    def __init__(self, validation_rules):
        self.rules = validation_rules
        self.validation_results = []
    
    def validate_dataset(self, df, dataset_name):
        """Comprehensive dataset validation"""
        validation_results = {
            'dataset': dataset_name,
            'timestamp': datetime.now(),
            'total_records': len(df),
            'checks': []
        }
        
        # Schema validation
        schema_check = self.validate_schema(df)
        validation_results['checks'].append(schema_check)
        
        # Data quality checks
        quality_checks = [
            self.check_completeness(df),
            self.check_validity(df),
            self.check_consistency(df),
            self.check_uniqueness(df),
            self.check_business_rules(df)
        ]
        
        validation_results['checks'].extend(quality_checks)
        
        # Calculate overall score
        validation_results['overall_score'] = self.calculate_quality_score(validation_results['checks'])
        
        return validation_results
    
    def check_completeness(self, df):
        """Check data completeness"""
        required_columns = self.rules.get('required_columns', [])
        completeness_results = []
        
        for column in required_columns:
            if column in df.columns:
                null_count = df[column].isna().sum()
                completeness_rate = 1 - (null_count / len(df))
                
                completeness_results.append({
                    'column': column,
                    'completeness_rate': completeness_rate,
                    'status': 'PASS' if completeness_rate >= 0.95 else 'FAIL'
                })
        
        return {
            'check_type': 'completeness',
            'results': completeness_results,
            'overall_status': 'PASS' if all(r['status'] == 'PASS' for r in completeness_results) else 'FAIL'
        }
```

## Performance Optimization Patterns

### Pandas Optimization Pattern
```python
# Standard pandas optimization patterns
class PandasOptimizer:
    @staticmethod
    def optimize_dtypes(df):
        """Optimize DataFrame data types for memory efficiency"""
        optimized_df = df.copy()
        
        for column in optimized_df.columns:
            col_type = optimized_df[column].dtype
            
            # Optimize integer columns
            if col_type == 'int64':
                col_min = optimized_df[column].min()
                col_max = optimized_df[column].max()
                
                if col_min >= np.iinfo(np.int8).min and col_max <= np.iinfo(np.int8).max:
                    optimized_df[column] = optimized_df[column].astype(np.int8)
                elif col_min >= np.iinfo(np.int16).min and col_max <= np.iinfo(np.int16).max:
                    optimized_df[column] = optimized_df[column].astype(np.int16)
                elif col_min >= np.iinfo(np.int32).min and col_max <= np.iinfo(np.int32).max:
                    optimized_df[column] = optimized_df[column].astype(np.int32)
            
            # Optimize float columns
            elif col_type == 'float64':
                optimized_df[column] = optimized_df[column].astype(np.float32)
            
            # Optimize object columns (strings)
            elif col_type == 'object':
                if optimized_df[column].nunique() / len(optimized_df) < 0.5:
                    optimized_df[column] = optimized_df[column].astype('category')
        
        return optimized_df
    
    @staticmethod
    def chunked_processing(file_path, chunk_size=10000, processing_func=None):
        """Process large files in chunks"""
        results = []
        
        for chunk in pd.read_csv(file_path, chunksize=chunk_size):
            if processing_func:
                processed_chunk = processing_func(chunk)
                results.append(processed_chunk)
            else:
                results.append(chunk)
        
        return pd.concat(results, ignore_index=True) if results else pd.DataFrame()
```

## Pattern Usage Guidelines

### Implementation Checklist
- [ ] Choose appropriate pattern for use case
- [ ] Adapt pattern to specific requirements
- [ ] Implement error handling and logging
- [ ] Add validation and testing
- [ ] Document any customizations
- [ ] Update pattern if improvements found

### Pattern Evolution
- Regular review of pattern effectiveness
- Community contributions and improvements
- Version control for pattern changes
- Performance benchmarking and optimization
- Integration with new technologies and approaches

## Related Documentation
- See `data_lake/agents/knowledge/decisions/` for pattern selection rationale
- Reference `data_lake/docs/implementation_guides/` for detailed implementation instructions
- Check `data_lake/examples/` for pattern usage examples
- Review `data_lake/tests/patterns/` for pattern validation tests
