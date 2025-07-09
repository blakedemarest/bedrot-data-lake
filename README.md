# BEDROT Data Lake

## Executive Summary

The BEDROT Data Lake is a production-grade, multi-zone ETL platform that ingests, validates, transforms, and curates data from 15+ music industry platforms. Built with Python and Playwright, it processes streaming analytics, financial transactions, social media metrics, and advertising data through a robust 5-zone architecture ensuring complete data lineage, governance, and business readiness.

### Key Capabilities
- **Multi-Platform Integration**: Spotify, TikTok, Meta Ads, DistroKid, Linktree, TooLost, YouTube, MailChimp
- **Zone-Based Processing**: Landing → Raw → Staging → Curated → Archive
- **Automated Orchestration**: Cron-based pipeline execution with dependency management
- **Data Quality**: SHA-256 deduplication, schema validation, business rule enforcement
- **AI-Ready**: Comprehensive documentation for autonomous agent operations

For full architectural diagrams and technical deep-dive, see: `BEDROT_Data_Lake_Analysis.md`

## 📁 Data Lake Architecture

```plaintext
BEDROT_DATA_LAKE/
├── .agent/
├── .venv/
├── .windsurf/
├── archive/
├── curated/
├── landing/
├── minio/
├── raw/
├── sandbox/
├── src/
│   ├── .playwright_dk_session/ (configurable via PLAYWRIGHT_SESSION_DIR)
│   ├── distrokid/
│   │   ├── extractors/
│   │   └── cleaners/
│   ├── linktree/
│   │   ├── extractors/
│   │   └── cleaners/
│   ├── metaads/
│   │   ├── extractors/
│   │   └── cleaners/
│   ├── tiktok/
│   │   ├── extractors/
│   │   ├── cleaners/
│   │   └── cookies/
│   ├── toolost/
│   │   ├── extractors/
│   │   └── cleaners/
├── staging/
├── staged/
├── tests/
├── agents/
│   └── knowledge/
```

### Zone-Based Data Flow
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   LANDING   │───▶│     RAW     │───▶│   STAGING   │───▶│   CURATED   │───▶│   ARCHIVE   │
│             │    │             │    │             │    │             │    │             │
│ • Raw files │    │ • Validated │    │ • Cleaned   │    │ • Business  │    │ • Historical│
│ • Timestamped│    │ • Immutable │    │ • Transform │    │ • Analytics │    │ • Compliance│
│ • All sources│    │ • Lineage   │    │ • Quality   │    │ • Aggregated│    │ • Backup    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

- `.agent/` — AI agent working directories (cache, context, logs)
- `archive/` — **Archive Zone**: Long-term storage for datasets no longer actively used. Ensures historical data is preserved for compliance and future analysis.
- `changelog.md` — Project changelog.
- `cronjob/` — Batch files and automation scripts (automation triggers all ETL stages).
- `curated/` — **Curated Zone**: Business-ready datasets for analytics, dashboards, and ML. Cleaned, aggregated, and enriched data with stable schemas.
  - **Note:** All outputs from cleaner scripts are first written to `staging/` and only promoted to `curated/` after validation.
- `data_lake_flow.dot` — Pipeline visualization (Graphviz).
- `docker-compose.yml` — MinIO and other service orchestration.
- `image.png`, `image.svg` — Project diagrams (see analysis doc for mermaid diagrams).
- `agents/knowledge/` — AI knowledge base (decisions, patterns, agents).
- `landing/` — **Landing Zone**: Initial data ingestion. Raw, unaltered, timestamped files from all external sources. Read-only. Next: move to `raw` after validation.
- `minio/` — MinIO configuration.
- `raw/` — **Raw Zone**: Immutable, validated, append-only copies of data from landing. Maintains full lineage. Next: processed to `staging`.
- `requirements.txt` — Python dependencies.
- `sandbox/` — Experimental work area (Jupyter notebooks for raw data exploration and cleaning).
- `src/` — All ETL and pipeline code:
  - `distrokid/`
    - `extractors/` — DistroKid data extraction scripts
    - `cleaners/` — DistroKid data cleaning scripts
  - `metaads/`
    - `extractors/` — Meta Ads data extraction scripts
  - `linktree/`
    - `extractors/` — Linktree data extraction scripts
    - `cleaners/` — Linktree data cleaning scripts
  - `metaads/`
    - `extractors/` — Meta Ads data extraction scripts
    - `cleaners/` — Meta Ads data cleaning scripts (see below)
  - `tiktok/`
    - `extractors/` — TikTok data extraction scripts
      - `tiktok_analytics_extractor_zonea0.py` — Extracts analytics for the ZONE A0 TikTok account using its own persistent browser profile and cookies.
      - `tiktok_analytics_extractor_pig1987.py` — Extracts analytics for the PIG1987 TikTok account with a separate browser profile and cookies.
      - Extendable: Add new extractor scripts for additional TikTok accounts by duplicating and adjusting the user profile/cookie paths as needed.
    - `cleaners/` — TikTok data cleaning scripts
  - `toolost/`
    - `extractors/` — TooLost data extraction scripts (see `toolost_scraper.py` for robust Playwright-based ETL: analytics is always extracted before notifications/sales report)
    - `cleaners/` — TooLost data cleaning scripts
    - Each source folder includes a README with examples.
  - `raw/` — Raw ETL helpers/utilities
- `staging/` — **Data cleaning, validation, and transformation zone**. Where data is standardized, quality-checked, and joined/aggregated. All transformations and schema enforcement occur here. **All output from cleaner scripts (DistroKid, TooLost, Meta Ads, etc.) lands here by default.** Next step: move to `curated` for business use.
- `tests/` — Automated tests

---

### 🔄 Data Lake Zone Definitions

#### Landing Zone (`landing/`)
- **Purpose**: Initial data ingestion from external sources
- **Characteristics**: Raw, unprocessed, timestamped files
- **Format**: Original format (HTML, JSON, CSV) from source systems
- **Retention**: Permanent for audit trail and reprocessing capability
- **Access**: Write-only by extractors, read-only for downstream processing

#### Raw Zone (`raw/`)
- **Purpose**: Validated, immutable copy of landing data
- **Characteristics**: Append-only, never modified, full lineage tracking
- **Format**: Standardized NDJSON and CSV with consistent schemas
- **Validation**: Data type checking, required field validation, duplicate detection
- **Storage**: SHA-256 hash tracking in `_hashes.json` for deduplication

#### Staging Zone (`staging/`)
- **Purpose**: Data cleaning, transformation, and business rule application
- **Processing**: Normalization, enrichment, quality checks, aggregation
- **Format**: Business-aligned schemas with standardized field names
- **Quality Gates**: Data validation rules, outlier detection, completeness checks
- **Promotion**: Only validated data proceeds to curated zone

#### Curated Zone (`curated/`)
- **Purpose**: Business-ready datasets for analytics and reporting
- **Characteristics**: Stable schemas, documented, high-quality data
- **Consumers**: Data warehouse ETL, dashboards, ML models, BI tools
- **SLA**: <12 hour freshness for critical business metrics
- **Versioning**: Atomic updates with rollback capability

#### Archive Zone (`archive/`)
- **Purpose**: Long-term historical data preservation
- **Retention**: 7+ years for compliance and trend analysis
- **Access**: Read-only for historical reporting and data recovery
- **Compression**: Optimized storage for cost-effective long-term retention
- **Restoration**: Full data recovery capability for any point in time

- **DistroKid & TooLost Extractors and Staging-to-Curated Cleaners**
  - Scripts: `src/distrokid/cleaners/distrokid_staging2curated.py`, `src/toolost/cleaners/toolost_staging2curated.py`, `src/toolost/extractors/toolost_scraper.py`
  - **Unified Structure:** All Playwright-based extractors (including TooLost) are modular, robust to login/2FA, and use PROJECT_ROOT for all outputs. The TooLost extractor now completes analytics extraction (Spotify/Apple) before navigating to notifications for sales report download, ensuring reliable ETL flow. See changelog entry `2025-06-05-toolost-extractor-flow`.
  - **Workflow:**
    - Load new daily streams data for the relevant source from `staging/`.
    - Remove any stale rows for that source from the curated CSV.
    - Merge and cast numeric columns, enforce categorical ordering (`distrokid` before `toolost`).
    - Only write to `curated/` if data has changed; prior versions are archived with a timestamp in `archive/`.
    - DistroKid cleaner also promotes bank details CSVs with the same atomic, auditable logic.
    - Toolost pipeline will ingest earnings CSVs (e.g., `@05-2025-70799.csv`) via updated landing2raw, raw2staging, and staging2curated scripts.
  - **Benefits:**
    - Ensures no duplication or stale data in curated outputs.
    - Guarantees full auditability and rollback via timestamped archives.
    - Consistent, maintainable codebase for all staging-to-curated promotions.
  - See changelog entry: `2025-05-29-staging2curated-refactor` for details on the refactor and its impact.

- **Meta Ads Data Cleaner: `metaads_tidy.py`**
  - Loads the most recent Meta Ads dump from the landing zone automatically (no manual folder selection needed).
  - Reads all raw JSON files (`ads.json`, `adsets.json`, `campaigns.json`, `insights.json`).
  - Converts key metrics (`spend`, `impressions`, `clicks`, `reach`, `cpc`, `ctr`, `frequency`) to numeric types for analysis and cleaning.
  - Prints loaded dataframe shapes for quick sanity checking.
  - Always selects the latest timestamped Meta Ads dump folder in `landing/`.
  - Designed for easy extension (add more cleaning, joins, or exports as needed).

- **Linktree Analytics Extractor: `linktree_analytics_extractor.py` (2025-05-27-linktree_analytics_extractor)**
  - Location: `src/linktree/extractors/linktree_analytics_extractor.py`
  - Automates extraction of Linktree analytics via Playwright.
  - Navigates to analytics dashboard, waits for manual login, sets filters to 'Last 365 days' and 'Daily'.
  - Captures all GraphQL network responses and saves as JSON in `landing/linktree/analytics/`.
  - Browser remains open until user closes it (manual login supported).
  - See changelog entry: `2025-05-27-linktree_analytics_extractor`.

- **Benefits:**
  - Zero manual path edits needed—safe for automation and batch runs.
  - Ensures all metrics are numeric for downstream analytics and reporting.
  - Can be adapted for other data sources with similar folder conventions.

---

## 🔧 ETL Pipeline Architecture

### Pipeline Design Principles
- **Modularity**: Each service has independent extractor/cleaner scripts
- **Self-Discovery**: New services automatically detected without manual registration
- **Idempotency**: Safe to re-run any pipeline stage without data corruption
- **Atomicity**: All-or-nothing processing ensures data consistency
- **Observability**: Comprehensive logging and monitoring at every stage

### Processing Stages

#### 1. **Extraction** (`src/*/extractors/`)
- **Technology**: Playwright for browser automation, Requests for API calls
- **Capabilities**: Session management, 2FA handling, rate limiting, error recovery
- **Authentication**: Cookie-based persistence, token refresh, credential rotation
- **Output**: Raw files timestamped and stored in landing zone
- **Services**: 15+ integrated platforms with service-specific logic

#### 2. **Validation** (`*_landing2raw.py`)
- **Schema Validation**: JSON Schema enforcement, data type checking
- **Integrity Checks**: File completeness, required field validation
- **Deduplication**: SHA-256 hash comparison prevents reprocessing
- **Error Handling**: Quarantine invalid data, detailed error logging
- **Promotion**: Only valid data moves to raw zone

#### 3. **Transformation** (`*_raw2staging.py`)
- **Normalization**: Standardize field names, data types, units
- **Enrichment**: Add calculated fields, business metrics, categorization
- **Aggregation**: Time-based rollups, cross-platform summaries
- **Quality Assurance**: Outlier detection, completeness scoring
- **Business Rules**: Apply domain-specific logic and validations

#### 4. **Curation** (`*_staging2curated.py`)
- **Final Validation**: Business rule compliance, data quality gates
- **Versioning**: Atomic updates with timestamped backups
- **Documentation**: Metadata generation, lineage tracking
- **Optimization**: Index creation, query performance tuning
- **Publication**: Make data available to downstream consumers

### Extractor Class Hierarchy

- `BaseExtractor`: Common interface for all extractors (`extract_data`, `validate_credentials`, `handle_authentication`).
- `PlaywrightExtractor`: Adds browser/session logic, login/2FA handling, and navigation helpers.
- `DistroKidExtractor`, `TooLostExtractor`, `TikTokExtractor`, etc.: Source-specific subclasses implementing analytics and report extraction logic.
- `MetaAdsExtractor`: API-based, implements campaign/ad/adset/insights extraction.

See `BEDROT_Data_Lake_Analysis.md` for class diagrams and technical details.

## 🚀 Automation & Operations

### Orchestration Strategy
- **Master Cron**: Single entry point triggers all pipeline stages
- **Dependency Management**: Automatic stage sequencing based on data availability
- **Parallel Processing**: Independent services run concurrently for efficiency
- **Auto-Discovery**: New extractors automatically included in execution
- **Batch Optimization**: Smart batching reduces resource consumption

### Monitoring & Observability
- **Pipeline Health**: Success/failure tracking for each stage
- **Data Quality Metrics**: Completeness, accuracy, freshness monitoring
- **Performance Tracking**: Execution time, throughput, resource usage
- **Alert System**: Automated notifications for failures and anomalies
- **Audit Trail**: Complete lineage from source to curated data

### Error Handling & Recovery
- **Graceful Degradation**: Continue processing other sources on individual failures
- **Retry Logic**: Exponential backoff for transient failures
- **Circuit Breakers**: Prevent cascade failures across services
- **Data Quarantine**: Isolate problematic data for manual review
- **Recovery Procedures**: Automated and manual recovery options

### Operational Procedures
- **Daily Health Checks**: Automated data freshness and quality validation
- **Weekly Performance Review**: Pipeline optimization and capacity planning
- **Monthly Audits**: Compliance verification and security assessment
- **Quarterly Upgrades**: Technology stack updates and feature enhancements

## Changelog

### 2025-06-05: TooLost Extractor Flow Refactor (`2025-06-05-toolost-extractor-flow`)
- Refactored `toolost_scraper.py` for correct extraction order and improved robustness. See changelog for details.

---

## 📚 Additional Resources

### Documentation
- **[BEDROT_Data_Lake_Analysis.md](BEDROT_Data_Lake_Analysis.md)** - Technical deep-dive and architecture diagrams
- **[CLAUDE.md](../CLAUDE.md)** - AI agent guidance and development conventions
- **[Changelog](changelog.md)** - Version history and feature updates
- **Service READMEs** - Platform-specific documentation in each `src/*/` directory

### Development Resources
- **[Testing Guide](tests/README.md)** - Comprehensive testing documentation
- **[API Documentation](docs/api.md)** - Service API specifications
- **[Troubleshooting Guide](docs/troubleshooting.md)** - Common issues and solutions
- **[Performance Tuning](docs/performance.md)** - Optimization best practices

### Operational Guides
- **[Deployment Guide](docs/deployment.md)** - Production deployment procedures
- **[Monitoring Setup](docs/monitoring.md)** - Observability and alerting configuration
- **[Backup & Recovery](docs/backup.md)** - Data protection strategies
- **[Security Checklist](docs/security.md)** - Security best practices

---

**BEDROT Data Lake** | Production-Grade ETL Platform | v2.0.0

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.9+ with pip
- Docker and Docker Compose (for MinIO)
- Git for version control
- 4GB+ available RAM
- 50GB+ available disk space

### Environment Setup

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd bedrot-data-ecosystem/data_lake
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install  # Install browser drivers
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### MinIO Object Storage Setup

1. **Start MinIO Services**
   ```bash
   docker-compose up -d
   ```

2. **Access MinIO Console**
   - URL: http://localhost:9001
   - Username: admin (configurable in .env)
   - Password: your_secure_password

3. **Create Required Buckets**
   ```bash
   # Via console or programmatically
   python scripts/setup_minio_buckets.py
   ```
   Creates: `landing`, `raw`, `staging`, `curated`, `archive`, `sandbox`

### Running the Pipeline

1. **Manual Execution**
   ```bash
   # Set environment variable
   export PROJECT_ROOT="$(pwd)"
   
   # Run specific extractor
   python src/spotify/extractors/spotify_audience_extractor.py
   
   # Run specific cleaner
   python src/spotify/cleaners/spotify_landing2raw.py
   ```

2. **Automated Pipeline**
   ```bash
   # Full pipeline (Windows)
   cronjob/run_datalake_cron.bat
   
   # Cleaners only
   cronjob/run_datalake_cron_no_extractors.bat
   ```

### Data Flow Verification

1. **Check Landing Zone**: Verify raw data files are created
2. **Validate Raw Zone**: Confirm data passes validation
3. **Review Staging**: Check transformed data quality
4. **Inspect Curated**: Verify business-ready datasets
5. **Monitor Logs**: Review execution logs for errors

### Troubleshooting

- **Browser Issues**: Run `playwright install` to update drivers
- **Permission Errors**: Ensure proper file system permissions
- **Network Issues**: Check firewall settings for external APIs
- **Memory Issues**: Increase available RAM or reduce batch sizes

## 🧪 Testing & Quality Assurance

### Test Framework
```bash
# Install dependencies
pip install -r requirements.txt

# Run full test suite with coverage
pytest -ra --cov=src --cov-report=term-missing

# Run specific service tests
pytest tests/spotify/ -v
pytest tests/tiktok/ -v

# Run integration tests
pytest tests/integration/ -v
```

### Code Quality
```bash
# Code formatting
black src/
isort src/

# Linting
flake8 src/

# Type checking
mypy src/
```

### Testing Strategy
- **Unit Tests**: Individual function and class testing
- **Integration Tests**: End-to-end pipeline validation
- **Data Quality Tests**: Schema validation, data integrity checks
- **Performance Tests**: Load testing and benchmark validation
- **Security Tests**: Authentication flow and data protection validation

### Continuous Integration
- **Automated Testing**: Every push triggers full test suite
- **Coverage Reporting**: Minimum 80% code coverage required
- **Quality Gates**: Code quality checks prevent regression
- **Security Scanning**: Dependency vulnerability assessment

