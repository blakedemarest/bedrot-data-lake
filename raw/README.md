# Raw Zone

## [2025-05-22] Update
- TooLost analytics scraper now reliably extracts and saves both Spotify and Apple Music data without manual intervention, improving the completeness of the raw data zone.

## Purpose
The raw zone stores an immutable, exact copy of the source data after initial validation. This serves as the single source of truth for all downstream processing.

## What Goes Here
- Validated copies of landing zone data (e.g., DistroKid HTML snapshots that pass validation)
- Data in its most granular form
- Original data types and structures preserved
- No data should be deleted or modified

## DistroKid Validation & Promotion
- Only DistroKid HTML files that pass automated validation are promoted here from landing
- See `src/distrokid/extractors/validate_dk_html.py` for validation logic

## Rules
- Data is append-only
- No transformations allowed
- Must maintain data lineage back to source
- Compress files for storage efficiency when possible
- Include metadata about the source and ingestion process

## Example Files
- `tiktok/raw/v1/2024/05/22/analytics_001.parquet`
- `spotify/streams/2024/05/22/streaming_history.json`

## Next Step
Data from here is processed and moved to the `staging` zone.
