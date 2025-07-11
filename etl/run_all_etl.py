"""
BEDROT Data Warehouse - Master ETL Orchestrator
Runs all ETL pipelines in proper sequence to populate the data warehouse.
"""

import sys
from pathlib import Path
from datetime import datetime

# Set up paths for both data_lake and warehouse ETL scripts
DATA_LAKE_PATH = Path(__file__).parent.parent
ECOSYSTEM_ROOT = DATA_LAKE_PATH.parent
WAREHOUSE_PATH = ECOSYSTEM_ROOT / "data-warehouse"

# Import data_lake ETL modules first (existing ETLs)
from etl_master_data import run_master_data_etl
from etl_streaming_performance import run_streaming_performance_etl
from etl_social_media_performance import run_social_media_etl

# Add warehouse path and import warehouse ETL modules (new ETLs)
sys.path.insert(0, str(WAREHOUSE_PATH))
from etl_financial_data_fixed import run_financial_etl
from etl_daily_streams import run_daily_streams_etl
from etl_advertising_performance import run_advertising_etl
from etl_link_analytics import run_link_analytics_etl
from etl_submithub_analytics import run_submithub_analytics_etl

def run_complete_etl_pipeline():
    """Run all ETL pipelines in proper dependency order."""
    
    print("=" * 60)
    print("🚀 BEDROT DATA WAREHOUSE - COMPLETE ETL PIPELINE")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success_count = 0
    total_pipelines = 8
    
    # Stage 1: Master Data (Artists, Platforms, Tracks)
    print("📋 STAGE 1: MASTER DATA")
    print("-" * 30)
    try:
        if run_master_data_etl():
            print("✅ Master Data ETL completed successfully")
            success_count += 1
        else:
            print("❌ Master Data ETL failed")
            return False
    except Exception as e:
        print(f"❌ Master Data ETL error: {e}")
        return False
    
    print()
    
    # Stage 2: Financial Data
    print("📋 STAGE 2: FINANCIAL DATA")
    print("-" * 30)
    try:
        if run_financial_etl():
            print("✅ Financial Data ETL completed successfully")
            success_count += 1
        else:
            print("⚠️ Financial Data ETL completed with warnings")
            success_count += 1  # Continue even if no financial data found
    except Exception as e:
        print(f"❌ Financial Data ETL error: {e}")
        print("⚠️ Continuing with remaining pipelines...")
    
    print()
    
    # Stage 3: Streaming Performance
    print("📋 STAGE 3: STREAMING PERFORMANCE")
    print("-" * 30)
    try:
        if run_streaming_performance_etl():
            print("✅ Streaming Performance ETL completed successfully")
            success_count += 1
        else:
            print("❌ Streaming Performance ETL failed")
    except Exception as e:
        print(f"❌ Streaming Performance ETL error: {e}")
    
    print()
    
    # Stage 4: Social Media Performance
    print("📋 STAGE 4: SOCIAL MEDIA PERFORMANCE")
    print("-" * 30)
    try:
        if run_social_media_etl():
            print("✅ Social Media Performance ETL completed successfully")
            success_count += 1
        else:
            print("❌ Social Media Performance ETL failed")
    except Exception as e:
        print(f"❌ Social Media Performance ETL error: {e}")
    
    print()
    
    # Stage 5: Daily Streaming Data
    print("📋 STAGE 5: DAILY STREAMING DATA")
    print("-" * 30)
    try:
        if run_daily_streams_etl():
            print("✅ Daily Streaming ETL completed successfully")
            success_count += 1
        else:
            print("❌ Daily Streaming ETL failed")
    except Exception as e:
        print(f"❌ Daily Streaming ETL error: {e}")
    
    print()
    
    # Stage 6: Advertising Performance (Meta Ads)
    print("📋 STAGE 6: ADVERTISING PERFORMANCE")
    print("-" * 30)
    try:
        if run_advertising_etl():
            print("✅ Advertising Performance ETL completed successfully")
            success_count += 1
        else:
            print("❌ Advertising Performance ETL failed")
    except Exception as e:
        print(f"❌ Advertising Performance ETL error: {e}")
    
    print()
    
    # Stage 7: Link Analytics (Linktree)
    print("📋 STAGE 7: LINK ANALYTICS")
    print("-" * 30)
    try:
        if run_link_analytics_etl():
            print("✅ Link Analytics ETL completed successfully")
            success_count += 1
        else:
            print("❌ Link Analytics ETL failed")
    except Exception as e:
        print(f"❌ Link Analytics ETL error: {e}")
    
    print()
    
    # Stage 8: SubmitHub Analytics
    print("📋 STAGE 8: SUBMITHUB ANALYTICS")
    print("-" * 30)
    try:
        if run_submithub_analytics_etl():
            print("✅ SubmitHub Analytics ETL completed successfully")
            success_count += 1
        else:
            print("❌ SubmitHub Analytics ETL failed")
    except Exception as e:
        print(f"❌ SubmitHub Analytics ETL error: {e}")
    
    print()
    print("=" * 60)
    print("📊 ETL PIPELINE SUMMARY")
    print("=" * 60)
    print(f"Completed pipelines: {success_count}/{total_pipelines}")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success_count >= 2:  # At least master data + one other pipeline
        print("🎉 ETL Pipeline completed successfully!")
        return True
    else:
        print("❌ ETL Pipeline failed - insufficient successful stages")
        return False

def show_final_database_summary():
    """Show final summary of loaded data."""
    import sqlite3
    
    # Database connection
    DATA_LAKE_PATH = Path(__file__).parent.parent
    ECOSYSTEM_ROOT = DATA_LAKE_PATH.parent
    WAREHOUSE_PATH = ECOSYSTEM_ROOT / "data-warehouse"
    DB_PATH = WAREHOUSE_PATH / "bedrot_analytics.db"
    
    conn = sqlite3.connect(str(DB_PATH))
    
    try:
        print("\n" + "=" * 60)
        print("📊 FINAL DATABASE SUMMARY")
        print("=" * 60)
        
        # Get record counts
        tables = [
            ('artists', 'Artists'),
            ('tracks', 'Tracks'),
            ('platforms', 'Platforms'),
            ('campaigns', 'Marketing Campaigns'),
            ('financial_transactions', 'Financial Transactions'),
            ('streaming_performance', 'Streaming Performance Records'),
            ('social_media_performance', 'Social Media Performance Records'),
            ('advertising_performance', 'Advertising Performance Records'),
            ('link_analytics', 'Link Analytics Records'),
            ('meta_pixel_events', 'Meta Pixel Events')
        ]
        
        for table_name, display_name in tables:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"{display_name}: {count:,}")
        
        # Show revenue summary if financial data exists
        cursor = conn.execute("SELECT COUNT(*) FROM financial_transactions")
        if cursor.fetchone()[0] > 0:
            cursor = conn.execute("SELECT SUM(amount) FROM financial_transactions WHERE amount > 0")
            revenue = cursor.fetchone()[0] or 0
            cursor = conn.execute("SELECT SUM(ABS(amount)) FROM financial_transactions WHERE amount < 0")
            expenses = cursor.fetchone()[0] or 0
            print(f"\nFinancial Summary:")
            print(f"  Total Revenue: ${revenue:.2f}")
            print(f"  Total Expenses: ${expenses:.2f}")
            print(f"  Net Income: ${revenue - expenses:.2f}")
        
        print("\n🎯 Data warehouse is ready for analytics!")
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = run_complete_etl_pipeline()
    
    if success:
        show_final_database_summary()
        sys.exit(0)
    else:
        sys.exit(1)