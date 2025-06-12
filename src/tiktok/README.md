# TikTok ETL

Extractors and cleaners for TikTok analytics data.

## Layout
- `extractors/` – Account-specific Playwright scripts that save analytics to `landing/tiktok/`.
- `cleaners/` – Promote and standardize the JSON files.
- `cookies/` – Stored login cookies used by Playwright sessions.
