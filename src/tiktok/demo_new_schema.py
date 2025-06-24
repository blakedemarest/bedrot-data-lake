"""
TikTok Schema Enhancement Demo

This script demonstrates the enhanced TikTok curated schema with follower tracking.

EXISTING SCHEMA:
artist,zone,date,Video Views,Profile Views,Likes,Comments,Shares,Year,engagement_rate

NEW ENHANCED SCHEMA:
artist,zone,date,Video Views,Profile Views,Likes,Comments,Shares,Year,engagement_rate,Followers,new_followers

NEW FEATURES:
- Followers: Current follower count (captured via network interception)
- new_followers: Daily new followers (calculated from daily differences)
"""

import pandas as pd
from datetime import datetime, date
from pathlib import Path

# Demo data showing the new schema
demo_data = [
    {
        'artist': 'pig1987',
        'zone': 'pig1987', 
        'date': date(2024, 6, 1),
        'Video Views': 1500,
        'Profile Views': 200,
        'Likes': 85,
        'Comments': 12,
        'Shares': 5,
        'Year': 2024,
        'engagement_rate': 0.0680,
        'Followers': 1250,  # NEW: Current followers
        'new_followers': 0  # NEW: No baseline for first day
    },
    {
        'artist': 'pig1987',
        'zone': 'pig1987',
        'date': date(2024, 6, 2), 
        'Video Views': 2100,
        'Profile Views': 180,
        'Likes': 95,
        'Comments': 18,
        'Shares': 8,
        'Year': 2024,
        'engagement_rate': 0.0576,
        'Followers': 1285,  # NEW: Increased followers
        'new_followers': 35  # NEW: 35 new followers (1285 - 1250)
    },
    {
        'artist': 'zone.a0',
        'zone': 'zone.a0',
        'date': date(2024, 6, 1),
        'Video Views': 3200,
        'Profile Views': 420,
        'Likes': 156,
        'Comments': 28,
        'Shares': 15,
        'Year': 2024,
        'engagement_rate': 0.0622,
        'Followers': 2100,  # NEW: Current followers
        'new_followers': 0  # NEW: No baseline for first day
    },
    {
        'artist': 'zone.a0',
        'zone': 'zone.a0',
        'date': date(2024, 6, 2),
        'Video Views': 2800,
        'Profile Views': 380,
        'Likes': 132,
        'Comments': 22,
        'Shares': 11,
        'Year': 2024,
        'engagement_rate': 0.0589,
        'Followers': 2158,  # NEW: Increased followers
        'new_followers': 58  # NEW: 58 new followers (2158 - 2100)
    }
]

def demonstrate_schema():
    """Show the enhanced schema with examples."""
    print("🎯 TikTok Enhanced Schema Demonstration")
    print("=" * 60)
    
    # Create DataFrame
    df = pd.DataFrame(demo_data)
    
    print("\n📊 ENHANCED CURATED DATA SAMPLE:")
    print("-" * 40)
    print(df.to_string(index=False))
    
    print(f"\n📈 FOLLOWER GROWTH ANALYSIS:")
    print("-" * 30)
    
    for artist in df['artist'].unique():
        artist_data = df[df['artist'] == artist].sort_values('date')
        
        total_new = artist_data['new_followers'].sum()
        start_followers = artist_data['Followers'].iloc[0]
        end_followers = artist_data['Followers'].iloc[-1]
        
        print(f"{artist}:")
        print(f"  • Starting followers: {start_followers:,}")
        print(f"  • Ending followers: {end_followers:,}")
        print(f"  • Total new followers: {total_new:,}")
        print(f"  • Growth rate: {((end_followers/start_followers - 1) * 100):.1f}%")
        print()
    
    print("✅ SCHEMA CHANGES SUMMARY:")
    print("-" * 25)
    print("BEFORE: 10 columns")
    print("AFTER:  12 columns (+2)")
    print()
    print("NEW COLUMNS ADDED:")
    print("  1. Followers - Current follower count (from network capture)")  
    print("  2. new_followers - Daily new followers (calculated in cleaner)")
    print()
    print("EXISTING COLUMNS: Unchanged")
    print("  ✓ Video Views (was always correct, no 'reach' issue in curated)")
    print("  ✓ All other engagement metrics preserved")
    
    print(f"\n🔧 IMPLEMENTATION DETAILS:")
    print("-" * 25)
    print("EXTRACTION:")
    print("  • Playwright network interception captures follower count")
    print("  • Saved as JSON files in landing zone")
    print("  • Integrated into existing TikTok extractors")
    print()
    print("PROCESSING:")
    print("  • landing2raw: Includes follower count in NDJSON")
    print("  • raw2staging: Adds Followers column")
    print("  • staging2curated: Calculates new_followers from daily diffs")
    print()
    print("AUTOMATION:")
    print("  • Existing cron job unchanged")
    print("  • Automatic follower tracking")
    print("  • Backward compatible with existing data")

if __name__ == "__main__":
    demonstrate_schema()