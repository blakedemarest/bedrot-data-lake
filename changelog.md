--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-05-22
# What Changed (≤ 50 words)
Finalized robust Playwright-based automation for DistroKid streaming data extraction. Script detects dashboard, navigates to both streams and Apple Music stats, and saves HTML with datetime-stamped filenames. No destructive actions unless authentication is confirmed; browser remains open for user review.
# Impact
- New dated HTML files in `landing/distrokid/streams/`
- Enhanced reliability and user control for DistroKid data pulls
- Documentation and changelogs updated in all relevant `README.md` files
- New `src/README.md` created
# Follow-ups
- Automate parsing of downloaded HTML
- Integrate with downstream pipelines if needed
--- END CHANGELOG ENTRY ---

--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-05-22-b
# What Changed (≤ 50 words)
Implemented validation script for DistroKid HTML snapshots in landing zone. Valid files are automatically promoted to raw/distrokid/streams/.
# Impact
- Ensures only files with required data structures are promoted
- Automated, auditable, and robust data flow from landing to raw
- No manual copy required for valid extractions
# Follow-ups
- Extend validation for other data sources
- Add logging or reporting for failed validations
--- END CHANGELOG ENTRY ---

--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-05-22-c
# What Changed (≤ 50 words)
Finalized robust Playwright-based automation for TooLost streaming data extraction. Script detects dashboard, navigates to both streams and Apple Music stats, and saves JSON network responses with datetime-stamped filenames. No destructive actions unless authentication is confirmed; browser remains open for user review.
# Impact
- New dated JSON files in `landing/toolost/`
- Enhanced reliability and user control for TooLost data pulls
- Documentation and changelogs updated in all relevant `README.md` files
- New `src/README.md` created
# Follow-ups
- Automate parsing of downloaded JSON
- Integrate with downstream pipelines if needed
--- END CHANGELOG ENTRY ---

--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-05-23-toolost-raw-validation
# What Changed (≤ 50 words)
Added Python script to validate TooLost analytics JSON files in landing zone. Valid files are automatically promoted to raw/toolost/streams/ with audit logging. Structure and field checks ensure only correct data is moved to the raw zone.
# Impact
- Ensures only valid TooLost analytics are promoted to raw
- Automated, auditable, and robust data flow from landing to raw/toolost/streams/
- No manual copy required for valid extractions
# Follow-ups
- Move ipynb experiments to more robust python scripts in `src/`
- Add optional deletion from landing after promotion
--- END CHANGELOG ENTRY ---

--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-05-26-meta-ads-ingest

# What Changed (≤ 50 words)
Added support for Meta Ads API data ingestion. Created [meta_raw_dump.ipynb](cci:7://file:///c:/Users/Earth/BEDROT%20PRODUCTIONS/BEDROT%20DATA%20LAKE/data_lake/sandbox/meta_raw_dump.ipynb:0:0-0:0) in sandbox to extract campaigns, ad sets, ads, and insights as raw JSON dumps to landing zone. Updated landing/README.md and main README.md to document Meta Ads as a supported source.

# Impact
- Meta Ads campaign/ad/insight data now available for analytics
- Landing zone and documentation updated for new data source

# Follow-ups
- Build cleaning/curation pipeline for Meta Ads data
- Integrate with downstream analytics workflows
--- END CHANGELOG ENTRY ---

--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-05-26-dataset-cleaners-pipeline

# What Changed (≤ 50 words)
Replaced DistroKid and TooLost exploratory notebooks with dedicated dataset cleaner scripts. Updated cronjob batch file and pipeline diagram to use these scripts, clarified README documentation, and removed notebook-based steps from the automated workflow.

# Impact
- Pipeline is now fully script-based for DistroKid and TooLost cleaning
- Improved automation, reproducibility, and maintainability
- Updated documentation and flow diagram for clarity

# Follow-ups
- Convert any remaining analytics/reporting notebooks to scripts
- Monitor for errors in new script-based steps
--- END CHANGELOG ENTRY ---


--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-05-26-cron-latest-file-automation

# What Changed (≤ 50 words)
Batch file now runs Meta Ads extraction from `src/metaads/extractors/meta_raw_dump.py`. DistroKid and TooLost cleaner scripts automatically process the latest files in the raw zone. Documentation and READMEs updated to reflect these improvements.

# Impact
- Fully automated, always-up-to-date cleaning for DistroKid and TooLost
- No more manual filename edits required in cleaner scripts
- Meta Ads extraction is now part of the main ETL pipeline
- Documentation and usage instructions improved

# Follow-ups
- Monitor for edge cases with file selection (e.g., missing or corrupt files)
- Add similar automation for any future data sources
- Consider adding logging for which files are processed each run
--- END CHANGELOG ENTRY ---