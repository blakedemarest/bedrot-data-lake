# Raw Zone

## Purpose
The raw zone stores an immutable, exact copy of the source data after initial validation. This serves as the single source of truth for all downstream processing.

## What Goes Here
- Validated copies of landing zone data
- Data in its most granular form
- Original data types and structures preserved
- No data should be deleted or modified

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
