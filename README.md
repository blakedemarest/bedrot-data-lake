# BEDROT Data Lake

This is the central data lake for BEDROT's music analytics platform.

## Directory Structure

- `.agent/` - AI agent working directories
  - `cache/` - Temporary processing artifacts
  - `context/` - Session-specific context
  - `logs/` - Agent execution logs
- `landing/` - Initial data ingestion area
- `raw/` - Immutable raw data
- `staging/` - Cleaned and validated data
- `curated/` - Business-ready datasets
- `archive/` - Historical data archives
- `sandbox/` - Experimental work area
- `knowledge/` - AI knowledge base
  - `decisions/` - Decision records
  - `patterns/` - Common data patterns
  - `agents/` - Agent-specific knowledge

## Getting Started with MinIO

1. **Prerequisites**
   - Docker and Docker Compose installed
   - Ports 9000 and 9001 available

2. **Start MinIO**
   ```bash
   docker-compose up -d
   ```

3. **Access MinIO Console**
   - URL: http://localhost:9001
   - Username: admin
   - Password: your_secure_password

4. **Create Buckets**
   After logging in, create the following buckets:
   - landing
   - raw
   - staging
   - curated
   - archive
   - sandbox

## Environment Variables

Update `.env` with your preferred credentials before starting MinIO.

## Data Flow

1. Data lands in the `landing` zone
2. Processed to `raw` (immutable)
3. Cleaned in `staging`
4. Business-ready in `curated`
5. Archived to `archive` when no longer actively used
