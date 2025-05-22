# Landing Zone

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
