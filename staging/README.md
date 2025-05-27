# Staging Zone

## Purpose
The staging zone is where data is cleaned, validated, and transformed into a consistent format. This zone serves as a preparation area before data reaches the curated zone.

## What Goes Here
- Cleaned and standardized data
- Data with enforced schemas
- Validated and quality-checked datasets
- Joined or aggregated data from multiple sources
- **All finalized output CSVs from cleaner scripts (DistroKid, TooLost, Meta Ads, etc.) are written here first.**

## Rules
- Data should be in a structured format (e.g., Parquet, ORC, CSV)
- Schema validation is required
- Data quality checks must pass
- Include data lineage information
- Document all transformations applied
- **All ETL scripts use the `PROJECT_ROOT` variable from `.env` for robust, portable path management.**

## Next Step
After validation and business logic, only business-ready data is promoted to the `curated` zone for analytics and reporting.
