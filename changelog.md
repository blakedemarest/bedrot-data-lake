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