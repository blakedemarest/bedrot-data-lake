#!/usr/bin/env python3
"""
File Watcher for BEDROT Data Lake CSV-to-Tables ETL.
Monitors the curated/ directory for new CSV files and automatically processes them.
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Set, Dict, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from csv_to_tables_etl import CSVToTablesETL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CSVFileHandler(FileSystemEventHandler):
    """Handles file system events for CSV files."""
    
    def __init__(self, etl_pipeline: CSVToTablesETL):
        self.etl_pipeline = etl_pipeline
        self.processed_files: Set[str] = set()
        self.debounce_time = 2  # seconds to wait before processing
        self.pending_files: Dict[str, float] = {}
    
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory and event.src_path.endswith('.csv'):
            logger.info(f"New CSV file detected: {event.src_path}")
            self.schedule_file_processing(event.src_path)
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory and event.src_path.endswith('.csv'):
            logger.info(f"CSV file modified: {event.src_path}")
            self.schedule_file_processing(event.src_path)
    
    def on_moved(self, event):
        """Handle file move events."""
        if not event.is_directory and event.dest_path.endswith('.csv'):
            logger.info(f"CSV file moved to: {event.dest_path}")
            self.schedule_file_processing(event.dest_path)
    
    def schedule_file_processing(self, file_path: str):
        """Schedule file processing with debouncing."""
        self.pending_files[file_path] = time.time()
    
    def process_pending_files(self):
        """Process files that have been pending for longer than debounce_time."""
        current_time = time.time()
        files_to_process = []
        
        for file_path, scheduled_time in list(self.pending_files.items()):
            if current_time - scheduled_time >= self.debounce_time:
                files_to_process.append(file_path)
                del self.pending_files[file_path]
        
        for file_path in files_to_process:
            self.process_csv_file(file_path)
    
    def process_csv_file(self, file_path: str):
        """Process a single CSV file."""
        try:
            if file_path in self.processed_files:
                logger.info(f"File {file_path} already processed recently, skipping")
                return
            
            path_obj = Path(file_path)
            
            # Check if file exists and is readable
            if not path_obj.exists():
                logger.warning(f"File {file_path} no longer exists")
                return
            
            if not path_obj.is_file():
                logger.warning(f"Path {file_path} is not a file")
                return
            
            # Check if file is within the curated directory
            try:
                path_obj.relative_to(self.etl_pipeline.curated_dir)
            except ValueError:
                logger.warning(f"File {file_path} is not within curated directory")
                return
            
            logger.info(f"Processing new CSV file: {file_path}")
            
            # Process the file
            table_name = self.etl_pipeline.create_table_from_csv(path_obj)
            
            if table_name:
                logger.info(f"Successfully processed {file_path} -> table: {table_name}")
                self.processed_files.add(file_path)
            else:
                logger.warning(f"Failed to process {file_path}")
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")

class FileWatcher:
    """Main file watcher class."""
    
    def __init__(self, curated_dir: str = None):
        self.etl_pipeline = CSVToTablesETL(curated_dir)
        self.curated_dir = self.etl_pipeline.curated_dir
        self.observer = Observer()
        self.event_handler = CSVFileHandler(self.etl_pipeline)
        self.running = False
    
    def start(self):
        """Start the file watcher."""
        logger.info(f"Starting file watcher for directory: {self.curated_dir}")
        
        # Ensure the directory exists
        if not self.curated_dir.exists():
            logger.error(f"Curated directory does not exist: {self.curated_dir}")
            return False
        
        # Process existing files first
        logger.info("Processing existing CSV files...")
        try:
            results = self.etl_pipeline.run_full_etl()
            logger.info(f"Initial processing complete: {results}")
        except Exception as e:
            logger.error(f"Error during initial processing: {e}")
        
        # Start watching for new files
        self.observer.schedule(
            self.event_handler,
            str(self.curated_dir),
            recursive=True
        )
        
        self.observer.start()
        self.running = True
        
        logger.info("File watcher started. Monitoring for new CSV files...")
        
        try:
            while self.running:
                # Process pending files
                self.event_handler.process_pending_files()
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, stopping...")
            self.stop()
        
        return True
    
    def stop(self):
        """Stop the file watcher."""
        logger.info("Stopping file watcher...")
        self.running = False
        self.observer.stop()
        self.observer.join()
        logger.info("File watcher stopped")
    
    def run_once(self):
        """Run the ETL process once without watching."""
        logger.info("Running CSV-to-Tables ETL once...")
        try:
            results = self.etl_pipeline.run_full_etl()
            logger.info(f"ETL processing complete: {results}")
            return results
        except Exception as e:
            logger.error(f"Error during ETL processing: {e}")
            raise

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='BEDROT Data Lake CSV File Watcher')
    parser.add_argument('--once', action='store_true', 
                       help='Run once instead of continuous monitoring')
    parser.add_argument('--curated-dir', type=str,
                       help='Path to curated directory (overrides env var)')
    
    args = parser.parse_args()
    
    try:
        watcher = FileWatcher(args.curated_dir)
        
        if args.once:
            results = watcher.run_once()
            print(f"\nProcessing Results:")
            print(f"Files processed: {results['files_processed']}")
            print(f"Tables created: {results['tables_created']}")
            print(f"Tables updated: {results['tables_updated']}")
            print(f"Total records: {results['total_records']}")
            print(f"Errors: {results['errors']}")
        else:
            watcher.start()
            
    except Exception as e:
        logger.error(f"File watcher failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()