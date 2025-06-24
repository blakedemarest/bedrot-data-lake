-- Create bedrot_app user and grant permissions
-- This file is mounted as /docker-entrypoint-initdb.d/02-user.sql

-- Create the application user
CREATE USER bedrot_app WITH PASSWORD 'bedrot_app_2025';

-- Grant database-level privileges
GRANT ALL PRIVILEGES ON DATABASE bedrot_analytics TO bedrot_app;
ALTER USER bedrot_app CREATEDB;

-- Connect to the target database to grant schema/table privileges
\c bedrot_analytics

-- Grant schema privileges
GRANT ALL PRIVILEGES ON SCHEMA bedrot_analytics TO bedrot_app;
GRANT ALL PRIVILEGES ON SCHEMA public TO bedrot_app;

-- Grant privileges on existing tables and sequences
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA bedrot_analytics TO bedrot_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA bedrot_analytics TO bedrot_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO bedrot_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO bedrot_app;

-- Grant default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA bedrot_analytics GRANT ALL PRIVILEGES ON TABLES TO bedrot_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA bedrot_analytics GRANT ALL PRIVILEGES ON SEQUENCES TO bedrot_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO bedrot_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO bedrot_app;

-- Verify user creation
SELECT 'User bedrot_app created successfully' as status;