# Landing Zone

## Changelog

### 2025-05-22: DistroKid Streaming Data Automation
- Automated extraction of DistroKid streaming and Apple Music stats using Playwright.
- HTML page sources are now saved with datetime-stamped filenames (e.g., `streams_stats_YYYYMMDD_HHMMSS.html`).
- See `src/distrokid/extractors/dk_auth.py` for the automation script.

### 2025-05-22: DistroKid Validation & Promotion
- Added validation script for DistroKid HTML in landing zone
- Valid files are automatically copied to `raw/distrokid/streams/` for immutable storage
- See `src/distrokid/extractors/validate_dk_html.py` for details

## Purpose
The landing zone is the initial entry point for all incoming data into the data lake. This is where data is first ingested from various sources before any processing occurs.

## What Goes Here
- Raw data files from external sources
- API responses
- Data dumps from production systems
- Third-party data feeds

## Rules
- Data should be in its original, unaltered form
- No transformations or modifications allowed
- Files should be read-only once written
- Include source system and timestamp in filenames

## Example Files
- `tiktok_analytics_20240522.json`
- `spotify_streams_20240522.csv`
- `distrokid_sales_20240522.xlsx`

## Next Step
Data in this zone should be moved to the `raw` zone after initial validation.
