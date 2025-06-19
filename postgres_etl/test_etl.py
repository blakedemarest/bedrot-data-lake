#!/usr/bin/env python3
"""
Test script for BEDROT Data Lake PostgreSQL ETL System.
Validates the ETL pipeline functionality without requiring full database setup.
"""

import sys
import tempfile
import csv
from pathlib import Path
from datetime import date, datetime
import pandas as pd

# Import our ETL components
from etl_pipeline import DataTypeDetector, DataCleaner, ETLPipeline

def test_data_type_detection():
    """Test data type detection logic."""
    print("Testing data type detection...")
    
    # Test streaming data
    streaming_columns = ['date', 'spotify_streams', 'apple_streams', 'combined_streams']
    assert DataTypeDetector.detect_metric_type(streaming_columns, 'tidy_daily_streams.csv') == 'streams'
    
    # Test social media data
    social_columns = ['date', 'totalViews', 'uniqueViews', 'totalClicks']
    assert DataTypeDetector.detect_metric_type(social_columns, 'linktree/analytics.csv') == 'views'
    
    # Test advertising data
    ad_columns = ['campaign_id', 'spend', 'impressions', 'clicks', 'cpc']
    assert DataTypeDetector.detect_metric_type(ad_columns, 'metaads/campaigns.csv') == 'advertising'
    
    print("✅ Data type detection tests passed")

def test_platform_extraction():
    """Test platform name extraction."""
    print("Testing platform extraction...")
    
    assert DataTypeDetector.extract_platform('linktree/analytics.csv', {}) == 'linktree'
    assert DataTypeDetector.extract_platform('tiktok/data.csv', {}) == 'tiktok'
    assert DataTypeDetector.extract_platform('metaads/campaigns.csv', {}) == 'meta'
    assert DataTypeDetector.extract_platform('distrokid/streams.csv', {}) == 'distrokid'
    
    # Test source field extraction
    assert DataTypeDetector.extract_platform('unknown.csv', {'source': 'spotify'}) == 'spotify'
    
    print("✅ Platform extraction tests passed")

def test_data_cleaning():
    """Test data cleaning functionality."""
    print("Testing data cleaning...")
    
    # Test numeric conversion
    dirty_data = {
        'spend': '129.20',
        'impressions': '762562',
        'rate': '0.415573',
        'text_field': 'campaign_name',
        'empty_field': ''
    }
    
    cleaned = DataCleaner.clean_numeric_fields(dirty_data)
    assert cleaned['spend'] == 129.20
    assert cleaned['impressions'] == 762562
    assert cleaned['rate'] == 0.415573
    assert cleaned['text_field'] == 'campaign_name'
    
    print("✅ Data cleaning tests passed")

def test_date_parsing():
    """Test date parsing functionality."""
    print("Testing date parsing...")
    
    # Test various date formats
    test_cases = [
        {'date': '2024-08-23'},
        {'date_recorded': '2024-12-01'},
        {'date_start': '2025-01-20T09:43:00-0800'},
        {'created_time': '2025-01-17T08:24:18-0800'}
    ]
    
    for test_data in test_cases:
        parsed_date = DataCleaner.parse_date_field(test_data)
        assert isinstance(parsed_date, date)
        assert parsed_date.year >= 2024
    
    print("✅ Date parsing tests passed")

def test_csv_discovery():
    """Test CSV file discovery in a temporary directory."""
    print("Testing CSV file discovery...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test CSV files
        (temp_path / 'test1.csv').touch()
        (temp_path / 'subdir').mkdir()
        (temp_path / 'subdir' / 'test2.csv').touch()
        (temp_path / 'not_csv.txt').touch()
        
        # Test discovery
        etl = ETLPipeline(curated_dir=str(temp_path))
        csv_files = etl.discover_csv_files()
        
        assert len(csv_files) == 2
        csv_names = [f.name for f in csv_files]
        assert 'test1.csv' in csv_names
        assert 'test2.csv' in csv_names
    
    print("✅ CSV discovery tests passed")

def create_test_csv():
    """Create a sample CSV file for integration testing."""
    print("Creating test CSV file...")
    
    test_data = [
        {'date': '2024-08-23', 'spotify_streams': 40, 'apple_streams': 0, 'combined_streams': 40, 'source': 'distrokid'},
        {'date': '2024-08-24', 'spotify_streams': 17, 'apple_streams': 0, 'combined_streams': 17, 'source': 'distrokid'},
        {'date': '2024-08-25', 'spotify_streams': 6, 'apple_streams': 0, 'combined_streams': 6, 'source': 'distrokid'}
    ]
    
    test_file = Path(__file__).parent / 'test_streaming_data.csv'
    
    with open(test_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=test_data[0].keys())
        writer.writeheader()
        writer.writerows(test_data)
    
    print(f"✅ Created test CSV: {test_file}")
    return test_file

def run_integration_test():
    """Run a basic integration test without database."""
    print("Running integration test...")
    
    # Create test CSV
    test_file = create_test_csv()
    
    try:
        # Test CSV processing logic (without database insertion)
        df = pd.read_csv(test_file)
        assert len(df) == 3
        
        # Test data type detection on real file
        columns = df.columns.tolist()
        metric_type = DataTypeDetector.detect_metric_type(columns, str(test_file))
        assert metric_type == 'streams'
        
        # Test row processing
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            cleaned_data = DataCleaner.clean_numeric_fields(row_dict)
            date_recorded = DataCleaner.parse_date_field(cleaned_data)
            platform = DataTypeDetector.extract_platform(str(test_file), cleaned_data)
            
            assert isinstance(cleaned_data['spotify_streams'], int)
            assert isinstance(date_recorded, date)
            assert platform == 'distrokid'
        
        print("✅ Integration test passed")
        
    finally:
        # Clean up test file
        if test_file.exists():
            test_file.unlink()
            print("🧹 Cleaned up test file")

def main():
    """Run all tests."""
    print("🧪 Starting BEDROT ETL System Tests\n")
    
    try:
        test_data_type_detection()
        test_platform_extraction() 
        test_data_cleaning()
        test_date_parsing()
        test_csv_discovery()
        run_integration_test()
        
        print("\n🎉 All tests passed! The ETL system is ready to use.")
        print("\nNext steps:")
        print("1. Set up your .env file with database credentials")
        print("2. Run 'python init_db.py' to initialize the database")
        print("3. Run 'python etl_pipeline.py' to process your curated data")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()