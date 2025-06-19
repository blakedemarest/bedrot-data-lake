#!/usr/bin/env python3
"""
CSV-to-Tables ETL Pipeline for BEDROT Data Lake.
Automatically creates individual PostgreSQL tables for each CSV file in curated/.
Each table matches the CSV schema exactly with identical column names and data types.
"""

import os
import sys
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CSVSchemaDetector:
    """Detects and generates PostgreSQL schema from CSV files."""
    
    @staticmethod
    def detect_column_type(series: pd.Series, column_name: str) -> str:
        """Detect the appropriate PostgreSQL data type for a pandas Series."""
        # Remove nulls for type detection
        non_null_series = series.dropna()
        
        if len(non_null_series) == 0:
            return "TEXT"  # Default for all-null columns
        
        # Check for date patterns first
        if CSVSchemaDetector._is_date_column(non_null_series, column_name):
            return "DATE"
        
        # Check for timestamp patterns
        if CSVSchemaDetector._is_timestamp_column(non_null_series, column_name):
            return "TIMESTAMP"
        
        # Check for boolean
        if CSVSchemaDetector._is_boolean_column(non_null_series):
            return "BOOLEAN"
        
        # Check for integer
        if CSVSchemaDetector._is_integer_column(non_null_series):
            return "INTEGER"
        
        # Check for decimal/float
        if CSVSchemaDetector._is_decimal_column(non_null_series):
            return "DECIMAL(15,6)"
        
        # Default to TEXT with appropriate length
        max_length = max(len(str(val)) for val in non_null_series)
        if max_length <= 255:
            return "VARCHAR(255)"
        else:
            return "TEXT"
    
    @staticmethod
    def _is_date_column(series: pd.Series, column_name: str) -> bool:
        """Check if column contains date values."""
        date_indicators = ['date', 'day', 'created', 'updated']
        if any(indicator in column_name.lower() for indicator in date_indicators):
            # Try to parse a few values as dates
            sample_size = min(10, len(series))
            successful_parses = 0
            
            for val in series.head(sample_size):
                try:
                    pd.to_datetime(str(val))
                    successful_parses += 1
                except:
                    continue
            
            return successful_parses > sample_size * 0.7
        
        return False
    
    @staticmethod
    def _is_timestamp_column(series: pd.Series, column_name: str) -> bool:
        """Check if column contains timestamp values."""
        timestamp_indicators = ['time', 'timestamp', 'created_at', 'updated_at']
        if any(indicator in column_name.lower() for indicator in timestamp_indicators):
            # Check if values have time components
            sample_val = str(series.iloc[0])
            return 'T' in sample_val or ':' in sample_val
        
        return False
    
    @staticmethod
    def _is_boolean_column(series: pd.Series) -> bool:
        """Check if column contains boolean values."""
        unique_vals = set(str(val).lower() for val in series.unique())
        boolean_sets = [
            {'true', 'false'},
            {'yes', 'no'},
            {'1', '0'},
            {'t', 'f'}
        ]
        
        return any(unique_vals.issubset(bool_set) or unique_vals == bool_set for bool_set in boolean_sets)
    
    @staticmethod
    def _is_integer_column(series: pd.Series) -> bool:
        """Check if column contains integer values."""
        try:
            # Convert to numeric and check if all values are integers
            numeric_series = pd.to_numeric(series, errors='coerce')
            if numeric_series.isna().all():
                return False
            
            # Check if all non-null values are integers
            return (numeric_series.dropna() == numeric_series.dropna().astype(int)).all()
        except:
            return False
    
    @staticmethod
    def _is_decimal_column(series: pd.Series) -> bool:
        """Check if column contains decimal/float values."""
        try:
            numeric_series = pd.to_numeric(series, errors='coerce')
            return not numeric_series.isna().all()
        except:
            return False
    
    @staticmethod
    def generate_table_schema(df: pd.DataFrame, table_name: str) -> str:
        """Generate CREATE TABLE SQL statement from DataFrame."""
        columns = []
        
        for column in df.columns:
            # Clean column name for SQL
            clean_column = CSVSchemaDetector.clean_column_name(column)
            column_type = CSVSchemaDetector.detect_column_type(df[column], column)
            columns.append(f"    {clean_column} {column_type}")
        
        # Add metadata columns
        columns.extend([
            "    _ingested_at TIMESTAMP DEFAULT NOW()",
            "    _file_source VARCHAR(500)",
            "    _row_hash VARCHAR(64)"
        ])
        
        schema_sql = f"""
CREATE TABLE IF NOT EXISTS bedrot_analytics.{table_name} (
    id SERIAL PRIMARY KEY,
{','.join(columns)}
);

-- Create index on ingestion timestamp
CREATE INDEX IF NOT EXISTS idx_{table_name}_ingested_at ON bedrot_analytics.{table_name}(_ingested_at);

-- Create unique constraint on row hash for deduplication
CREATE UNIQUE INDEX IF NOT EXISTS idx_{table_name}_row_hash ON bedrot_analytics.{table_name}(_row_hash);
"""
        
        return schema_sql
    
    @staticmethod
    def clean_column_name(column_name: str) -> str:
        """Clean column name to be SQL-safe."""
        # Replace spaces and special characters with underscores
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', column_name)
        # Remove multiple underscores
        clean_name = re.sub(r'_+', '_', clean_name)
        # Remove leading/trailing underscores
        clean_name = clean_name.strip('_')
        # Ensure it starts with a letter
        if clean_name and clean_name[0].isdigit():
            clean_name = f"col_{clean_name}"
        # Convert to lowercase
        return clean_name.lower()

class CSVToTablesETL:
    """Main ETL pipeline for CSV-to-table conversion."""
    
    def __init__(self, curated_dir: str = None):
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
    
    def generate_table_name(self, file_path: Path) -> str:
        """Generate a table name from file path."""
        # Use parent directory and filename
        if file_path.parent.name != 'curated':
            # Include subdirectory in table name
            table_name = f"{file_path.parent.name}_{file_path.stem}"
        else:
            table_name = file_path.stem
        
        # Clean table name
        table_name = CSVSchemaDetector.clean_column_name(table_name)
        
        # Ensure unique and valid table name
        return table_name
    
    def create_table_from_csv(self, file_path: Path) -> str:
        """Create a PostgreSQL table from a CSV file."""
        logger.info(f"Processing CSV file: {file_path}")
        
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            
            if df.empty:
                logger.warning(f"File {file_path} is empty, skipping")
                return None
            
            # Generate table name
            table_name = self.generate_table_name(file_path)
            
            # Generate schema
            schema_sql = CSVSchemaDetector.generate_table_schema(df, table_name)
            
            # Execute schema creation
            with self.get_database_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(schema_sql)
                    conn.commit()
            
            logger.info(f"Created table: bedrot_analytics.{table_name}")
            
            # Insert data
            self.insert_csv_data(df, table_name, file_path)
            
            return table_name
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise
    
    def insert_csv_data(self, df: pd.DataFrame, table_name: str, file_path: Path):
        """Insert CSV data into the created table."""
        logger.info(f"Inserting data into table: {table_name}")
        
        with self.get_database_connection() as conn:
            with conn.cursor() as cursor:
                # Get column names from DataFrame
                columns = [CSVSchemaDetector.clean_column_name(col) for col in df.columns]
                
                # Prepare insert statement
                placeholders = ', '.join(['%s'] * len(columns))
                column_names = ', '.join(columns)
                
                insert_sql = f"""
                INSERT INTO bedrot_analytics.{table_name} 
                ({column_names}, _file_source, _row_hash)
                VALUES ({placeholders}, %s, %s)
                ON CONFLICT (_row_hash) DO UPDATE SET
                    _ingested_at = NOW()
                """
                
                # Prepare data for insertion
                rows_to_insert = []
                for _, row in df.iterrows():
                    row_values = []
                    for col in df.columns:
                        val = row[col]
                        # Handle NaN values
                        if pd.isna(val):
                            row_values.append(None)
                        else:
                            row_values.append(val)
                    
                    # Add metadata
                    file_source = str(file_path.relative_to(self.curated_dir.parent))
                    row_hash = self.generate_row_hash(row_values, file_source)
                    
                    row_values.extend([file_source, row_hash])
                    rows_to_insert.append(tuple(row_values))
                
                # Execute batch insert
                cursor.executemany(insert_sql, rows_to_insert)
                conn.commit()
                
                logger.info(f"Inserted {len(rows_to_insert)} rows into {table_name}")
    
    def generate_row_hash(self, row_values: List[Any], file_source: str) -> str:
        """Generate a hash for row deduplication."""
        import hashlib
        import json
        
        hash_data = {
            'values': str(row_values),
            'source': file_source
        }
        
        hash_string = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def get_existing_tables(self) -> List[str]:
        """Get list of existing tables in bedrot_analytics schema."""
        with self.get_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'bedrot_analytics'
                    AND table_type = 'BASE TABLE'
                """)
                return [row[0] for row in cursor.fetchall()]
    
    def run_full_etl(self) -> Dict[str, Any]:
        """Run the complete CSV-to-tables ETL pipeline."""
        logger.info("Starting CSV-to-Tables ETL pipeline...")
        
        # Discover CSV files
        csv_files = self.discover_csv_files()
        logger.info(f"Found {len(csv_files)} CSV files to process")
        
        # Get existing tables
        existing_tables = self.get_existing_tables()
        logger.info(f"Found {len(existing_tables)} existing tables")
        
        results = {
            'files_processed': 0,
            'tables_created': 0,
            'tables_updated': 0,
            'total_records': 0,
            'errors': 0,
            'table_names': []
        }
        
        # Process each file
        for file_path in csv_files:
            try:
                table_name = self.generate_table_name(file_path)
                
                if table_name in existing_tables:
                    logger.info(f"Table {table_name} already exists, updating data...")
                    results['tables_updated'] += 1
                else:
                    logger.info(f"Creating new table: {table_name}")
                    results['tables_created'] += 1
                
                created_table = self.create_table_from_csv(file_path)
                if created_table:
                    results['files_processed'] += 1
                    results['table_names'].append(created_table)
                    
                    # Count records in the file
                    df = pd.read_csv(file_path)
                    results['total_records'] += len(df)
                
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                results['errors'] += 1
        
        logger.info(f"ETL pipeline completed. Results: {results}")
        return results

def main():
    """Main entry point."""
    try:
        etl = CSVToTablesETL()
        results = etl.run_full_etl()
        
        print(f"\nCSV-to-Tables ETL Pipeline Results:")
        print(f"Files processed: {results['files_processed']}")
        print(f"Tables created: {results['tables_created']}")
        print(f"Tables updated: {results['tables_updated']}")
        print(f"Total records: {results['total_records']}")
        print(f"Errors: {results['errors']}")
        print(f"\nTables created/updated:")
        for table_name in results['table_names']:
            print(f"  - bedrot_analytics.{table_name}")
        
    except Exception as e:
        logger.error(f"ETL pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()