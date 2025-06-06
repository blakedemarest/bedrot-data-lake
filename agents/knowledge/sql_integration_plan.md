# SQL Integration Plan for Curated and Archived Data

## Objective
Extend the BEDROT Data Lake so curated and archived CSVs are loaded into a Postgres database.  The database will serve as a relational layer on top of the existing zone-based storage.

## Current Curated Outputs
Based on the `*_staging2curated.py` scripts:

- `tidy_daily_streams.csv` – combined daily streams from DistroKid and TooLost.  Columns include `date`, numeric streaming metrics, and a `source` flag distinguishing platforms.
- `metaads_campaigns_daily.csv` – Meta Ads insights joined with campaign/adset data.  Key fields: `date_start`, `ad_id`, `adset_id`, `campaign_id`, metrics such as `spend` and `impressions`.
- `dk_bank_details.csv` – exported from DistroKid cleaner, listing payment account details.

Archived versions of these files are stored in `/archive` with timestamps appended.

## Database Modeling
Each curated CSV maps to a base table.  Archived snapshots use the same schema with an `_archive` suffix.

| CSV File | Curated Table | Archive Table |
|----------|---------------|---------------|
| `tidy_daily_streams.csv` | `daily_streams` | `daily_streams_archive` |
| `metaads_campaigns_daily.csv` | `metaads_campaigns_daily` | `metaads_campaigns_daily_archive` |
| `dk_bank_details.csv` | `dk_bank_details` | `dk_bank_details_archive` |

**Shared Keys**
- `date` or `date_start` (timestamp)
- Entity identifiers (`ad_id`, `campaign_id`, etc.)
- `source` when multiple platforms contribute to the same table

Surrogate integer IDs (`serial`/`bigserial`) can be added for relational joins, but natural keys will remain to enforce deduplication.

## Relational Linking Strategy
1. **Curated–Archive Relationship**
   - Each archive table mirrors the curated schema plus `archived_at TIMESTAMP` to record when the snapshot was taken.
   - Primary key matches the curated table (e.g., `date, source` for `daily_streams`).
   - Archive rows reference curated records via these natural keys to avoid duplication.
2. **Version Tracking**
   - Maintain a small `dataset_versions` table:
     - `table_name`
     - `snapshot_time`
     - `file_hash`
   - This enables lineage queries and rollback.

## Loading Strategy
A loader utility (`src/utils/sql_loader.py`) will:

1. Iterate over CSVs in `curated/` and `archive/`.
2. Use SQLAlchemy (with psycopg2 engine) to batch load into the appropriate table.
3. Record each ingestion in `agents/knowledge/sql_ingestion_log.md` with timestamp, row count, and file hash.
4. Optionally run `CREATE INDEX` statements for key columns if the table is new.

Pseudo-code outline:
```python
for csv_path in CURATED.glob('*.csv'):
    table = csv_path.stem
    load_csv_to_table(csv_path, table)

for csv_path in ARCHIVE.glob('*.csv'):
    table = f"{csv_path.stem}_archive"
    load_csv_to_table(csv_path, table, add_snapshot=True)
```

## Performance and Indexing
- Use `COPY FROM` or SQLAlchemy bulk inserts for efficiency.
- Index date columns (`date`, `date_start`) and high-cardinality identifiers (`ad_id`, `campaign_id`).
- Partition large archive tables by year or month if row counts grow substantially.

## Schema Compatibility
- Cleaner scripts must enforce stable column order and types before loading.
- Use `CREATE TABLE IF NOT EXISTS` with explicit column definitions that match the CSVs.
- When schemas evolve, version the table (e.g., `daily_streams_v2`) and document differences in the knowledge base.

## Sample Queries
- Join curated and archived data for change history:
```sql
SELECT c.*, a.archived_at
FROM daily_streams c
JOIN daily_streams_archive a
  ON c.date = a.date AND c.source = a.source
WHERE c.source = 'distrokid' AND c.date >= '2025-01-01';
```
- Retrieve the latest Meta Ads metrics for a campaign:
```sql
SELECT *
FROM metaads_campaigns_daily
WHERE campaign_id = '12345'
ORDER BY date_start DESC
LIMIT 1;
```

## Edge Cases
- **Schema Drift**: if a new column appears in a curated CSV, the loader should log a warning and add the column to the table if allowed.
- **Duplicate Records**: natural keys plus constraints will prevent double inserts.
- **Large Archives**: consider periodic compression or moving old partitions to cheaper storage.

## Next Steps
1. Implement `sql_loader.py` according to this plan.
2. Configure database credentials via `.env` (e.g., `DB_URL`).
3. Automate nightly loads via cronjob after cleaner scripts run.
4. Update documentation as schemas evolve.
