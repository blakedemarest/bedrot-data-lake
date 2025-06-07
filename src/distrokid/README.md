# DistroKid ETL

Scripts to download and process streaming and sales data from DistroKid.

## Layout
- `extractors/` – Playwright automation for logging in and fetching HTML or TSV files.
- `cleaners/` – Validation and promotion steps for landing → raw → staging → curated.

Example extraction:
```bash
python extractors/dk_auth.py
```
