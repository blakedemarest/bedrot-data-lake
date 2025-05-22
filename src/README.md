# src Directory

## Purpose
The `src` directory contains all source code for data extraction, transformation, and loading (ETL) processes in the BEDROT Data Lake project. This is where you will find scripts, modules, and utilities for automating data workflows.

## Structure
- `distrokid/` — Scripts and extractors for DistroKid streaming and sales data
- (Add additional subdirectories as new sources or ETL modules are added)

## Example Usage
- Run DistroKid extraction:
  ```bash
  python src/distrokid/extractors/dk_auth.py
  ```

## Notes
- Source code should be modular and documented
- Sensitive information (credentials, tokens) should be managed via environment variables or a `.env` file
- Test scripts before running in production

---
For details on the data lake zones and ingestion flow, see the main project `README.md`.
