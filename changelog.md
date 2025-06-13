--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-06-06-ci-workflow
# What Changed (≤ 50 words)
Added GitHub Actions workflow running pytest with coverage on each push and pull request. README now documents how to run tests locally.
# Impact
- Standard CI testing ensures reliability
- Coverage artifacts available for analysis
# Follow-ups
- Enforce coverage thresholds as tests expand
--- END CHANGELOG ENTRY ---

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

--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-05-26-cronjob-automation

# What Changed (≤ 50 words)
Added a Python script to auto-generate a "no extractors" cron job batch file from the master cron job. The master batch file now always runs this script as its final step, ensuring the secondary file is always up-to-date and eliminating manual duplication.

# Impact
- No more manual edits needed for the secondary cron job file
- Centralized maintenance of ETL pipeline scheduling
- All batch file steps now run in the correct working directory
- Cleaner scripts now print the most recent reporting date for auditability

# Follow-ups
- Replace analytics/reporting placeholders with real scripts
- Consider similar automation for other workflow variants
--- END CHANGELOG ENTRY ---

--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-05-27-meta_ads_dump_folder_naming

# What Changed (≤ 50 words)
Meta Ads extractor output folder now uses the format `meta_ads_dump_<timestamp>` under the landing directory. Ad set level spend is included in [insights.json](cci:7://file:///c:/Users/Earth/BEDROT%20PRODUCTIONS/BEDROT%20DATA%20LAKE/data_lake/landing/20250527_123555/insights.json:0:0-0:0). Output directory is anchored to `PROJECT_ROOT` from `.env`.

# Impact
All Meta Ads dumps are organized with clear, timestamped folder names for easy tracking. Data is reliably stored in the correct landing directory. No breaking changes.

# Follow-ups
Validate downstream scripts use the new folder naming. Consider adding similar timestamped naming for other extractors.
--- END CHANGELOG ENTRY ---

--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-05-27-metaads_tidy_cleaner

# What Changed (≤ 50 words)
Added [metaads_tidy.py](cci:7://file:///c:/Users/Earth/BEDROT%20PRODUCTIONS/BEDROT%20DATA%20LAKE/data_lake/src/metaads/cleaners/metaads_tidy.py:0:0-0:0) cleaner script for Meta Ads. It auto-detects the latest landing folder, loads all raw JSONs, and converts key metrics to numeric types for robust analysis. No manual path edits required.

# Impact
Cleaner is now fully automated and batch-friendly. Ensures all metrics are numeric for downstream analytics. Reduces manual errors and setup time.

# Follow-ups
Document additional cleaning steps as they are added. Consider extending the pattern to other data sources.
--- END CHANGELOG ENTRY ---

--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-05-27-StagingCleanerRefactor

# What Changed (≤ 50 words)
All finalized output CSVs from DistroKid, TooLost, and Meta Ads cleaner scripts now write to the `staging/` directory (not `curated/`). Path management standardized using `PROJECT_ROOT` from `.env`. All relevant README files updated to reflect this workflow.

# Impact
- Output location for analytics and reporting scripts is now `/staging`
- No more hardcoded project root paths
- Improved automation and portability
- Documentation is accurate and up-to-date

# Follow-ups
- Update downstream analytics/reporting scripts to read from `/staging`
- Add script-specific documentation if needed
--- END CHANGELOG ENTRY ---

--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-05-27-metaads_curated_promotion

# What Changed (≤ 50 words)
Automated promotion of `tidy_metaads.csv` from `/staging` to `/curated` as `metaads_campaigns_daily.csv` via the [metaads_tidy.py](cci:7://file:///c:/Users/Earth/BEDROT%20PRODUCTIONS/BEDROT%20DATA%20LAKE/data_lake/src/metaads/cleaners/metaads_tidy.py:0:0-0:0) cleaner script. No changes to upstream data processing logic.

# Impact
- Meta Ads business-ready data is now available in the curated zone for analytics and reporting.
- Ensures consistent naming and location for downstream consumers.
- No new dependencies or breaking changes.

# Follow-ups
- Update `/curated/README.md` to document the new Meta Ads dataset and schema.
- Consider adding schema/data dictionary details for future maintainers.

--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-05-27-linktree_analytics_extractor

# What Changed (≤ 50 words)
Created a Playwright-based extractor script for Linktree analytics. The script automates login, sets analytics filters, and captures all relevant GraphQL network responses, saving them to the landing zone for further processing.

# Impact
No new dependencies beyond Playwright. Enables automated, repeatable Linktree analytics extraction. Manual login supported for secure authentication.

# Follow-ups
- Integrate with main ETL/cron if desired
- Add post-processing/validation for captured JSONs
- Document usage in project-level README
--- END CHANGELOG ENTRY ---

# Change ID
2025-05-28-tiktok-extractor-rollout

# What Changed (≤ 50 words)
Initial rollout and stabilization of the TikTok analytics extractor. The extractor now reliably automates login, analytics navigation, date range selection, and CSV download using a persistent browser session. All debug output removed and context closing fixed.

# Impact
- TikTok analytics extraction is now fully automated and production-ready.
- No manual tab management or debug noise.
- Resolves long-standing automation and selector issues.

# Follow-ups
- Parameterize date range and file format for future flexibility.
- Add error handling/logging for failed downloads.
- add further functionality for other artist pig1987

--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-05-28-tiktok-extractor-pig1987-profile

# What Changed (≤ 50 words)
Created a new script, [tiktok_analytics_extractor_pig1987.py](cci:7://file:///c:/Users/Earth/BEDROT%20PRODUCTIONS/BEDROT%20DATA%20LAKE/data_lake/src/tiktok/extractors/tiktok_analytics_extractor_pig1987.py:0:0-0:0), to automate TikTok analytics extraction for the PIG1987 account. The script uses a dedicated persistent Playwright user profile and PIG1987-specific cookies, ensuring full session isolation from other TikTok automation.

# Impact
- Each TikTok automation now uses its own browser profile for true multi-account support.
- The script will auto-create the profile directory if missing and import cookies only once.
- No interference between ZONE A0 and PIG1987 sessions.

# Follow-ups
-create loading script for tiktok analytics, moving csvs from landing to raw to staging to curated
--- END CHANGELOG ENTRY ---

--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-05-28-metaads-landing-folder-refactor

# What Changed (≤ 50 words)
Refactored both the Meta Ads extractor (`meta_raw_dump.py`) and cleaner ([metaads_tidy.py](cci:7://file:///c:/Users/Earth/BEDROT%20PRODUCTIONS/BEDROT%20DATA%20LAKE/data_lake/src/metaads/cleaners/metaads_tidy.py:0:0-0:0)) scripts to use the dedicated `landing/metaads/` subfolder for all raw dumps and tidy processing, instead of the root landing folder.

# Impact
- Keeps Meta Ads data organized and isolated from other sources.
- Prevents accidental processing of non-Meta Ads data.
- Pipeline is now source-specific and easier to maintain.

# Follow-ups
- Update documentation to reflect new folder structure.
- Apply similar refactoring to other sources if needed.
--- END CHANGELOG ENTRY ---

--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-06-05-toolost-extractor-flow

# What Changed (≤ 50 words)
Refactored `toolost_scraper.py` so that analytics extraction (Spotify/Apple) always completes before navigating to notifications for sales report download. Updated all relevant README files to document the new ETL flow, modularity, and robust folder usage.

# Impact
- Ensures reliable TooLost ETL runs in automation and batch.
- Reduces flakiness in both analytics and sales report extraction.
- Improves project documentation and onboarding clarity.
- No new dependencies.

# Follow-ups
- Monitor for edge cases in notifications detection.
- Consider similar flow audits for other Playwright-based extractors.
--- END CHANGELOG ENTRY ---

--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-06-06-toolost-earnings-pipeline
# What Changed (≤ 50 words)
Planned a new TooLost earnings pipeline based on the CSV `@05-2025-70799.csv`.
Landing2raw, raw2staging, and staging2curated will validate, transform, and merge
these reports into curated earnings data.
# Impact
- Adds a finance path for TooLost with the same audit logic as streams.
- Provides a curated `tidy_daily_earnings.csv` for analytics.
# Follow-ups
- Implement the code updates in the three cleaner scripts.
- Validate sample earnings data to finalize schema.
--- END CHANGELOG ENTRY ---

# Change ID
2025-06-12-LinktreeReadmeFinalization

# What Changed (≤ 50 words)
Documented Linktree pipeline outputs in [staging/README.md](cci:7://file:///c:/Users/Earth/BEDROT%20PRODUCTIONS/BEDROT%20DATA%20LAKE/data_lake/staging/README.md:0:0-0:0) and [curated/README.md](cci:7://file:///c:/Users/Earth/BEDROT%20PRODUCTIONS/BEDROT%20DATA%20LAKE/data_lake/curated/README.md:0:0-0:0) after validating cleaners; no code changes.

# Impact
Improves discoverability & data-catalog accuracy; **no runtime impact**.

# Follow-ups
Replicate README updates for other new datasets as they come online.

--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-06-13-ServiceDirsAndTodoUpdate

# What Changed (≤ 50 words)
Created standard `src/<service>/{extractors,cleaners,cookies}` directories for Spotify, Mailchimp, Instagram, YouTube.  
Updated [CODEBASE_TODO.md](cci:7://file:///c:/Users/Earth/BEDROT%20PRODUCTIONS/BEDROT%20DATA%20LAKE/data_lake/CODEBASE_TODO.md:0:0-0:0) with “Upcoming Service Integrations” section (IDs S-1…S-4), outlining next-step tasks for each service.

# Impact
• Directory scaffolds unblock extractor/cleaner development.  
• TODO now tracks integration roadmap.  
(no code execution changes)

# Follow-ups
• Scaffold Spotify extractor & cleaner templates.  
• Add cron entries for new services after scripts exist.  
• Set up credential management for each API/Scraper.

--- END CHANGELOG ENTRY ---

--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-06-13-tiktok_staging2curated

# What Changed (≤ 50 words)
Added [src/tiktok/cleaners/tiktok_staging2curated.py](cci:7://file:///c:/Users/Earth/BEDROT%20PRODUCTIONS/BEDROT%20DATA%20LAKE/data_lake/src/tiktok/cleaners/tiktok_staging2curated.py:0:0-0:0) to aggregate all TikTok metrics by `artist`, `zone`, and `date`, producing curated CSV (Parquet optional).

# Impact
New curated dataset; cron now produces TikTok analytics ready for reporting.

# Follow-ups
Add unit tests; integrate into README datasets table.
--- END CHANGELOG ENTRY ---

--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-06-13-tiktok_csv_only

# What Changed (≤ 50 words)
Modified [tiktok_staging2curated.py](cci:7://file:///c:/Users/Earth/BEDROT%20PRODUCTIONS/BEDROT%20DATA%20LAKE/data_lake/src/tiktok/cleaners/tiktok_staging2curated.py:0:0-0:0) to default to `staging/tiktok/tiktok.csv`; removed Parquet dependency and improved error handling.

# Impact
Cleaner runs without Parquet; simplifies pipeline.

# Follow-ups
Deprecate Parquet paths in older docs; update cron docs.
--- END CHANGELOG ENTRY ---

--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-06-13-service_zone_dirs

# What Changed (≤ 50 words)
Created landing/raw/staging/curated directories for new services (Spotify, Mailchimp, Instagram, YouTube).

# Impact
Standard zone layout in place; unblock future extractors.

# Follow-ups
Define path helpers; update cron to include new services when scripts exist.
--- END CHANGELOG ENTRY ---

--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-06-13-src_service_scaffold

# What Changed (≤ 50 words)
Added `src/<service>/{extractors,cleaners,cookies}` scaffolds for Spotify, Mailchimp, Instagram, YouTube, following Service_Integration_Guide.md.

# Impact
Developers now have canonical locations for code; lint & tests won’t fail on missing paths.

# Follow-ups
Generate minimal `__init__.py` and `.gitkeep`; scaffold initial extractor templates.
--- END CHANGELOG ENTRY ---

--- CHANGELOG ENTRY (PIN THIS) ---
# Change ID
2025-06-13-todo_service_section

# What Changed (≤ 50 words)
Appended “Upcoming Service Integrations” section (IDs S-1…S-4) to [CODEBASE_TODO.md](cci:7://file:///c:/Users/Earth/BEDROT%20PRODUCTIONS/BEDROT%20DATA%20LAKE/data_lake/CODEBASE_TODO.md:0:0-0:0), detailing tasks for each new service.

# Impact
Roadmap visible to contributors; improves planning and PR linkage.

# Follow-ups
Open GitHub issues per ID; reference in future PRs.
--- END CHANGELOG ENTRY ---