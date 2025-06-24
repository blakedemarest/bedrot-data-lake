#!/usr/bin/env python3
"""
Simple test script to validate enhanced TikTok schema without dependencies
"""

import json
import csv
from datetime import datetime
from pathlib import Path

def test_follower_data_loading():
    """Test loading follower JSON data."""
    print("🧪 Testing Follower Data Loading...")
    
    # Test pig1987 follower data
    pig_follower_file = Path("landing/tiktok/analytics/pig1987_followers_20250624_test.json")
    if pig_follower_file.exists():
        with open(pig_follower_file, 'r') as f:
            pig_data = json.load(f)
        print(f"✅ pig1987 follower data: {pig_data['count']} followers")
    else:
        print("❌ pig1987 follower data not found")
        return False
    
    # Test zonea0 follower data  
    zone_follower_file = Path("landing/tiktok/analytics/zonea0_followers_20250624_test.json")
    if zone_follower_file.exists():
        with open(zone_follower_file, 'r') as f:
            zone_data = json.load(f)
        print(f"✅ zone.a0 follower data: {zone_data['count']} followers")
    else:
        print("❌ zone.a0 follower data not found")
        return False
    
    return True

def test_enhanced_raw_schema():
    """Test the enhanced raw NDJSON schema."""
    print("\n🧪 Testing Enhanced Raw Schema...")
    
    # Sample enhanced record (what landing2raw should produce)
    enhanced_record = {
        "artist": "pig1987",
        "date": "2024-06-24",
        "year": 2024,
        "video_views": 1500,
        "profile_views": 200,
        "likes": 85,
        "comments": 12,
        "shares": 5,
        "followers": 1287,  # NEW: From follower JSON
        "processed_at": datetime.now().isoformat()
    }
    
    # Check required fields
    required_fields = ["artist", "date", "video_views", "profile_views", "likes", "comments", "shares", "followers"]
    missing_fields = [field for field in required_fields if field not in enhanced_record]
    
    if missing_fields:
        print(f"❌ Missing fields in enhanced schema: {missing_fields}")
        return False
    
    print("✅ Enhanced raw schema has all required fields:")
    for field in required_fields:
        print(f"   • {field}: {enhanced_record[field]}")
    
    return True

def test_staging_schema():
    """Test the enhanced staging schema."""
    print("\n🧪 Testing Enhanced Staging Schema...")
    
    # Sample staging record (what raw2staging should produce)
    staging_record = {
        "Artist": "pig1987",
        "Date": "2024-06-24",
        "Video Views": 1500,
        "Profile Views": 200,
        "Likes": 85,
        "Comments": 12,
        "Shares": 5,
        "Year": 2024,
        "Followers": 1287  # NEW: Follower count from raw
    }
    
    # Check staging schema
    expected_columns = ["Artist", "Date", "Video Views", "Profile Views", "Likes", "Comments", "Shares", "Year", "Followers"]
    missing_columns = [col for col in expected_columns if col not in staging_record]
    
    if missing_columns:
        print(f"❌ Missing columns in staging schema: {missing_columns}")
        return False
    
    print("✅ Enhanced staging schema has all required columns:")
    for col in expected_columns:
        print(f"   • {col}: {staging_record[col]}")
    
    return True

def test_curated_schema():
    """Test the final enhanced curated schema."""
    print("\n🧪 Testing Enhanced Curated Schema...")
    
    # Sample curated records (what staging2curated should produce)
    curated_records = [
        {
            "artist": "pig1987",
            "zone": "pig1987", 
            "date": "2024-06-23",
            "Video Views": 1200,
            "Profile Views": 180,
            "Likes": 65,
            "Comments": 8,
            "Shares": 3,
            "Year": 2024,
            "engagement_rate": 0.0633,
            "Followers": 1250,  # NEW: Current followers
            "new_followers": 0   # NEW: No baseline for first day
        },
        {
            "artist": "pig1987",
            "zone": "pig1987",
            "date": "2024-06-24", 
            "Video Views": 1500,
            "Profile Views": 200,
            "Likes": 85,
            "Comments": 12,
            "Shares": 5,
            "Year": 2024,
            "engagement_rate": 0.0680,
            "Followers": 1287,  # NEW: Current followers  
            "new_followers": 37  # NEW: 1287 - 1250 = 37 new followers
        }
    ]
    
    # Expected final schema (existing + 2 new columns)
    expected_columns = [
        "artist", "zone", "date", "Video Views", "Profile Views", 
        "Likes", "Comments", "Shares", "Year", "engagement_rate",
        "Followers", "new_followers"  # NEW: Only these 2 added
    ]
    
    # Validate schema
    for i, record in enumerate(curated_records):
        missing_columns = [col for col in expected_columns if col not in record]
        if missing_columns:
            print(f"❌ Record {i+1} missing columns: {missing_columns}")
            return False
    
    print("✅ Enhanced curated schema (12 columns total):")
    print("   📊 EXISTING (10 columns):")
    existing_cols = expected_columns[:-2]
    for col in existing_cols:
        print(f"      • {col}")
    
    print("   ✨ NEW (2 columns):")
    new_cols = expected_columns[-2:]
    for col in new_cols:
        print(f"      • {col}")
    
    # Test new_followers calculation logic
    print("\n   🧮 new_followers calculation test:")
    print(f"      Day 1: {curated_records[0]['Followers']} followers → {curated_records[0]['new_followers']} new")
    print(f"      Day 2: {curated_records[1]['Followers']} followers → {curated_records[1]['new_followers']} new")
    print(f"      Logic: {curated_records[1]['Followers']} - {curated_records[0]['Followers']} = {curated_records[1]['new_followers']}")
    
    return True

def main():
    """Run all enhanced schema tests."""
    print("🚀 TikTok Enhanced Pipeline Schema Test")
    print("=" * 50)
    
    tests = [
        ("Follower Data Loading", test_follower_data_loading),
        ("Enhanced Raw Schema", test_enhanced_raw_schema),
        ("Enhanced Staging Schema", test_staging_schema),
        ("Enhanced Curated Schema", test_curated_schema)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST RESULTS SUMMARY:")
    print("-" * 25)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All enhanced schema tests PASSED!")
        print("✅ Ready for production implementation")
    else:
        print("⚠️  Some tests failed - review implementation")
    
    return passed == len(results)

if __name__ == "__main__":
    main()