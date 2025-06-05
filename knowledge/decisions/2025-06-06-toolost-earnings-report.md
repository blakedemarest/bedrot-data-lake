# ADR: Toolost Earnings Report Pipeline

## Status
Proposed

## Context
We recently extracted a Toolost earnings CSV named `@05-2025-70799.csv`.
Existing ETL scripts handle only analytics JSON files. The new CSV contains
earnings data that must flow through landing, raw, staging, and curated zones.

## Decision
Add an earnings pipeline for Toolost that mirrors the DistroKid bank details
workflow.

- **landing2raw**: Validate the earnings CSV (non-empty, expected columns) and
  copy it to `raw/toolost/earnings/` with versioning.
- **raw2staging**: Read the latest earnings CSV, normalize column names to
  `date` and `earnings_usd`, and output `daily_earnings_toolost.csv` in staging.
- **staging2curated**: Merge `daily_earnings_toolost.csv` into a new curated
  dataset `tidy_daily_earnings.csv`, archiving prior versions if the file
  changes.

## Consequences
This design introduces a parallel finance path for Toolost. The scripts remain
source-specific but share the same audit and archive logic as other cleaners.
Future earnings files will be ingested automatically once the code changes are
implemented.
