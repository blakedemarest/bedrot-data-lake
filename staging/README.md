# Staging Zone

## Purpose
The staging zone is where data is cleaned, validated, and transformed into a consistent format. This zone serves as a preparation area before data reaches the curated zone.

## What Goes Here
- Cleaned and standardized data
- Data with enforced schemas
- Validated and quality-checked datasets
- Joined or aggregated data from multiple sources

## Rules
- Data should be in a structured format (e.g., Parquet, ORC)
- Schema validation is required
- Data quality checks must pass
- Include data lineage information
- Document all transformations applied

## Example Files
- `analytics/daily_metrics/2024/05/22/metrics.parquet`
- `social/combined_engagement/2024/05/22/engagement_stats.parquet`

## Next Step
After validation, data moves to the `curated` zone for business use.
