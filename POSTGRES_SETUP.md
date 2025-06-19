# PostgreSQL Database Setup Guide

Complete step-by-step instructions for setting up the BEDROT Data Lake PostgreSQL analytics system.

---

## Quick Start with Docker (Preferred)

The easiest and most reproducible way to get the BEDROT analytics database running is via Docker. Containers spin up Postgres, pgAdmin (optional), and the ETL runner that loads your curated CSVs.

```bash
# 1. Ensure you are inside the repository root
# 2. Copy the env template and edit credentials/paths
cp postgres_etl/.env.example postgres_etl/.env

# 3. Start Postgres in the background (creates volume `postgres_data`)
docker compose up -d postgres

# 4. Initialise the database schema and users
#    (Runs init_db.py inside the ETL container and exits)
docker compose run --rm etl_runner python init_db.py

# 5. Run the full ETL pipeline
#    --profile etl ensures only the ETL container starts in stream mode
docker compose --profile etl up

# 6. (Optional) Launch pgAdmin UI at http://localhost:8080
docker compose --profile admin up -d pgadmin
```

Volumes mounted:
* `postgres_data` – persistent Postgres data directory
* `./postgres_etl/logs` – ETL logs on host
* `../` (entire repo) – mounted read-only at `/workspace/data_lake` inside `etl_runner`

`CURATED_DATA_PATH` defaults to `/workspace/data_lake/curated`, but you can override it in `.env`.

Shutdown and clean up everything (including volumes):
```bash
docker compose down -v
```

---

## Prerequisites

- Windows 10/11 with WSL2 (you're already using this)
- Python 3.8+ installed
- Git (already installed)

## Appendix: Manual PostgreSQL Installation (No Docker)

### Option A: Install PostgreSQL on Windows (Recommended)

1. **Download PostgreSQL Installer**
   - Go to https://www.postgresql.org/download/windows/
   - Download the latest version (15.x or 16.x)
   - Run the installer as Administrator

2. **Installation Settings**
   - Choose installation directory: `C:\Program Files\PostgreSQL\16`
   - Select components: PostgreSQL Server, pgAdmin 4, Command Line Tools
   - Data directory: `C:\Program Files\PostgreSQL\16\data`
   - **Set superuser password** (remember this - you'll need it!)
   - Port: `5432` (default)
   - Locale: Default

3. **Verify Installation**
   ```cmd
   # Open Command Prompt as Administrator
   cd "C:\Program Files\PostgreSQL\16\bin"
   psql --version
   ```

### Option B: Install PostgreSQL on WSL2 (Alternative)

```bash
# Update package list
sudo apt update

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo service postgresql start

# Set password for postgres user
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'your_password';"
```

## Step 2: Configure Environment

1. **Navigate to the postgres_etl directory**
   ```bash
   cd "/mnt/c/Users/Earth/BEDROT PRODUCTIONS/BEDROT DATA LAKE/data_lake/postgres_etl"
   ```

2. **Create environment configuration**
   ```bash
   cp .env.example .env
   ```

3. **Edit the .env file** (use `nano .env` or your preferred editor)
   ```env
   # PostgreSQL Connection Settings
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=bedrot_analytics
   
   # Application Database User (will be created)
   POSTGRES_USER=bedrot_app
   POSTGRES_PASSWORD=SecurePassword123!
   
   # Admin User (your PostgreSQL superuser)
   POSTGRES_ADMIN_USER=postgres
   POSTGRES_ADMIN_PASSWORD=YourPostgresPassword
   
   # ETL Configuration
   CURATED_DATA_PATH=/mnt/c/Users/Earth/BEDROT PRODUCTIONS/BEDROT DATA LAKE/data_lake/curated
   BATCH_SIZE=1000
   LOG_LEVEL=INFO
   ```

   **Important**: Replace `YourPostgresPassword` with the password you set during PostgreSQL installation.

## Step 3: Install Python Dependencies

```bash
# Install required Python packages
pip3 install -r requirements.txt

# If you get permission errors, try:
pip3 install --user -r requirements.txt
```

## Step 4: Initialize the Database

```bash
# Run the database initialization script
python3 init_db.py
```

**Expected Output:**
```
2024-06-18 10:30:15 - INFO - Created database: bedrot_analytics
2024-06-18 10:30:15 - INFO - Created user: bedrot_app
2024-06-18 10:30:15 - INFO - Granted privileges to bedrot_app
2024-06-18 10:30:16 - INFO - Applied database schema successfully
2024-06-18 10:30:16 - INFO - Database verification successful. data_sources table has 0 rows
2024-06-18 10:30:16 - INFO - Database initialization completed successfully!
```

## Step 5: Test the ETL Pipeline

```bash
# Run the ETL pipeline to process your curated data
python3 etl_pipeline.py
```

**Expected Output:**
```
2024-06-18 10:35:22 - INFO - Starting full ETL pipeline...
2024-06-18 10:35:22 - INFO - Found 6 CSV files to process
2024-06-18 10:35:22 - INFO - Processing file: curated/tidy_daily_streams.csv
2024-06-18 10:35:22 - INFO - Registered new data source: curated_tidy_daily_streams
2024-06-18 10:35:23 - INFO - Successfully processed 150 records from curated/tidy_daily_streams.csv
...
2024-06-18 10:35:30 - INFO - ETL pipeline completed. Results: {'files_processed': 6, 'total_records': 892, 'errors': 0}

ETL Pipeline Results:
Files processed: 6
Total records: 892
Errors: 0
```

## Step 6: Verify Your Data

### Option A: Using Command Line

```bash
# Connect to your database
psql -h localhost -U bedrot_app -d bedrot_analytics

# Once connected, run these queries:
```

```sql
-- Check data sources
SELECT source_name, row_count, last_ingested_at 
FROM bedrot_analytics.data_sources;

-- View streaming data
SELECT date_recorded, artist_name, platform, spotify_streams, combined_streams 
FROM bedrot_analytics.streaming_insights 
ORDER BY date_recorded DESC 
LIMIT 10;

-- View social media data  
SELECT date_recorded, platform, total_views, total_clicks, click_through_rate
FROM bedrot_analytics.social_insights
WHERE total_views > 0
LIMIT 10;

-- View advertising data
SELECT date_recorded, campaign_name, spend, impressions, cost_per_click
FROM bedrot_analytics.advertising_insights
WHERE spend > 0
LIMIT 10;

-- Exit
\q
```

### Option B: Using pgAdmin (GUI)

1. **Open pgAdmin**
   - Windows: Start Menu → pgAdmin 4
   - Or visit: http://localhost:5050 (if using Docker)

2. **Connect to Server**
   - Right-click "Servers" → Create → Server
   - Name: `BEDROT Analytics`
   - Host: `localhost`
   - Port: `5432`
   - Database: `bedrot_analytics`
   - Username: `bedrot_app`
   - Password: `SecurePassword123!` (your password from .env)

3. **Explore Your Data**
   - Navigate: Servers → BEDROT Analytics → Databases → bedrot_analytics → Schemas → bedrot_analytics
   - Tables: `data_sources`, `insights`
   - Views: `streaming_insights`, `social_insights`, `advertising_insights`

## Step 7: Set Up Automated Running (Optional)

### Create a batch file for easy execution:

```bash
# Create a Windows batch file
cat > "/mnt/c/Users/Earth/BEDROT PRODUCTIONS/BEDROT DATA LAKE/data_lake/run_etl.bat" << 'EOF'
@echo off
cd /d "C:\Users\Earth\BEDROT PRODUCTIONS\BEDROT DATA LAKE\data_lake\postgres_etl"
wsl python3 etl_pipeline.py
pause
EOF
```

Now you can double-click `run_etl.bat` from Windows Explorer to run the ETL pipeline.

## Troubleshooting

### Common Issues

**1. Connection refused**
```
psycopg2.OperationalError: connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused
```
**Solution**: Ensure PostgreSQL service is running
```bash
# Windows
net start postgresql-x64-16

# WSL2
sudo service postgresql start
```

**2. Authentication failed**
```
psycopg2.OperationalError: FATAL: password authentication failed for user "postgres"
```
**Solution**: Check your password in the `.env` file matches your PostgreSQL installation.

**3. Permission denied**
```
psycopg2.errors.InsufficientPrivilege: permission denied for schema public
```
**Solution**: Re-run `python3 init_db.py` to fix permissions.

**4. Module not found**
```
ModuleNotFoundError: No module named 'pandas'
```
**Solution**: Install dependencies: `pip3 install -r requirements.txt`

**5. No CSV files found**
```
INFO - Found 0 CSV files to process
```
**Solution**: Check the `CURATED_DATA_PATH` in your `.env` file points to the correct directory.

### Checking Service Status

**Windows:**
```cmd
# Check if PostgreSQL is running
sc query postgresql-x64-16
```

**WSL2:**
```bash
# Check PostgreSQL status
sudo service postgresql status

# Start if not running
sudo service postgresql start
```

### Logs and Debugging

```bash
# View detailed logs
tail -f /var/log/postgresql/postgresql-*.log

# Test database connection
python3 -c "
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    dbname=os.getenv('POSTGRES_DB')
)
print('✅ Connection successful!')
conn.close()
"
```

## Next Steps

Once your database is set up and running:

1. **Schedule Regular ETL Runs**: Add the ETL script to your existing cron jobs
2. **Create Custom Queries**: Write SQL queries for specific business insights
3. **Build Dashboards**: Connect tools like Grafana, Tableau, or Power BI
4. **Monitor Performance**: Set up alerts for data quality and pipeline failures

## Docker Alternative (If You Prefer Containers)

If you prefer to use Docker instead of installing PostgreSQL directly:

```bash
# Start PostgreSQL in Docker
docker-compose up postgres -d

# Initialize database
docker-compose run --rm etl_runner python3 init_db.py

# Run ETL pipeline
docker-compose --profile etl up

# Access pgAdmin at http://localhost:8080
docker-compose --profile admin up pgadmin -d
```

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Verify all environment variables in `.env` are correct
3. Ensure PostgreSQL service is running
4. Test database connectivity before running ETL

Your PostgreSQL analytics database is now ready to store and analyze your BEDROT Data Lake insights! 🎉