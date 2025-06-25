"""
BEDROT Data Warehouse - Master Data ETL Pipeline
Extracts and loads Artists, Platforms, and Tracks from CSV sources.

This module processes all CSV files to identify and normalize:
1. Artists - Unique artist entities across all platforms
2. Platforms - Already seeded, but can be extended
3. Tracks - Musical content with ISRC/UPC codes where available
"""

import sqlite3
import pandas as pd
import re
from pathlib import Path
from datetime import datetime
from typing import Set, Dict, List, Tuple

# Paths - Updated to work from data_lake directory
DATA_LAKE_PATH = Path(__file__).parent.parent  # Go up to data_lake from etl/
ECOSYSTEM_ROOT = DATA_LAKE_PATH.parent
WAREHOUSE_PATH = ECOSYSTEM_ROOT / "data-warehouse"
DB_PATH = WAREHOUSE_PATH / "bedrot_analytics.db"
CURATED_CSV_PATH = DATA_LAKE_PATH / "curated"

def get_connection():
    """Get database connection with optimized settings."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def extract_artists_from_csvs() -> Set[str]:
    """Extract unique artist names from all CSV sources."""
    artists = set()
    
    # From DistroKid bank details
    dk_file = CURATED_CSV_PATH / "dk_bank_details.csv"
    if dk_file.exists():
        df = pd.read_csv(dk_file)
        if 'Artist' in df.columns:
            artists.update(df['Artist'].dropna().unique())
    
    # From Spotify audience data  
    spotify_file = CURATED_CSV_PATH / "spotify_audience_curated_20250623_081402.csv"
    if spotify_file.exists():
        df = pd.read_csv(spotify_file)
        if 'artist_name' in df.columns:
            artists.update(df['artist_name'].dropna().unique())
    
    # From TikTok analytics
    tiktok_file = CURATED_CSV_PATH / "tiktok_analytics_curated_20250623_081404.csv"
    if tiktok_file.exists():
        df = pd.read_csv(tiktok_file)
        if 'artist' in df.columns:
            artists.update(df['artist'].dropna().unique())
    
    # From SubmitHub files
    for submithub_file in CURATED_CSV_PATH.glob("submithub_links_analytics_*.csv"):
        df = pd.read_csv(submithub_file)
        if 'artist' in df.columns:
            artists.update(df['artist'].dropna().unique())
    
    # From Meta Ads campaign names (extract artist from campaign names)
    metaads_file = CURATED_CSV_PATH / "metaads_campaigns_performance_log.csv"
    if metaads_file.exists():
        df = pd.read_csv(metaads_file)
        if 'campaign_name' in df.columns:
            for campaign in df['campaign_name'].dropna().unique():
                # Extract artist from campaign names like "PIG1987 - DYSMORPHIA - Streaming"
                if ' - ' in campaign:
                    artist_part = campaign.split(' - ')[0].strip()
                    if artist_part and not artist_part.upper().startswith('THE '):
                        artists.add(artist_part)
    
    # Clean and normalize artist names including collaborations
    cleaned_artists = set()
    for artist in artists:
        if artist and isinstance(artist, str) and len(artist.strip()) > 0:
            normalized = normalize_artist_name(artist)
            cleaned_artists.add(normalized)
    
    return cleaned_artists

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

def extract_tracks_from_csvs() -> List[Dict]:
    """Extract unique tracks with metadata from CSV sources."""
    tracks = []
    
    # From DistroKid bank details (has ISRC, UPC, track titles)
    dk_file = CURATED_CSV_PATH / "dk_bank_details.csv"
    if dk_file.exists():
        df = pd.read_csv(dk_file)
        
        for _, row in df.iterrows():
            if pd.notna(row.get('Title')) and pd.notna(row.get('Artist')):
                isrc = str(row.get('ISRC', '')).strip() if pd.notna(row.get('ISRC')) and str(row.get('ISRC')).strip() and str(row.get('ISRC')).strip() != 'nan' else None
                upc = str(row.get('UPC', '')).strip() if pd.notna(row.get('UPC')) and str(row.get('UPC')).strip() and str(row.get('UPC')).strip() != 'nan' else None
                
                track = {
                    'artist_name': normalize_artist_name(str(row['Artist']).strip()),
                    'track_title': str(row['Title']).strip(),
                    'isrc': isrc,
                    'upc': upc,
                    'content_type': str(row.get('Song/Album', 'Song')).strip() if pd.notna(row.get('Song/Album')) else 'Song'
                }
                
                # Clean content type
                if track['content_type'] not in ['Song', 'Album']:
                    track['content_type'] = 'Song'
                
                tracks.append(track)
    
    # From SubmitHub files (track names from campaign data)
    for submithub_file in CURATED_CSV_PATH.glob("submithub_links_analytics_*.csv"):
        df = pd.read_csv(submithub_file)
        
        for _, row in df.iterrows():
            if pd.notna(row.get('track')) and pd.notna(row.get('artist')):
                track = {
                    'artist_name': normalize_artist_name(str(row['artist']).strip()),
                    'track_title': str(row['track']).strip(), 
                    'isrc': None,
                    'upc': None,
                    'content_type': 'Song'  # Assume songs from SubmitHub
                }
                tracks.append(track)
    
    # From Meta Ads campaign names (infer tracks)
    metaads_file = CURATED_CSV_PATH / "metaads_campaigns_performance_log.csv"
    if metaads_file.exists():
        df = pd.read_csv(metaads_file)
        
        for campaign in df['campaign_name'].dropna().unique():
            if ' - ' in campaign:
                parts = campaign.split(' - ')
                if len(parts) >= 2:
                    artist_part = parts[0].strip()
                    track_part = parts[1].strip()
                    
                    # Skip if it's not a real track (like "Streaming")
                    if track_part.lower() not in ['streaming', 'broad', 'techno', 'hard trance', 'broad spotify']:
                        track = {
                            'artist_name': normalize_artist_name(artist_part),
                            'track_title': track_part,
                            'isrc': None,
                            'upc': None,
                            'content_type': 'Song'
                        }
                        tracks.append(track)
    
    # Remove duplicates based on artist + track title, and handle ISRC conflicts
    unique_tracks = {}
    isrc_seen = set()
    
    for track in tracks:
        key = (track['artist_name'].lower(), track['track_title'].lower())
        
        # Skip if ISRC already exists (avoid UNIQUE constraint violation)
        if track['isrc'] and track['isrc'] in isrc_seen:
            track['isrc'] = None  # Remove duplicate ISRC
        elif track['isrc']:
            isrc_seen.add(track['isrc'])
        
        if key not in unique_tracks:
            unique_tracks[key] = track
        else:
            # Merge metadata (prefer non-null values)
            existing = unique_tracks[key]
            if not existing['isrc'] and track['isrc']:
                existing['isrc'] = track['isrc']
                isrc_seen.add(track['isrc'])
            if not existing['upc'] and track['upc']:
                existing['upc'] = track['upc']
    
    return list(unique_tracks.values())

def load_artists(conn, artists: Set[str]) -> Dict[str, int]:
    """Load artists into database and return name -> id mapping."""
    artist_map = {}
    
    for artist_name in sorted(artists):
        cursor = conn.execute(
            "INSERT OR IGNORE INTO artists (artist_name) VALUES (?)",
            (artist_name,)
        )
        
        # Get the artist_id (either newly inserted or existing)
        cursor = conn.execute(
            "SELECT artist_id FROM artists WHERE artist_name = ?",
            (artist_name,)
        )
        artist_id = cursor.fetchone()[0]
        artist_map[artist_name] = artist_id
    
    return artist_map

def load_tracks(conn, tracks: List[Dict], artist_map: Dict[str, int]) -> Dict[Tuple[str, str], int]:
    """Load tracks into database and return (artist, title) -> id mapping."""
    track_map = {}
    
    for track in tracks:
        artist_name = track['artist_name']
        
        if artist_name not in artist_map:
            print(f"Warning: Artist '{artist_name}' not found in artist_map")
            continue
        
        artist_id = artist_map[artist_name]
        
        # Check if track already exists
        cursor = conn.execute(
            "SELECT track_id FROM tracks WHERE artist_id = ? AND track_title = ?",
            (artist_id, track['track_title'])
        )
        existing = cursor.fetchone()
        
        if existing:
            track_id = existing[0]
            # Update with additional metadata if available
            if track['isrc']:
                conn.execute(
                    "UPDATE tracks SET isrc = ? WHERE track_id = ? AND isrc IS NULL",
                    (track['isrc'], track_id)
                )
            if track['upc']:
                conn.execute(
                    "UPDATE tracks SET upc = ? WHERE track_id = ? AND upc IS NULL", 
                    (track['upc'], track_id)
                )
        else:
            # Insert new track
            cursor = conn.execute(
                """INSERT INTO tracks 
                   (artist_id, track_title, isrc, upc, content_type) 
                   VALUES (?, ?, ?, ?, ?)""",
                (artist_id, track['track_title'], track['isrc'], track['upc'], track['content_type'])
            )
            track_id = cursor.lastrowid
        
        track_map[(artist_name, track['track_title'])] = track_id
    
    return track_map

def update_spotify_artist_ids(conn, artist_map: Dict[str, int]):
    """Update Spotify artist IDs from Spotify audience data."""
    spotify_file = CURATED_CSV_PATH / "spotify_audience_curated_20250623_081402.csv"
    if not spotify_file.exists():
        return
    
    df = pd.read_csv(spotify_file)
    
    # Group by artist to get unique artist_id mappings
    spotify_mapping = df.groupby('artist_name')['artist_id'].first().to_dict()
    
    for artist_name, spotify_artist_id in spotify_mapping.items():
        if artist_name in artist_map and pd.notna(spotify_artist_id):
            conn.execute(
                "UPDATE artists SET spotify_artist_id = ? WHERE artist_id = ?",
                (spotify_artist_id, artist_map[artist_name])
            )

def run_master_data_etl():
    """Run complete master data ETL pipeline."""
    print("🚀 Starting Master Data ETL Pipeline...")
    print(f"Source: {CURATED_CSV_PATH}")
    print(f"Target: {DB_PATH}")
    
    conn = get_connection()
    
    try:
        print("\n1. Extracting Artists...")
        artists = extract_artists_from_csvs()
        print(f"   Found {len(artists)} unique artists: {sorted(artists)}")
        
        print("\n2. Extracting Tracks...")
        tracks = extract_tracks_from_csvs()
        print(f"   Found {len(tracks)} unique tracks")
        
        print("\n3. Loading Artists...")
        artist_map = load_artists(conn, artists)
        print(f"   Loaded {len(artist_map)} artists")
        
        print("\n4. Loading Tracks...")
        track_map = load_tracks(conn, tracks, artist_map)
        print(f"   Loaded {len(track_map)} tracks")
        
        print("\n5. Updating Spotify Artist IDs...")
        update_spotify_artist_ids(conn, artist_map)
        print("   ✓ Spotify IDs updated")
        
        conn.commit()
        
        # Show final counts
        cursor = conn.execute("SELECT COUNT(*) FROM artists")
        artist_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM tracks")
        track_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM platforms")
        platform_count = cursor.fetchone()[0]
        
        print(f"\n✅ Master Data ETL Complete!")
        print(f"   Artists: {artist_count}")
        print(f"   Tracks: {track_count}")
        print(f"   Platforms: {platform_count}")
        
        # Update database info
        conn.execute(
            "UPDATE database_info SET last_etl_run = ?, total_records = ? WHERE info_id = 1",
            (datetime.now().isoformat(), artist_count + track_count + platform_count)
        )
        conn.commit()
        
        return True
        
    except Exception as e:
        print(f"❌ Error in master data ETL: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def show_master_data_summary():
    """Display summary of loaded master data."""
    conn = get_connection()
    
    try:
        print("\n📊 Master Data Summary")
        
        # Artists
        print("\n🎤 Artists:")
        cursor = conn.execute(
            "SELECT artist_name, spotify_artist_id FROM artists ORDER BY artist_name"
        )
        for row in cursor.fetchall():
            spotify_id = f" (Spotify: {row[1]})" if row[1] else ""
            print(f"   - {row[0]}{spotify_id}")
        
        # Tracks by artist
        print("\n🎵 Tracks:")
        cursor = conn.execute("""
            SELECT a.artist_name, t.track_title, t.content_type, t.isrc
            FROM tracks t
            JOIN artists a ON t.artist_id = a.artist_id
            ORDER BY a.artist_name, t.track_title
        """)
        
        current_artist = None
        for row in cursor.fetchall():
            artist, title, content_type, isrc = row
            if artist != current_artist:
                print(f"   {artist}:")
                current_artist = artist
            isrc_info = f" (ISRC: {isrc})" if isrc else ""
            print(f"     - {title} [{content_type}]{isrc_info}")
        
        # Platform summary
        print("\n🌐 Platforms:")
        cursor = conn.execute(
            "SELECT platform_name, platform_type FROM platforms ORDER BY platform_type, platform_name"
        )
        current_type = None
        for row in cursor.fetchall():
            platform, ptype = row
            if ptype != current_type:
                print(f"   {ptype}:")
                current_type = ptype
            print(f"     - {platform}")
            
    finally:
        conn.close()

if __name__ == "__main__":
    success = run_master_data_etl()
    if success:
        show_master_data_summary()