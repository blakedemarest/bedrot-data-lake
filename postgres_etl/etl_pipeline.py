#!/usr/bin/env python3
"""
Modular ETL Pipeline for BEDROT Data Lake PostgreSQL Integration.
Automatically discovers and ingests CSV files from the curated directory.
"""

import os
import sys
import json
import hashlib
import logging
import math
import numpy as np
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataTypeDetector:
    """Intelligent data type detection and classification."""
    
    @staticmethod
    def detect_metric_type(columns: List[str], file_path: str) -> str:
        """Detect the primary metric type based on columns and file path."""
        columns_lower = [col.lower() for col in columns]
        file_path_lower = file_path.lower()
        
        # Streaming metrics
        if any(term in columns_lower for term in ['streams', 'spotify', 'apple']):
            return 'streams'
        
        # Social media metrics
        if any(term in columns_lower for term in ['views', 'clicks', 'clickthrough', 'unique']):
            return 'views' if 'views' in columns_lower else 'clicks'
        
        # Advertising metrics
        if any(term in columns_lower for term in ['spend', 'impressions', 'cpc', 'campaign']):
            return 'advertising'
        
        # Financial metrics
        if any(term in columns_lower for term in ['amount', 'purchase', 'transaction']):
            return 'financial'
        
        # Default based on file path
        if 'metaads' in file_path_lower or 'advertising' in file_path_lower:
            return 'advertising'
        elif 'linktree' in file_path_lower or 'tiktok' in file_path_lower:
            return 'engagement'
        elif 'distrokid' in file_path_lower or 'streaming' in file_path_lower:
            return 'streams'
        
        return 'unknown'
    
    @staticmethod
    def extract_platform(file_path: str, data: Dict[str, Any]) -> str:
        """Extract platform name from file path or data."""
        file_path_lower = file_path.lower()
        
        platform_mapping = {
            'linktree': 'linktree',
            'tiktok': 'tiktok',
            'metaads': 'meta',
            'distrokid': 'distrokid',
            'spotify': 'spotify',
            'instagram': 'instagram',
            'facebook': 'facebook'
        }
        
        for key, platform in platform_mapping.items():
            if key in file_path_lower:
                return platform
        
        # Check if source is in the data
        if 'source' in data:
            return str(data['source'])
        
        return 'unknown'
    
    @staticmethod
    def extract_entity_name(data: Dict[str, Any], metric_type: str) -> Optional[str]:
        """Extract the main entity name (artist, campaign, etc.)."""
        if metric_type == 'advertising':
            return data.get('campaign_name_x') or data.get('campaign_name_y') or data.get('campaign_name')
        elif metric_type == 'streams':
            return data.get('artist') or data.get('artist_name')
        
        return None

class DataCleaner:
    """Data cleaning and transformation utilities."""
    
    @staticmethod
    def clean_numeric_fields(data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and convert numeric fields."""
        import math
        import numpy as np
        
        cleaned = data.copy()
        
        for key, value in cleaned.items():
            # Handle pandas NaN values
            if pd.isna(value) or (isinstance(value, float) and math.isnan(value)):
                cleaned[key] = None
                continue
            
            # Handle numpy NaN values
            if isinstance(value, (np.floating, np.integer)) and np.isnan(value):
                cleaned[key] = None
                continue
            
            # Handle string representations of NaN
            if isinstance(value, str):
                if value.lower() in ['nan', 'null', 'none', '']:
                    cleaned[key] = None
                    continue
                
                # Try to convert string numbers
                try:
                    if '.' in value or 'e' in value.lower():
                        cleaned[key] = float(value)
                    else:
                        cleaned[key] = int(value)
                except (ValueError, TypeError):
                    # Keep as string if conversion fails
                    pass
        
        return cleaned
    
    @staticmethod
    def parse_date_field(data: Dict[str, Any]) -> Optional[date]:
        """Extract and parse date from various possible fields."""
        date_fields = ['date', 'date_recorded', 'date_start', 'created_time']
        
        for field in date_fields:
            if field in data and data[field]:
                try:
                    date_str = str(data[field])
                    # Handle various date formats
                    if 'T' in date_str:  # ISO format with time
                        return datetime.fromisoformat(date_str.split('T')[0]).date()
                    else:
                        return datetime.strptime(date_str, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    continue
        
        return None
    
    @staticmethod
    def generate_hash_key(data: Dict[str, Any], file_path: str) -> str:
        """Generate a hash key for deduplication."""
        # Create a deterministic string from key data points
        hash_data = {
            'file_path': file_path,
            'date': data.get('date', ''),
            'entity': data.get('campaign_name_x') or data.get('artist') or '',
            'first_values': str(list(data.values())[:3])  # First few values for uniqueness
        }
        
        hash_string = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(hash_string.encode()).hexdigest()

class ETLPipeline:
    """Main ETL pipeline orchestrator."""
    
    def __init__(self, curated_dir: str = None):
        # Allow override via environment variable CURATED_DATA_PATH, otherwise use provided arg or default path
        env_curated = os.getenv('CURATED_DATA_PATH')
        default_curated = Path(__file__).parent.parent / 'curated'
        self.curated_dir = Path(curated_dir) if curated_dir else Path(env_curated) if env_curated else default_curated
        self.connection_params = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'user': os.getenv('POSTGRES_USER', 'bedrot_app'),
            'password': os.getenv('POSTGRES_PASSWORD'),
            'dbname': os.getenv('POSTGRES_DB', 'bedrot_analytics')
        }
        
        if not self.connection_params['password']:
            raise ValueError("POSTGRES_PASSWORD environment variable must be set")
    
    def get_database_connection(self):
        """Get a database connection."""
        return psycopg2.connect(**self.connection_params)
    
    def discover_csv_files(self) -> List[Path]:
        """Discover all CSV files in the curated directory."""
        csv_files = []
        
        def scan_directory(directory: Path):
            for item in directory.iterdir():
                if item.is_file() and item.suffix.lower() == '.csv':
                    csv_files.append(item)
                elif item.is_dir() and not item.name.startswith('.'):
                    scan_directory(item)
        
        scan_directory(self.curated_dir)
        return csv_files
    
    def register_data_source(self, file_path: Path, metric_type: str, row_count: int) -> str:
        """Register or update a data source in the database."""
        with self.get_database_connection() as conn:
            with conn.cursor() as cursor:
                source_name = f"{file_path.parent.name}_{file_path.stem}"
                relative_path = str(file_path.relative_to(self.curated_dir.parent))
                
                # Check if source exists
                cursor.execute(
                    "SELECT id FROM bedrot_analytics.data_sources WHERE source_name = %s",
                    (source_name,)
                )
                result = cursor.fetchone()
                
                if result:
                    # Update existing source
                    cursor.execute("""
                        UPDATE bedrot_analytics.data_sources 
                        SET last_ingested_at = NOW(), row_count = %s, updated_at = NOW()
                        WHERE source_name = %s
                        RETURNING id
                    """, (row_count, source_name))
                    source_id = cursor.fetchone()[0]
                    logger.info(f"Updated data source: {source_name}")
                else:
                    # Create new source
                    cursor.execute("""
                        INSERT INTO bedrot_analytics.data_sources 
                        (source_name, source_type, file_path, row_count)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """, (source_name, metric_type, relative_path, row_count))
                    source_id = cursor.fetchone()[0]
                    logger.info(f"Registered new data source: {source_name}")
                
                conn.commit()
                return source_id
    
    def process_csv_file(self, file_path: Path) -> int:
        """Process a single CSV file and load into database."""
        logger.info(f"Processing file: {file_path}")
        
        try:
            # Read CSV file with better error handling
            try:
                df = pd.read_csv(file_path)
            except pd.errors.ParserError:
                # Try with more flexible parsing
                logger.warning(f"CSV parsing issue with {file_path}, trying with error_bad_lines=False")
                df = pd.read_csv(file_path, on_bad_lines='skip')
            
            if df.empty:
                logger.warning(f"File {file_path} is empty, skipping")
                return 0
            
            # Replace all NaN values with None before processing
            df = df.where(pd.notnull(df), None)
            
            # Detect data characteristics
            columns = df.columns.tolist()
            metric_type = DataTypeDetector.detect_metric_type(columns, str(file_path))
            
            # Register data source
            source_id = self.register_data_source(file_path, metric_type, len(df))
            
            # Process each row
            insights_batch = []
            for _, row in df.iterrows():
                row_dict = row.to_dict()
                
                # Clean the data
                cleaned_data = DataCleaner.clean_numeric_fields(row_dict)
                
                # Additional JSON-safe cleaning: remove any remaining NaN values
                json_safe_data = {}
                for k, v in cleaned_data.items():
                    # Comprehensive NaN checking
                    if v is None:
                        json_safe_data[k] = None
                    elif pd.isna(v):
                        json_safe_data[k] = None
                    elif isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                        json_safe_data[k] = None
                    elif isinstance(v, str) and v.lower() in ['nan', 'inf', '-inf', 'null', 'none']:
                        json_safe_data[k] = None
                    elif hasattr(v, 'isna') and v.isna():  # pandas scalar
                        json_safe_data[k] = None
                    else:
                        json_safe_data[k] = v
                
                # Extract structured fields
                date_recorded = DataCleaner.parse_date_field(json_safe_data)
                platform = DataTypeDetector.extract_platform(str(file_path), json_safe_data)
                entity_name = DataTypeDetector.extract_entity_name(json_safe_data, metric_type)
                hash_key = DataCleaner.generate_hash_key(json_safe_data, str(file_path))
                
                insight = {
                    'source_id': source_id,
                    'date_recorded': date_recorded or date.today(),
                    'metric_type': metric_type,
                    'entity_name': entity_name,
                    'platform': platform,
                    'raw_data': Json(json_safe_data),
                    'file_source': str(file_path.relative_to(self.curated_dir.parent)),
                    'hash_key': hash_key
                }
                
                insights_batch.append(insight)
            
            # Batch insert insights
            self.insert_insights_batch(insights_batch)
            
            logger.info(f"Successfully processed {len(insights_batch)} records from {file_path}")
            return len(insights_batch)
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise
    
    def insert_insights_batch(self, insights: List[Dict[str, Any]]):
        """Insert a batch of insights with deduplication."""
        if not insights:
            return
        
        with self.get_database_connection() as conn:
            with conn.cursor() as cursor:
                # Use ON CONFLICT to handle duplicates
                insert_query = """
                    INSERT INTO bedrot_analytics.insights 
                    (source_id, date_recorded, metric_type, entity_name, platform, 
                     raw_data, file_source, hash_key)
                    VALUES (%(source_id)s, %(date_recorded)s, %(metric_type)s, 
                            %(entity_name)s, %(platform)s, %(raw_data)s, 
                            %(file_source)s, %(hash_key)s)
                    ON CONFLICT (hash_key) DO UPDATE SET
                        raw_data = EXCLUDED.raw_data,
                        ingested_at = NOW()
                """
                
                cursor.executemany(insert_query, insights)
                conn.commit()
    
    def run_full_etl(self) -> Dict[str, int]:
        """Run the complete ETL pipeline."""
        logger.info("Starting full ETL pipeline...")
        
        # Discover CSV files
        csv_files = self.discover_csv_files()
        logger.info(f"Found {len(csv_files)} CSV files to process")
        
        results = {
            'files_processed': 0,
            'total_records': 0,
            'errors': 0
        }
        
        # Process each file
        for file_path in csv_files:
            try:
                record_count = self.process_csv_file(file_path)
                results['files_processed'] += 1
                results['total_records'] += record_count
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                results['errors'] += 1
        
        logger.info(f"ETL pipeline completed. Results: {results}")
        return results

def main():
    """Main entry point."""
    try:
        etl = ETLPipeline()
        results = etl.run_full_etl()
        
        print(f"\nETL Pipeline Results:")
        print(f"Files processed: {results['files_processed']}")
        print(f"Total records: {results['total_records']}")
        print(f"Errors: {results['errors']}")
        
    except Exception as e:
        logger.error(f"ETL pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()