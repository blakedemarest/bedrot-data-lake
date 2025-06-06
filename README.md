# BEDROT Data Lake

## Executive Summary

The BEDROT Data Lake provides a robust, modular, and auditable platform for ingesting, validating, transforming, and curating data from music, social, and ad platforms. Data flows through clearly defined zones (Landing, Raw, Staging, Curated, Archive), ensuring traceability, governance, and business readiness. Automation and modular Python ETL scripts (with Playwright for web sources) enable reliable, scalable operations.

For full architectural diagrams and technical deep-dive, see: `BEDROT_Data_Lake_Analysis.md`

## Project Folder Structure

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

This is the central data lake for BEDROT productions

---



---

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
  - `raw/` — Raw ETL helpers/utilities
- `staging/` — **Data cleaning, validation, and transformation zone**. Where data is standardized, quality-checked, and joined/aggregated. All transformations and schema enforcement occur here. **All output from cleaner scripts (DistroKid, TooLost, Meta Ads, etc.) lands here by default.** Next step: move to `curated` for business use.
- `tests/` — Automated tests

---

### Data Lake Zone Definitions

- **Landing Zone**: Initial data ingestion, raw files, timestamped, never modified. Ensures traceability and auditability.
- **Raw Zone**: Immutable, validated, append-only. Full data lineage, no transformations.
- **Staging Zone**: Data cleaning, validation, transformation, and joining. All business logic applied here. Outputs promoted to `curated/` only after validation.
- **Curated Zone**: Business-ready, stable, and documented datasets for analytics and ML. Consumed by BI tools and downstream apps.
- **Archive Zone**: Long-term retention for compliance and historical analysis.

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

## ETL Pipeline Architecture

The ETL pipeline is modular and source-centric, with clear separation between extraction, validation, transformation, and loading. Automation is managed by batch/cron jobs that trigger each stage in sequence.

- **Extraction**: Playwright-based scripts for DistroKid, TooLost, TikTok, Meta Ads, Linktree, etc. Each extractor handles login/2FA, navigation, and robust download/capture of analytics and sales reports.
- **Validation**: Landing-to-raw validators ensure data integrity, structure, and correct source mapping.
- **Transformation**: Raw-to-staging cleaners standardize, join, and aggregate data. All business logic is applied here. Outputs are only promoted to curated after validation.
- **Loading**: Staging-to-curated promotion scripts archive prior versions and ensure only changed data is written.
- **Automation**: All stages are orchestrated by batch scripts and cron jobs for hands-off operation.

### Extractor Class Hierarchy

- `BaseExtractor`: Common interface for all extractors (`extract_data`, `validate_credentials`, `handle_authentication`).
- `PlaywrightExtractor`: Adds browser/session logic, login/2FA handling, and navigation helpers.
- `DistroKidExtractor`, `TooLostExtractor`, `TikTokExtractor`, etc.: Source-specific subclasses implementing analytics and report extraction logic.
- `MetaAdsExtractor`: API-based, implements campaign/ad/adset/insights extraction.

See `BEDROT_Data_Lake_Analysis.md` for class diagrams and technical details.

## Automation & Operational Strategy

- **Cron jobs**: Master cron triggers all ETL stages. No manual duplication—secondary batch files are auto-generated.
- **Monitoring & Logging**: All major ETL steps are logged for traceability. Failures trigger clear logs for troubleshooting.
- **Validation & Error Handling**: Validators and robust error handling at every stage ensure data quality and pipeline resilience.

## Changelog

### 2025-06-05: TooLost Extractor Flow Refactor (`2025-06-05-toolost-extractor-flow`)
- Refactored `toolost_scraper.py` for correct extraction order and improved robustness. See changelog for details.

---

For full diagrams, technical details, and deep-dive documentation, see `BEDROT_Data_Lake_Analysis.md`.

## Getting Started with MinIO

1. **Prerequisites**
   - Docker and Docker Compose installed
   - Ports 9000 and 9001 available

2. **Start MinIO**
   ```bash
   docker-compose up -d
   ```

3. **Access MinIO Console**
   - URL: http://localhost:9001
   - Username: admin
   - Password: your_secure_password

4. **Create Buckets**
   After logging in, create the following buckets:
   - landing
   - raw
   - staging
   - curated
   - archive
   - sandbox

## Environment Variables

Update `.env` with your preferred credentials before starting MinIO.

## Data Flow

1. Data lands in the `landing` zone
2. Processed to `raw` (immutable)
3. Cleaned in `staging`
4. Business-ready in `curated`
5. Archived to `archive` when no longer actively used

## Running Tests

This project uses **pytest** for the test suite. To run tests locally with coverage:

```bash
pip install -r requirements.txt
pytest -q --cov=src
```

The CI workflow executes the same command on every push and pull request. Coverage results are uploaded as an artifact in GitHub Actions.

