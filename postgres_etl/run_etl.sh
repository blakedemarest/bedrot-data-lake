#!/bin/bash
# BEDROT Data Lake ETL Runner Script
# Convenience script to run the complete ETL pipeline

set -e

echo "🎯 BEDROT Data Lake PostgreSQL ETL Pipeline"
echo "==========================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found! Please copy .env.example to .env and configure it."
    exit 1
fi

# Load environment variables
source .env

# Check if Python dependencies are installed
echo "📦 Checking Python dependencies..."
python3 -c "import pandas, psycopg2, dotenv" 2>/dev/null || {
    echo "📥 Installing Python dependencies..."
    pip3 install -r requirements.txt
}

# Check database connection
echo "🔗 Checking database connection..."
python3 -c "
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()
try:
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        dbname=os.getenv('POSTGRES_DB')
    )
    conn.close()
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    print('💡 Run: python3 init_db.py to initialize the database')
    exit(1)
"

# Run ETL pipeline
echo "🚀 Running ETL pipeline..."
python3 etl_pipeline.py

echo "✅ ETL pipeline completed successfully!"
echo ""
echo "🔍 To view your data:"
echo "  - Connect to PostgreSQL and query bedrot_analytics.insights"
echo "  - Use the predefined views: streaming_insights, social_insights, advertising_insights"
echo "  - Or start pgAdmin: docker-compose --profile admin up pgadmin"