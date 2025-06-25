"""
BEDROT Data Warehouse - Financial Data ETL Pipeline
Extracts and loads financial transactions from DistroKid and Capitol One data.
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
CURATED_CSV_PATH = DATA_LAKE_PATH / "curated_csvs"

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

def get_track_map(conn) -> Dict[str, int]:
    """Get track title to ID mapping."""
    cursor = conn.execute("""
        SELECT t.track_title, t.track_id, a.artist_name
        FROM tracks t
        JOIN artists a ON t.artist_id = a.artist_id
    """)
    return {f"{row[2]}|{row[0]}": row[1] for row in cursor.fetchall()}

def extract_distrokid_financial_data() -> List[Dict]:
    """Extract financial transactions from DistroKid bank details."""
    transactions = []
    
    dk_file = CURATED_CSV_PATH / "dk_bank_details.csv"
    if not dk_file.exists():
        print(f"Warning: {dk_file} not found")
        return transactions
    
    df = pd.read_csv(dk_file)
    
    for _, row in df.iterrows():
        if pd.notna(row.get('Earnings USD')) and float(row['Earnings USD']) != 0:
            # Parse date from filename or reporting period
            date_str = row.get('Reporting Date', '2024-01-01')
            
            transaction = {
                'transaction_date': date_str,
                'description': f"DistroKid earnings for {row.get('Title', 'Unknown Track')}",
                'amount': float(row['Earnings USD']),
                'currency': 'USD',
                'category': 'Streaming Revenue',
                'status': 'Completed',
                'source_platform': 'DistroKid',
                'artist_name': row.get('Artist'),
                'track_title': row.get('Title'),
                'country': row.get('Territory', 'Unknown')
            }
            transactions.append(transaction)
    
    return transactions

def extract_capitol_one_financial_data() -> List[Dict]:
    """Extract financial transactions from Capitol One banking data."""
    transactions = []
    
    # Look for Capitol One files
    capitol_files = list(CURATED_CSV_PATH.glob("*capitol*")) + list(CURATED_CSV_PATH.glob("*bank*"))
    
    for file_path in capitol_files:
        if file_path.name == "dk_bank_details.csv":  # Skip DistroKid file
            continue
            
        try:
            df = pd.read_csv(file_path)
            
            # Process Capitol One transaction format
            for _, row in df.iterrows():
                # Adapt to actual Capitol One CSV structure
                if pd.notna(row.get('Amount')):
                    transaction = {
                        'transaction_date': row.get('Date', '2024-01-01'),
                        'description': row.get('Description', 'Capitol One Transaction'),
                        'amount': float(row['Amount']),
                        'currency': 'USD',
                        'category': 'Business Expense',
                        'status': 'Completed',
                        'source_platform': 'Capitol One',
                        'artist_name': None,  # No artist association for bank transactions
                        'track_title': None,
                        'country': 'US'
                    }
                    transactions.append(transaction)
                    
        except Exception as e:
            print(f"Warning: Could not process {file_path}: {e}")
    
    return transactions

def load_financial_transactions(conn, transactions: List[Dict], artist_map: Dict[str, int], 
                              platform_map: Dict[str, int], track_map: Dict[str, int]):
    """Load financial transactions into database."""
    
    loaded_count = 0
    
    for transaction in transactions:
        # Map foreign keys
        source_platform_id = platform_map.get(transaction['source_platform'])
        artist_id = artist_map.get(transaction['artist_name']) if transaction['artist_name'] else None
        
        # Find track ID
        track_id = None
        if transaction['artist_name'] and transaction['track_title']:
            track_key = f"{transaction['artist_name']}|{transaction['track_title']}"
            track_id = track_map.get(track_key)
        
        # Insert transaction
        cursor = conn.execute("""
            INSERT INTO financial_transactions 
            (transaction_date, description, amount, currency, category, status,
             source_platform_id, artist_id, track_id, country)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            transaction['transaction_date'],
            transaction['description'],
            transaction['amount'],
            transaction['currency'],
            transaction['category'],
            transaction['status'],
            source_platform_id,
            artist_id,
            track_id,
            transaction['country']
        ))
        
        loaded_count += 1
    
    return loaded_count

def run_financial_etl():
    """Run complete financial data ETL pipeline."""
    print("🚀 Starting Financial Data ETL Pipeline...")
    
    conn = get_connection()
    
    try:
        # Get mapping data
        print("Getting reference data...")
        artist_map = get_artist_map(conn)
        platform_map = get_platform_map(conn)
        track_map = get_track_map(conn)
        
        print(f"   Artists: {len(artist_map)}")
        print(f"   Platforms: {len(platform_map)}")
        print(f"   Tracks: {len(track_map)}")
        
        # Extract financial data
        print("\n1. Extracting DistroKid financial data...")
        dk_transactions = extract_distrokid_financial_data()
        print(f"   Found {len(dk_transactions)} DistroKid transactions")
        
        print("\n2. Extracting Capitol One financial data...")
        co_transactions = extract_capitol_one_financial_data()
        print(f"   Found {len(co_transactions)} Capitol One transactions")
        
        # Combine all transactions
        all_transactions = dk_transactions + co_transactions
        print(f"\n3. Total transactions to load: {len(all_transactions)}")
        
        # Load transactions
        print("\n4. Loading financial transactions...")
        loaded_count = load_financial_transactions(conn, all_transactions, artist_map, platform_map, track_map)
        print(f"   Loaded {loaded_count} transactions")
        
        conn.commit()
        
        # Show summary
        cursor = conn.execute("SELECT COUNT(*) FROM financial_transactions")
        total_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT SUM(amount) FROM financial_transactions WHERE amount > 0")
        total_revenue = cursor.fetchone()[0] or 0
        
        cursor = conn.execute("SELECT SUM(ABS(amount)) FROM financial_transactions WHERE amount < 0")
        total_expenses = cursor.fetchone()[0] or 0
        
        print(f"\n✅ Financial ETL Complete!")
        print(f"   Total Transactions: {total_count}")
        print(f"   Total Revenue: ${total_revenue:.2f}")
        print(f"   Total Expenses: ${total_expenses:.2f}")
        print(f"   Net: ${total_revenue - total_expenses:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in financial ETL: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    run_financial_etl()