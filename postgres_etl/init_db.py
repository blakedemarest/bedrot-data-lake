#!/usr/bin/env python3
"""
Database initialization script for BEDROT Data Lake PostgreSQL system.
Creates database, applies schema, and sets up initial configuration.
"""

import os
import sys
import logging
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseInitializer:
    def __init__(self):
        self.host = os.getenv('POSTGRES_HOST', 'localhost')
        self.port = os.getenv('POSTGRES_PORT', '5432')
        self.admin_user = os.getenv('POSTGRES_ADMIN_USER', 'postgres')
        self.admin_password = os.getenv('POSTGRES_ADMIN_PASSWORD')
        self.database = os.getenv('POSTGRES_DB', 'bedrot_analytics')
        self.app_user = os.getenv('POSTGRES_USER', 'bedrot_app')
        self.app_password = os.getenv('POSTGRES_PASSWORD')
        
        if not all([self.admin_password, self.app_password]):
            raise ValueError("Required environment variables not set. Check POSTGRES_ADMIN_PASSWORD and POSTGRES_PASSWORD")
    
    def create_database_and_user(self):
        """Create database and application user if they don't exist."""
        try:
            # Connect as admin to create database and user
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.admin_user,
                password=self.admin_password,
                dbname='postgres'  # Connect to default postgres db
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Create database
            cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{self.database}'")
            exists = cursor.fetchone()
            if not exists:
                cursor.execute(f'CREATE DATABASE "{self.database}"')
                logger.info(f"Created database: {self.database}")
            else:
                logger.info(f"Database {self.database} already exists")
            
            # Create user
            cursor.execute(f"SELECT 1 FROM pg_roles WHERE rolname = '{self.app_user}'")
            exists = cursor.fetchone()
            if not exists:
                cursor.execute(f"CREATE USER {self.app_user} WITH PASSWORD '{self.app_password}'")
                logger.info(f"Created user: {self.app_user}")
            else:
                logger.info(f"User {self.app_user} already exists")
                # Update password in case it changed
                cursor.execute(f"ALTER USER {self.app_user} WITH PASSWORD '{self.app_password}'")
            
            # Grant permissions
            cursor.execute(f'GRANT ALL PRIVILEGES ON DATABASE "{self.database}" TO {self.app_user}')
            logger.info(f"Granted privileges to {self.app_user}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error creating database/user: {e}")
            raise
    
    def apply_schema(self):
        """Apply the schema to the database."""
        try:
            # Connect as admin to create schema and objects
            admin_conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.admin_user,
                password=self.admin_password,
                dbname=self.database
            )
            admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            admin_cursor = admin_conn.cursor()
            
            # Read and execute schema file as admin
            schema_file = Path(__file__).parent / 'schema.sql'
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            admin_cursor.execute(schema_sql)
            logger.info("Applied database schema successfully")
            
            # Grant all permissions on schema to app user
            admin_cursor.execute(f'GRANT USAGE ON SCHEMA bedrot_analytics TO {self.app_user}')
            admin_cursor.execute(f'GRANT CREATE ON SCHEMA bedrot_analytics TO {self.app_user}')
            admin_cursor.execute(f'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA bedrot_analytics TO {self.app_user}')
            admin_cursor.execute(f'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA bedrot_analytics TO {self.app_user}')
            admin_cursor.execute(f'GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA bedrot_analytics TO {self.app_user}')
            admin_cursor.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA bedrot_analytics GRANT ALL ON TABLES TO {self.app_user}')
            admin_cursor.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA bedrot_analytics GRANT ALL ON SEQUENCES TO {self.app_user}')
            admin_cursor.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA bedrot_analytics GRANT ALL ON FUNCTIONS TO {self.app_user}')
            
            admin_cursor.close()
            admin_conn.close()
            
        except Exception as e:
            logger.error(f"Error applying schema: {e}")
            raise
    
    def verify_setup(self):
        """Verify the database setup is working."""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.app_user,
                password=self.app_password,
                dbname=self.database
            )
            cursor = conn.cursor()
            
            # Test basic operations
            cursor.execute("SELECT COUNT(*) FROM bedrot_analytics.data_sources")
            count = cursor.fetchone()[0]
            logger.info(f"Database verification successful. data_sources table has {count} rows")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Database verification failed: {e}")
            raise
    
    def initialize(self):
        """Run full database initialization."""
        logger.info("Starting database initialization...")
        
        self.create_database_and_user()
        self.apply_schema()
        self.verify_setup()
        
        logger.info("Database initialization completed successfully!")

def main():
    """Main entry point."""
    try:
        initializer = DatabaseInitializer()
        initializer.initialize()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()