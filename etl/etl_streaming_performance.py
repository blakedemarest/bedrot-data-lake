"""
BEDROT Data Warehouse - Streaming Performance ETL Pipeline
Extracts and loads streaming performance data from Spotify audience data.
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

def extract_spotify_performance_data() -> List[Dict]:
    """Extract streaming performance from Spotify audience data."""
    performance_data = []
    
    spotify_file = CURATED_CSV_PATH / "spotify_audience_curated_20250623_081402.csv"
    if not spotify_file.exists():
        print(f"Warning: {spotify_file} not found")
        return performance_data
    
    df = pd.read_csv(spotify_file)
    
    # Group by date and artist to aggregate metrics
    for _, row in df.iterrows():
        if pd.notna(row.get('artist_name')):
            performance = {
                'date': row.get('date', '2024-06-23'),  # Use extraction date as default
                'artist_name': normalize_artist_name(row['artist_name']),
                'platform': 'Spotify',
                'track_id': None,  # Spotify data is artist-level, not track-level
                'listeners': int(row.get('listeners', 0)) if pd.notna(row.get('listeners')) else 0,
                'streams': int(row.get('streams', 0)) if pd.notna(row.get('streams')) else 0,
                'followers': int(row.get('followers', 0)) if pd.notna(row.get('followers')) else 0,
                'data_source': 'Spotify Audience Data'
            }
            performance_data.append(performance)
    
    return performance_data

def load_streaming_performance(conn, performance_data: List[Dict], artist_map: Dict[str, int], platform_map: Dict[str, int]):
    """Load streaming performance data into database."""
    
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
            INSERT INTO streaming_performance 
            (date, artist_id, platform_id, track_id, listeners, streams, followers, data_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            performance['date'],
            artist_id,
            platform_id,
            performance['track_id'],
            performance['listeners'],
            performance['streams'],
            performance['followers'],
            performance['data_source']
        ))
        
        loaded_count += 1
    
    return loaded_count

def run_streaming_performance_etl():
    """Run complete streaming performance ETL pipeline."""
    print("🚀 Starting Streaming Performance ETL Pipeline...")
    
    conn = get_connection()
    
    try:
        # Get mapping data
        print("Getting reference data...")
        artist_map = get_artist_map(conn)
        platform_map = get_platform_map(conn)
        
        print(f"   Artists: {len(artist_map)}")
        print(f"   Platforms: {len(platform_map)}")
        
        # Extract streaming data
        print("\n1. Extracting Spotify performance data...")
        spotify_data = extract_spotify_performance_data()
        print(f"   Found {len(spotify_data)} Spotify performance records")
        
        # Load performance data
        print("\n2. Loading streaming performance data...")
        loaded_count = load_streaming_performance(conn, spotify_data, artist_map, platform_map)
        print(f"   Loaded {loaded_count} performance records")
        
        conn.commit()
        
        # Show summary
        cursor = conn.execute("SELECT COUNT(*) FROM streaming_performance")
        total_count = cursor.fetchone()[0]
        
        cursor = conn.execute("""
            SELECT a.artist_name, SUM(sp.listeners), SUM(sp.streams), SUM(sp.followers)
            FROM streaming_performance sp
            JOIN artists a ON sp.artist_id = a.artist_id
            GROUP BY a.artist_name
            ORDER BY SUM(sp.streams) DESC
        """)
        
        print(f"\n✅ Streaming Performance ETL Complete!")
        print(f"   Total Performance Records: {total_count}")
        print("\n📊 Artist Performance Summary:")
        
        for row in cursor.fetchall():
            artist, listeners, streams, followers = row
            print(f"   {artist}: {streams:,} streams, {listeners:,} listeners, {followers:,} followers")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in streaming performance ETL: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    run_streaming_performance_etl()