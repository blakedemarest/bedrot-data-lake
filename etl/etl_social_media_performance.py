"""
BEDROT Data Warehouse - Social Media Performance ETL Pipeline
Extracts and loads social media performance data from TikTok analytics.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Paths
DATA_LAKE_PATH = Path(__file__).parent.parent
ECOSYSTEM_ROOT = DATA_LAKE_PATH.parent
WAREHOUSE_PATH = ECOSYSTEM_ROOT / "data-warehouse"
DB_PATH = WAREHOUSE_PATH / "bedrot_analytics.db"
CURATED_CSV_PATH = DATA_LAKE_PATH / "curated"

def get_connection():
    """Get database connection with optimized settings."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def get_artist_map(conn) -> Dict[str, int]:
    """Get artist name to ID mapping."""
    cursor = conn.execute("SELECT artist_name, artist_id FROM artists")
    return {row[0]: row[1] for row in cursor.fetchall()}

def get_platform_map(conn) -> Dict[str, int]:
    """Get platform name to ID mapping."""
    cursor = conn.execute("SELECT platform_name, platform_id FROM platforms")
    return {row[0]: row[1] for row in cursor.fetchall()}

def normalize_artist_name(artist_name: str) -> str:
    """Normalize artist name with proper handling of variations and collaborations."""
    if not artist_name or not isinstance(artist_name, str):
        return artist_name
    
    cleaned = artist_name.strip()
    
    # Normalize case variations
    if cleaned.lower() == 'pig1987':
        return 'PIG1987'
    elif cleaned.upper() == 'ZONE A0' or cleaned.lower() in ['zone.a0', 'zone_a0']:
        return 'ZONE A0'
    elif cleaned.upper() == 'IWARY':
        return 'IWARY'
    elif 'PIG1987' in cleaned and 'ZONE A0' in cleaned:
        return 'PIG1987 & ZONE A0'
    elif 'ZONE A0' in cleaned and 'Sxnctuary' in cleaned:
        return 'ZONE A0 & Sxnctuary'
    
    return cleaned

def extract_tiktok_performance_data() -> List[Dict]:
    """Extract social media performance from TikTok analytics data."""
    performance_data = []
    
    tiktok_file = CURATED_CSV_PATH / "tiktok_analytics_curated_20250623_081404.csv"
    if not tiktok_file.exists():
        print(f"Warning: {tiktok_file} not found")
        return performance_data
    
    df = pd.read_csv(tiktok_file)
    
    for _, row in df.iterrows():
        if pd.notna(row.get('artist')):
            performance = {
                'date': row.get('date', '2024-06-23'),
                'artist_name': normalize_artist_name(row['artist']),
                'platform': 'TikTok',
                'video_views': int(row.get('video_views', 0)) if pd.notna(row.get('video_views')) else 0,
                'profile_views': int(row.get('profile_views', 0)) if pd.notna(row.get('profile_views')) else 0,
                'likes': int(row.get('likes', 0)) if pd.notna(row.get('likes')) else 0,
                'comments': int(row.get('comments', 0)) if pd.notna(row.get('comments')) else 0,
                'shares': int(row.get('shares', 0)) if pd.notna(row.get('shares')) else 0,
                'engagement_rate': float(row.get('engagement_rate', 0.0)) if pd.notna(row.get('engagement_rate')) else 0.0
            }
            performance_data.append(performance)
    
    return performance_data

def load_social_media_performance(conn, performance_data: List[Dict], artist_map: Dict[str, int], platform_map: Dict[str, int]):
    """Load social media performance data into database."""
    
    loaded_count = 0
    
    for performance in performance_data:
        # Map foreign keys
        artist_id = artist_map.get(performance['artist_name'])
        platform_id = platform_map.get(performance['platform'])
        
        if not artist_id:
            print(f"Warning: Artist '{performance['artist_name']}' not found in database")
            continue
            
        if not platform_id:
            print(f"Warning: Platform '{performance['platform']}' not found in database")
            continue
        
        # Insert performance record
        cursor = conn.execute("""
            INSERT INTO social_media_performance 
            (date, artist_id, platform_id, video_views, profile_views, likes, 
             comments, shares, engagement_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            performance['date'],
            artist_id,
            platform_id,
            performance['video_views'],
            performance['profile_views'],
            performance['likes'],
            performance['comments'],
            performance['shares'],
            performance['engagement_rate']
        ))
        
        loaded_count += 1
    
    return loaded_count

def run_social_media_etl():
    """Run complete social media performance ETL pipeline."""
    print("🚀 Starting Social Media Performance ETL Pipeline...")
    
    conn = get_connection()
    
    try:
        # Get mapping data
        print("Getting reference data...")
        artist_map = get_artist_map(conn)
        platform_map = get_platform_map(conn)
        
        print(f"   Artists: {len(artist_map)}")
        print(f"   Platforms: {len(platform_map)}")
        
        # Extract social media data
        print("\n1. Extracting TikTok performance data...")
        tiktok_data = extract_tiktok_performance_data()
        print(f"   Found {len(tiktok_data)} TikTok performance records")
        
        # Load performance data
        print("\n2. Loading social media performance data...")
        loaded_count = load_social_media_performance(conn, tiktok_data, artist_map, platform_map)
        print(f"   Loaded {loaded_count} performance records")
        
        conn.commit()
        
        # Show summary
        cursor = conn.execute("SELECT COUNT(*) FROM social_media_performance")
        total_count = cursor.fetchone()[0]
        
        cursor = conn.execute("""
            SELECT a.artist_name, SUM(smp.video_views), SUM(smp.likes), AVG(smp.engagement_rate)
            FROM social_media_performance smp
            JOIN artists a ON smp.artist_id = a.artist_id
            GROUP BY a.artist_name
            ORDER BY SUM(smp.video_views) DESC
        """)
        
        print(f"\n✅ Social Media ETL Complete!")
        print(f"   Total Performance Records: {total_count}")
        print("\n📊 Social Media Performance Summary:")
        
        for row in cursor.fetchall():
            artist, video_views, likes, avg_engagement = row
            print(f"   {artist}: {video_views:,} views, {likes:,} likes, {avg_engagement:.2%} engagement")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in social media ETL: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    run_social_media_etl()