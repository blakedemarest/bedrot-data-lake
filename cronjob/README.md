# Data Lake Master Cron Job

## What This Cron Job Does
This master cron job automates the sequential execution of all critical ETL and analytics scripts for the BEDROT Data Lake. It ensures that raw data is extracted, validated, explored, curated, and reported on in a robust, repeatable fashion.

**The workflow includes:**
- Extracting and validating Meta Ads, DistroKid, and TooLost data
- Running exploratory/cleaning notebooks
- Curating and preparing analytics-ready datasets
- Generating analytics and reports

The execution order and dependencies are visualized in `data_lake_cron_flow.dot` (render with Graphviz).

## How It’s Scheduled
- The cron job is scheduled using **Windows Task Scheduler** to run every Monday, Wednesday, and Friday.
- The batch file (`run_datalake_cron.bat`) should be set as the program to execute in Task Scheduler.
- All paths are relative to the project root, which is referenced via the `.env` variable `PROJECT_ROOT`.

## Caveats & Dependencies
- **Python** must be installed and available in your PATH.
- All Python scripts and Jupyter notebooks must be present and executable.
- The `.env` file must be configured correctly, including `PROJECT_ROOT`.
- If any script fails, the batch file will stop and require manual intervention.
- Jupyter notebooks should be converted to `.py` scripts for full automation, or run with `papermill`/`nbconvert`.
- Graphviz must be installed to render the flow diagram.

---
**Edit this README as your pipeline evolves!**
