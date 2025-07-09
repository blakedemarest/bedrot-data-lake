# Service Integration Guide

This guide explains how existing extractors and cleaners are organised in the `src/` tree and provides a template for integrating a new data source. Follow these conventions so that automation scripts and the cron job pick up your service automatically.

## Understanding Existing Modules

The project stores ETL code by platform under `src/<platform>` with three main sub‑directories:

- `extractors/` – Python scripts that download or scrape raw data and place it in the **landing** zone. Example: `src/distrokid/extractors/dk_auth.py` logs into DistroKid and saves HTML reports.
- `cleaners/` – Scripts that promote data through `landing` → `raw` → `staging` → `curated` as CSV/NDJSON. Cleaners follow the naming conventions documented in [`LLM_cleaner_guidelines.md`](../src/LLM_cleaner_guidelines.md).
- `cookies/` – Optional JSON cookie files used by Playwright based extractors. These are loaded with `common.cookies.load_cookies()`.

### Existing Services

| Service    | Example extractor                           | Example cleaner                          | Outputs                                                    |
|------------|---------------------------------------------|-----------------------------------------|-----------------------------------------------------------|
| **DistroKid** | `distrokid/extractors/dk_auth.py`          | `distrokid/cleaners/distrokid_raw2staging.py` | Streams HTML → cleaned CSV in `staging/distrokid/` and then merged into `curated/tidy_daily_streams.csv` |
| **TooLost**   | `toolost/extractors/toolost_scraper.py`    | `toolost/cleaners/toolost_raw2staging.py`    | Spotify/Apple JSON → daily CSV in `staging/toolost/`       |
| **Meta Ads**  | `metaads/extractors/meta_raw_dump.py`      | `metaads/cleaners/metaads_raw2staging.py`   | API JSON dumps → `tidy_metaads.csv` in staging             |
| **TikTok**    | `tiktok/extractors/tiktok_analytics_extractor_zonea0.py` | `tiktok/cleaners/tiktok_raw2staging.py` | Zip exports → `tiktok.csv` in staging                     |
| **Linktree**  | `linktree/extractors/linktree_analytics_extractor.py` | `linktree/cleaners/linktree_raw2staging.py` | GraphQL JSON → CSV + Parquet in curated                   |

Each extractor writes to `landing/<platform>` and each cleaner reads from one zone and writes to the next. The cron job (`cronjob/run_datalake_cron.bat`) iterates over every directory under `src/` and executes all scripts found in `extractors` and `cleaners` automatically【F:cronjob/run_datalake_cron.bat†L24-L54】.

## Service Integration Template

1. **Create directories**
   ```bash
   src/<service>/extractors/
   src/<service>/cleaners/
   src/<service>/cookies/        # optional
   ```
   Add a short `README.md` describing the data source.

2. **Extraction script skeleton** (`src/<service>/extractors/<service>_extract.py`)
   ```python
   import os
   from pathlib import Path
   from dotenv import load_dotenv
   from playwright.sync_api import sync_playwright

   load_dotenv()
   PROJECT_ROOT = Path(os.environ["PROJECT_ROOT"])
   OUTPUT_DIR = PROJECT_ROOT / "landing" / "<service>"
   OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

   def run(playwright):
       # implement login and download logic
       pass

   if __name__ == "__main__":
       with sync_playwright() as p:
           run(p)
   ```
   Store credentials in `.env` (e.g. `<SERVICE>_USER`, `<SERVICE>_PASS`).

3. **Cleaner scripts** – follow [`LLM_cleaner_guidelines.md`](../src/LLM_cleaner_guidelines.md) for naming and structure:
   - `<service>_landing2raw.py`
   - `<service>_raw2staging.py`
   - `<service>_staging2curated.py`

   Each script should:
   - Read from `PROJECT_ROOT` paths (e.g., `landing/<service>/`, `raw/<service>/`).
   - Use `# %%` cell markers and minimal `print` logging.
   - Provide a CLI (`--file`, `--out`, or `--input` as appropriate).
   - Write UTF‑8 CSV or NDJSON files.

4. **Automatic registration** – No manual imports are required. The cron job loops over every folder under `src/` and runs `extractors/*.py` then `cleaners/*.py`. Simply placing your scripts in the correct sub‑directories registers them.

5. **Testing** – add placeholder tests under `tests/<service>/` and run `pytest -q --cov=src` to ensure nothing breaks.

## Example: Adding `ExampleAPI`

1. **Scaffold folders**
   ```bash
   mkdir -p src/exampleapi/extractors src/exampleapi/cleaners src/exampleapi/cookies
   mkdir -p tests/exampleapi
   ```

2. **Extractor** (`src/exampleapi/extractors/exampleapi_extract.py`)
   ```python
   """Download data from ExampleAPI into the landing zone."""
   import os
   from pathlib import Path
   from dotenv import load_dotenv
   import requests

   load_dotenv()
   PROJECT_ROOT = Path(os.environ["PROJECT_ROOT"])
   API_TOKEN = os.environ.get("EXAMPLEAPI_TOKEN")
   OUTPUT_DIR = PROJECT_ROOT / "landing" / "exampleapi"
   OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

   def run():
       resp = requests.get("https://example.com/api", headers={"Authorization": f"Bearer {API_TOKEN}"})
       resp.raise_for_status()
       out = OUTPUT_DIR / "exampleapi_raw.json"
       out.write_text(resp.text, encoding="utf-8")
       print(f"[INFO] Saved → {out}")

   if __name__ == "__main__":
       run()
   ```

3. **Cleaners** (`src/exampleapi/cleaners/exampleapi_landing2raw.py`, etc.)
   Follow the template in `LLM_cleaner_guidelines.md` to validate the raw JSON, convert to NDJSON, then build a staging CSV and curated CSV.

4. **Add tests** (`tests/exampleapi/test_placeholder.py`)
   ```python
   def test_placeholder():
       assert True
   ```

5. **Run tests**
   ```bash
   pip install -r requirements.txt
   pytest -q --cov=src
   ```
   Ensure all tests pass before committing.

With these steps a new service becomes part of the automated data lake. The cron job detects the new folder and executes its extractor and cleaner scripts on the next scheduled run.
