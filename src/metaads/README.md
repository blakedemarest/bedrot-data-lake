# Meta Ads ETL

Tools for dumping Meta Ads API data and cleaning it for analytics.

## Layout
- `extractors/` – Downloads campaigns, ad sets, ads, and insights to `landing/metaads/<timestamp>`.
- `cleaners/` – Validates dumps and normalizes them through raw and staging zones.
