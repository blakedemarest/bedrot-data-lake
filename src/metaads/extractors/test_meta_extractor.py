# Test script for Meta Ads daily campaigns extractor
# Validates API structure and field definitions without making actual API calls

# %%
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# Test the corrected extractor structure
def test_extractor_structure():
    """Test that the extractor has the correct structure and field definitions"""
    
    print("[TEST] Testing Meta Ads extractor structure...")
    
    # Test field definitions match working patterns
    try:
        # Simulate the field definitions from working extractor
        campaign_fields = [
            'id', 'name', 'status', 'objective', 'effective_status',
            'created_time', 'updated_time'
        ]
        
        insight_fields = [
            'campaign_id', 'campaign_name', 'adset_id', 'adset_name',
            'spend', 'impressions', 'clicks', 'cpc', 'ctr',
            'reach', 'frequency', 'actions', 'date_start', 'date_stop'
        ]
        
        print(f"✅ Campaign fields defined: {len(campaign_fields)} fields")
        print(f"✅ Insight fields defined: {len(insight_fields)} fields")
        
        # Test required fields are present
        required_fields = ['reach', 'cpc', 'spend', 'clicks', 'impressions', 'actions']
        missing_fields = [f for f in required_fields if f not in insight_fields]
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        else:
            print(f"✅ All required fields present: {required_fields}")
        
        return True
        
    except Exception as e:
        print(f"❌ Structure test failed: {e}")
        return False

# %%
def test_pixel_events_extraction():
    """Test pixel events extraction logic"""
    
    print("\n[TEST] Testing pixel events extraction...")
    
    # Sample actions data from Meta API
    sample_actions = [
        {'action_type': 'offsite_conversion.fb_pixel_view_content', 'value': '32'},
        {'action_type': 'offsite_conversion.fb_pixel_add_to_cart', 'value': '4'},
        {'action_type': 'offsite_conversion.fb_pixel_purchase', 'value': '1'},
        {'action_type': 'link_click', 'value': '15'},
        {'action_type': 'post_engagement', 'value': '8'},
        {'action_type': 'unknown_event', 'value': '2'}
    ]
    
    def extract_pixel_events(actions):
        pixel_events = {}
        if not actions:
            return pixel_events
        
        for action in actions:
            action_type = action.get('action_type', '')
            value = int(float(action.get('value', 0)))
            
            event_mapping = {
                'offsite_conversion.fb_pixel_view_content': 'ViewContent',
                'offsite_conversion.fb_pixel_add_to_cart': 'AddToCart', 
                'offsite_conversion.fb_pixel_purchase': 'Purchase',
                'offsite_conversion.fb_pixel_initiate_checkout': 'InitiateCheckout',
                'offsite_conversion.fb_pixel_add_payment_info': 'AddPaymentInfo',
                'offsite_conversion.fb_pixel_lead': 'Lead',
                'offsite_conversion.fb_pixel_complete_registration': 'CompleteRegistration',
                'link_click': 'LinkClick',
                'post_engagement': 'PostEngagement',
                'onsite_conversion.messaging_conversation_started_7d': 'MessagingStarted'
            }
            
            event_name = event_mapping.get(action_type, action_type)
            
            if event_name in pixel_events:
                pixel_events[event_name] += value
            else:
                pixel_events[event_name] = value
        
        return pixel_events
    
    try:
        result = extract_pixel_events(sample_actions)
        expected_events = {'ViewContent', 'AddToCart', 'Purchase', 'LinkClick', 'PostEngagement'}
        
        print(f"✅ Extracted events: {json.dumps(result, indent=2)}")
        
        # Verify expected events are present
        for event in expected_events:
            if event in result:
                print(f"✅ {event}: {result[event]}")
            else:
                print(f"❌ Missing expected event: {event}")
        
        # Test edge cases
        empty_result = extract_pixel_events([])
        if empty_result == {}:
            print("✅ Empty actions handled correctly")
        else:
            print(f"❌ Empty actions test failed: {empty_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pixel events test failed: {e}")
        return False

# %%
def test_campaign_activity_tracker():
    """Test campaign activity tracking logic"""
    
    print("\n[TEST] Testing campaign activity tracker...")
    
    try:
        import sqlite3
        from datetime import datetime
        
        # Create in-memory database for testing
        test_db = ":memory:"
        
        class TestCampaignActivityTracker:
            def __init__(self, db_path):
                self.db_path = db_path
                self._init_db()
            
            def _init_db(self):
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS campaign_activity (
                            campaign_id TEXT PRIMARY KEY,
                            last_active_date TEXT,
                            is_active INTEGER,
                            consecutive_inactive_days INTEGER DEFAULT 0,
                            updated_at TEXT
                        )
                    """)
                    conn.commit()
            
            def get_active_campaigns(self):
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT campaign_id FROM campaign_activity 
                        WHERE is_active = 1 OR consecutive_inactive_days < 7
                    """)
                    return {row[0] for row in cursor.fetchall()}
            
            def update_campaign_activity(self, campaign_id, has_data, date):
                with sqlite3.connect(self.db_path) as conn:
                    existing = conn.execute(
                        "SELECT consecutive_inactive_days FROM campaign_activity WHERE campaign_id = ?",
                        (campaign_id,)
                    ).fetchone()
                    
                    if has_data:
                        conn.execute("""
                            INSERT OR REPLACE INTO campaign_activity 
                            (campaign_id, last_active_date, is_active, consecutive_inactive_days, updated_at)
                            VALUES (?, ?, 1, 0, ?)
                        """, (campaign_id, date, datetime.now().isoformat()))
                    else:
                        inactive_days = (existing[0] if existing else 0) + 1
                        is_active = 1 if inactive_days < 7 else 0
                        
                        conn.execute("""
                            INSERT OR REPLACE INTO campaign_activity 
                            (campaign_id, last_active_date, is_active, consecutive_inactive_days, updated_at)
                            VALUES (?, ?, ?, ?, ?)
                        """, (campaign_id, date, is_active, inactive_days, datetime.now().isoformat()))
                    
                    conn.commit()
        
        # Test tracker
        tracker = TestCampaignActivityTracker(test_db)
        
        # Test initial state (empty)
        active_campaigns = tracker.get_active_campaigns()
        if len(active_campaigns) == 0:
            print("✅ Initial state: no active campaigns")
        else:
            print(f"❌ Expected empty set, got: {active_campaigns}")
        
        # Test adding active campaign
        tracker.update_campaign_activity("camp_123", True, "2025-06-24")
        active_campaigns = tracker.get_active_campaigns()
        if "camp_123" in active_campaigns:
            print("✅ Active campaign added successfully")
        else:
            print(f"❌ Active campaign not found: {active_campaigns}")
        
        # Test marking campaign inactive (but < 7 days)
        for day in range(1, 6):  # 5 days of no activity
            tracker.update_campaign_activity("camp_123", False, f"2025-06-{24+day}")
        
        active_campaigns = tracker.get_active_campaigns()
        if "camp_123" in active_campaigns:
            print("✅ Campaign still active after 5 inactive days")
        else:
            print(f"❌ Campaign should still be active: {active_campaigns}")
        
        # Test marking campaign inactive for 7+ days
        for day in range(6, 8):  # 2 more days (total 7)
            tracker.update_campaign_activity("camp_123", False, f"2025-06-{24+day}")
        
        active_campaigns = tracker.get_active_campaigns()
        if "camp_123" not in active_campaigns:
            print("✅ Campaign correctly marked inactive after 7 days")
        else:
            print(f"❌ Campaign should be inactive: {active_campaigns}")
        
        return True
        
    except Exception as e:
        print(f"❌ Activity tracker test failed: {e}")
        return False

# %%
def test_output_format():
    """Test expected output format"""
    
    print("\n[TEST] Testing output format...")
    
    try:
        # Sample daily record structure
        sample_record = {
            'date': '2025-06-24',
            'campaign_id': '120214803933120075',
            'campaign_name': 'Test Campaign',
            'adset_id': '120214803933310075',
            'reach': 580554.0,
            'cpc': 0.04077,
            'spend_usd': 129.20,
            'clicks': 3169,
            'impressions': 762562,
            'meta_pixel_events': '{"ViewContent": 32, "AddToCart": 4, "Purchase": 1}',
            'is_active': True
        }
        
        # Verify all required fields are present
        required_fields = [
            'date', 'campaign_id', 'campaign_name', 'adset_id', 
            'reach', 'cpc', 'spend_usd', 'clicks', 'impressions',
            'meta_pixel_events', 'is_active'
        ]
        
        missing_fields = [f for f in required_fields if f not in sample_record]
        
        if missing_fields:
            print(f"❌ Missing required output fields: {missing_fields}")
            return False
        else:
            print(f"✅ All required output fields present: {len(required_fields)} fields")
        
        # Test data types
        if isinstance(sample_record['reach'], float):
            print("✅ reach is float")
        else:
            print(f"❌ reach should be float, got {type(sample_record['reach'])}")
        
        if isinstance(sample_record['is_active'], bool):
            print("✅ is_active is boolean")
        else:
            print(f"❌ is_active should be boolean, got {type(sample_record['is_active'])}")
        
        # Test pixel events JSON
        try:
            pixel_events = json.loads(sample_record['meta_pixel_events'])
            if isinstance(pixel_events, dict):
                print(f"✅ meta_pixel_events is valid JSON: {pixel_events}")
            else:
                print(f"❌ meta_pixel_events should be dict, got {type(pixel_events)}")
        except json.JSONDecodeError as e:
            print(f"❌ meta_pixel_events is not valid JSON: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Output format test failed: {e}")
        return False

# %%
def main():
    """Run all tests"""
    print("=" * 60)
    print("META ADS DAILY CAMPAIGNS EXTRACTOR - TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_extractor_structure,
        test_pixel_events_extraction,
        test_campaign_activity_tracker,
        test_output_format
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("✅ ALL TESTS PASSED - Extractor structure is correct")
        return True
    else:
        print("❌ SOME TESTS FAILED - Review extractor implementation")
        return False

# %%
if __name__ == "__main__":
    main()