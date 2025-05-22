# src Directory

## TooLost Scraper Automation
- The Playwright-based TooLost scraper now uses robust dropdown option detection by visible text.
- Platform switching (Spotify → Apple) is fully automated, no manual clicks required.
- Script prints all dropdown options and selects the correct one for reliable, hands-free data extraction.

## Purpose
The `src` directory contains all source code for data extraction, transformation, and loading (ETL) processes in the BEDROT Data Lake project. This is where you will find scripts, modules, and utilities for automating data workflows.

## Structure
- `distrokid/` — Scripts and extractors for DistroKid streaming and sales data
- (Add additional subdirectories as new sources or ETL modules are added)

## Example Usage
- All Playwright scripts use `src/.playwright_dk_session` as the master persistent session directory for browser automation.
- Run DistroKid extraction:
  ```bash
  python src/distrokid/extractors/dk_auth.py
  ```

## Notes
- All Playwright scripts should use `src/.playwright_dk_session` as the persistent context for session reuse and space savings.
- Source code should be modular and documented
- Sensitive information (credentials, tokens) should be managed via environment variables or a `.env` file
- Test scripts before running in production

---
For details on the data lake zones and ingestion flow, see the main project `README.md`.
