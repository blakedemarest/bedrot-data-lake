# BEDROT Data Lake

This is the central data lake for BEDROT productions

---

## Changelog

### 2025-05-22: Finalized DistroKid Data Extraction
- Added robust Playwright automation for DistroKid login, 2FA, and streaming stats extraction.
- Script now detects dashboard, navigates to both streams and Apple Music stats pages, and saves HTML with datetime-stamped filenames (e.g., `streams_stats_YYYYMMDD_HHMMSS.html`).
- No destructive actions occur unless authentication is confirmed; browser remains open for user review.
- See [`src/README.md`](src/README.md) for code structure and usage.

### 2025-05-22: TooLost JSON Validation and Promotion
- Validated copies of landing zone data (e.g., DistroKid HTML snapshots that pass validation)
- Validated TooLost analytics JSON files, promoted using `src/toolost/validate_toolost_json.py` after automated structure checks

---

## Cron Job Pipeline Automation

**Centralized Cron Job Maintenance:**
- Only edit the master cron job file: `cronjob/run_datalake_cron.bat`.
- The secondary batch file (`run_datalake_cron_no_extractors.bat`, which skips extractor scripts) is always generated automatically by `cronjob/generate_no_extractors_cron.py` (run as the last step of the master cron job).
- This eliminates manual duplication and ensures both cron jobs are always in sync.

---

## Directory Structure

- `.agent/` - AI agent working directories
  - `cache/` - Temporary processing artifacts
  - `context/` - Session-specific context
  - `logs/` - Agent execution logs
- `landing/` - Initial data ingestion area
- `raw/` - Immutable raw data
- `staging/` - Cleaned and validated data
- `curated/` - Business-ready datasets (main source for business reporting)
- `archive/` - Historical data archives
- `sandbox/` - Experimental work area (Jupyter notebooks for raw data exploration and cleaning)
    - See `src/distrokid/cleaners/distrokid_dataset_cleaner.py` and `src/toolost/cleaners/toolost_dataset_cleaner.py` for automated cleaning and merging of DistroKid and TooLost data. Use `sandbox/meta_raw_dump.ipynb` for Meta Ads API extraction and profiling. Cleaned analytics-ready CSVs are output to `curated/`.
- `knowledge/` - AI knowledge base
  - `decisions/` - Decision records
  - `patterns/` - Common data patterns
  - `agents/` - Agent-specific knowledge

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
