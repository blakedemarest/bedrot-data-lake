# BEDROT Data Lake

This is the central data lake for BEDROT productions

---

## Cron Job Pipeline Automation

**Centralized Cron Job Maintenance:**
- Only edit the master cron job file: `cronjob/run_datalake_cron.bat`.
- The secondary batch file (`run_datalake_cron_no_extractors.bat`, which skips extractor scripts) is always generated automatically by `cronjob/generate_no_extractors_cron.py` (run as the last step of the master cron job).
- This eliminates manual duplication and ensures both cron jobs are always in sync.

---



- `.agent/` — AI agent working directories (cache, context, logs)
- `archive/` — **Historical data**; long-term storage for datasets no longer actively used.
- `changelog.md` — Project changelog.
- `cronjob/` — Batch files and automation scripts.
- `curated/` — **Business-ready datasets**. Main consumption layer for analytics, dashboards, and ML. Contains cleaned, aggregated, and enriched data with stable schemas and documentation.
- `data_lake_flow.dot` — Pipeline visualization (Graphviz).
- `docker-compose.yml` — MinIO and other service orchestration.
- `image.png`, `image.svg` — Project diagrams.
- `knowledge/` — AI knowledge base (decisions, patterns, agents).
- `landing/` — **Initial data ingestion zone**. Raw, unaltered data files from all external sources (APIs, partners, etc). No transformations allowed. Files are read-only and timestamped. Next step: move to `raw` after initial validation.
- `minio/` — MinIO configuration.
- `raw/` — **Immutable, validated source-of-truth zone**. Exact, append-only copies of validated data from landing. No transformations. Maintains full lineage. Next step: processed to `staging`.
- `requirements.txt` — Python dependencies.
- `sandbox/` — Experimental work area (Jupyter notebooks for raw data exploration and cleaning).
- `src/` — All ETL and pipeline code:
  - `distrokid/`
    - `extractors/` — DistroKid ## Directory Structuredata extraction scripts
    - `cleaners/` — DistroKid data cleaning scripts
  - `metaads/`
    - `extractors/` — Meta Ads data extraction scripts
    - `cleaners/` — Meta Ads data cleaning scripts (see below)
  - `linktree/`
    - `extractors/` — Linktree data extraction scripts
    - `cleaners/` — Linktree data cleaning scripts
  - `tiktok/`
    - `extractors/` — TikTok data extraction scripts
    - `cleaners/` — TikTok data cleaning scripts
  - `raw/` — Raw ETL helpers/utilities
- `staging/` — **Data cleaning, validation, and transformation zone**. Where data is standardized, quality-checked, and joined/aggregated. All transformations and schema enforcement occur here. Next step: move to `curated` for business use.
- `tests/` — Automated tests

---

### Meta Ads Data Cleaner: `metaads_tidy.py`

- **Purpose:**
  - Loads the most recent Meta Ads dump from the landing zone automatically (no manual folder selection needed).
  - Reads all raw JSON files (`ads.json`, `adsets.json`, `campaigns.json`, `insights.json`, `campaigns.json`).
  - Converts key metrics (`spend`, `impressions`, `clicks`, `reach`, `cpc`, `ctr`, `frequency`) to numeric types for analysis and cleaning.
  - Prints loaded dataframe shapes for quick sanity checking.

- **How it works:**
  - Uses `PROJECT_ROOT` from `.env` for robust path resolution.
  - Always selects the latest timestamped Meta Ads dump folder in `landing/`.
  - Designed for easy extension (add more cleaning, joins, or exports as needed).

- **Benefits:**
  - Zero manual path edits needed—safe for automation and batch runs.
  - Ensures all metrics are numeric for downstream analytics and reporting.
  - Can be adapted for other data sources with similar folder conventions.

---

### Data Zone Importance & Flow

- **Landing:** _First stop for all incoming data. Ensures traceability and auditability from the very start. No changes allowed—preserves original context._
- **Raw:** _Immutable, validated, and append-only. The single source of truth for all downstream processing. Guarantees reproducibility and full lineage._
- **Staging:** _Where data is cleaned, validated, and transformed. Ensures consistency, quality, and readiness for analytics. All business logic and joins applied here._
- **Curated:** _The “golden” layer. Datasets are business-ready, documented, and optimized for analytics, reporting, and ML. This is what end-users and applications consume._
- **Archive:** _Long-term retention. Keeps historical data accessible for compliance and future analysis._

This structure ensures robust data governance, auditability, and a clear, repeatable data flow from raw ingestion to business insight.

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
