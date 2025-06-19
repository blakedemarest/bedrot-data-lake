#!/usr/bin/env python3
"""
Test script to demonstrate CSV schema detection without external dependencies.
Shows how the CSV-to-tables system would analyze your CSV files.
"""

import os
import sys
from pathlib import Path

def analyze_csv_structure(file_path):
    """Analyze CSV structure using basic Python."""
    print(f"\nAnalyzing: {file_path}")
    print("-" * 50)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read header
            header = f.readline().strip()
            columns = [col.strip() for col in header.split(',')]
            
            print(f"Columns found: {len(columns)}")
            for i, col in enumerate(columns, 1):
                print(f"  {i}. {col}")
            
            # Read a few sample rows
            print(f"\nSample data:")
            for i, line in enumerate(f):
                if i >= 3:  # Show first 3 data rows
                    break
                values = [val.strip() for val in line.strip().split(',')]
                print(f"  Row {i+1}: {values}")
            
            # Generate proposed table name
            table_name = Path(file_path).stem.lower().replace(' ', '_').replace('-', '_')
            if Path(file_path).parent.name != 'curated':
                parent_name = Path(file_path).parent.name.lower().replace(' ', '_').replace('-', '_')
                table_name = f"{parent_name}_{table_name}"
            
            print(f"\nProposed table name: bedrot_analytics.{table_name}")
            
            # Generate basic CREATE TABLE statement
            print(f"\nSQL Schema (estimated):")
            print(f"CREATE TABLE bedrot_analytics.{table_name} (")
            print(f"    id SERIAL PRIMARY KEY,")
            
            for col in columns:
                clean_col = col.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')
                # Simple type detection based on column name
                if 'date' in clean_col.lower():
                    col_type = "DATE"
                elif 'time' in clean_col.lower():
                    col_type = "TIMESTAMP"
                elif any(word in clean_col.lower() for word in ['amount', 'price', 'cost', 'rate', 'percentage']):
                    col_type = "DECIMAL(15,6)"
                elif any(word in clean_col.lower() for word in ['count', 'quantity', 'views', 'clicks', 'streams']):
                    col_type = "INTEGER"
                else:
                    col_type = "VARCHAR(255)"
                
                print(f"    {clean_col} {col_type},")
            
            print(f"    _ingested_at TIMESTAMP DEFAULT NOW(),")
            print(f"    _file_source VARCHAR(500),")
            print(f"    _row_hash VARCHAR(64)")
            print(f");")
            
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")

def main():
    """Main function to analyze CSV files."""
    curated_dir = Path(__file__).parent.parent / 'curated'
    
    print("BEDROT Data Lake - CSV Schema Analysis")
    print("=" * 50)
    print(f"Scanning directory: {curated_dir}")
    
    csv_files = []
    
    # Find all CSV files
    def scan_directory(directory):
        for item in directory.iterdir():
            if item.is_file() and item.suffix.lower() == '.csv':
                csv_files.append(item)
            elif item.is_dir() and not item.name.startswith('.'):
                scan_directory(item)
    
    if curated_dir.exists():
        scan_directory(curated_dir)
        
        print(f"Found {len(csv_files)} CSV files:")
        for i, file_path in enumerate(csv_files, 1):
            print(f"{i}. {file_path.relative_to(curated_dir.parent)}")
        
        # Analyze each file
        for file_path in csv_files:
            analyze_csv_structure(file_path)
    else:
        print(f"Curated directory not found: {curated_dir}")

if __name__ == "__main__":
    main()