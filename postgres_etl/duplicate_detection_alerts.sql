-- Duplicate Detection Alert System for BEDROT Data Lake
-- Implements triggers and monitoring functions to detect and alert on duplicate entries

-- Create a function to log duplicate detection alerts
CREATE OR REPLACE FUNCTION bedrot_analytics.log_duplicate_alert(
    table_name TEXT,
    duplicate_columns TEXT[],
    duplicate_count INTEGER,
    sample_values TEXT
) RETURNS VOID AS $$
BEGIN
    -- Log to a dedicated alerts table
    INSERT INTO bedrot_analytics.duplicate_alerts (
        detected_at,
        table_name,
        duplicate_columns,
        duplicate_count,
        sample_values,
        alert_level
    ) VALUES (
        NOW(),
        table_name,
        duplicate_columns,
        duplicate_count,
        sample_values,
        CASE 
            WHEN duplicate_count > 100 THEN 'CRITICAL'
            WHEN duplicate_count > 10 THEN 'HIGH'
            ELSE 'MEDIUM'
        END
    );
    
    -- Raise a notice (will appear in logs)
    RAISE NOTICE 'DUPLICATE ALERT: Table % has % duplicate records on columns %. Sample: %', 
        table_name, duplicate_count, array_to_string(duplicate_columns, ', '), sample_values;
        
    -- For critical alerts, also raise a warning
    IF duplicate_count > 100 THEN
        RAISE WARNING 'CRITICAL DUPLICATE ALERT: Table % has % duplicate records', table_name, duplicate_count;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create the duplicate_alerts table if it doesn't exist
CREATE TABLE IF NOT EXISTS bedrot_analytics.duplicate_alerts (
    id SERIAL PRIMARY KEY,
    detected_at TIMESTAMP DEFAULT NOW(),
    table_name TEXT NOT NULL,
    duplicate_columns TEXT[] NOT NULL,
    duplicate_count INTEGER NOT NULL,
    sample_values TEXT,
    alert_level TEXT CHECK (alert_level IN ('MEDIUM', 'HIGH', 'CRITICAL')),
    resolved_at TIMESTAMP NULL,
    notes TEXT
);

-- Create index for efficient querying
CREATE INDEX IF NOT EXISTS idx_duplicate_alerts_table_time 
ON bedrot_analytics.duplicate_alerts (table_name, detected_at DESC);

-- Function to check for duplicates in any table
CREATE OR REPLACE FUNCTION bedrot_analytics.check_table_duplicates(
    target_table TEXT,
    check_columns TEXT[]
) RETURNS INTEGER AS $$
DECLARE
    duplicate_count INTEGER;
    sample_record TEXT;
    sql_query TEXT;
BEGIN
    -- Build dynamic SQL to check for duplicates
    sql_query := format('
        WITH duplicate_check AS (
            SELECT %s, COUNT(*) as cnt
            FROM %s 
            GROUP BY %s 
            HAVING COUNT(*) > 1
        )
        SELECT COUNT(*), 
               COALESCE(string_agg((%s)::TEXT, '', ''), ''No duplicates'') as sample
        FROM duplicate_check',
        array_to_string(check_columns, ', '),
        target_table,
        array_to_string(check_columns, ', '),
        array_to_string(check_columns, ', ')
    );
    
    EXECUTE sql_query INTO duplicate_count, sample_record;
    
    -- If duplicates found, log alert
    IF duplicate_count > 0 THEN
        PERFORM bedrot_analytics.log_duplicate_alert(
            target_table,
            check_columns,
            duplicate_count,
            sample_record
        );
    END IF;
    
    RETURN duplicate_count;
END;
$$ LANGUAGE plpgsql;

-- Create a monitoring job function to check all tables
CREATE OR REPLACE FUNCTION bedrot_analytics.monitor_all_duplicates() RETURNS TABLE(
    table_name TEXT,
    duplicate_count INTEGER,
    check_columns TEXT[]
) AS $$
DECLARE
    tbl RECORD;
    dup_count INTEGER;
BEGIN
    -- Check insights table (main data table)
    SELECT bedrot_analytics.check_table_duplicates(
        'bedrot_analytics.insights',
        ARRAY['source_id', 'date_recorded']
    ) INTO dup_count;
    
    IF dup_count > 0 THEN
        table_name := 'insights';
        duplicate_count := dup_count;
        check_columns := ARRAY['source_id', 'date_recorded'];
        RETURN NEXT;
    END IF;
    
    -- Check individual data tables for common duplicate patterns
    FOR tbl IN 
        SELECT t.table_name 
        FROM information_schema.tables t 
        WHERE t.table_schema = 'bedrot_analytics' 
        AND t.table_type = 'BASE TABLE'
        AND t.table_name NOT IN ('data_sources', 'duplicate_alerts', 'insights')
    LOOP
        -- Check for date-based duplicates (most common pattern)
        IF EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'bedrot_analytics' 
            AND table_name = tbl.table_name 
            AND column_name = 'date'
        ) THEN
            SELECT bedrot_analytics.check_table_duplicates(
                'bedrot_analytics.' || tbl.table_name,
                ARRAY['date']
            ) INTO dup_count;
            
            IF dup_count > 0 THEN
                table_name := tbl.table_name;
                duplicate_count := dup_count;
                check_columns := ARRAY['date'];
                RETURN NEXT;
            END IF;
        END IF;
        
        -- For Spotify tables, check artist_name + date
        IF tbl.table_name LIKE '%spotify%' THEN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'bedrot_analytics' 
                AND table_name = tbl.table_name 
                AND column_name = 'artist_name'
            ) THEN
                SELECT bedrot_analytics.check_table_duplicates(
                    'bedrot_analytics.' || tbl.table_name,
                    ARRAY['artist_name', 'date']
                ) INTO dup_count;
                
                IF dup_count > 0 THEN
                    table_name := tbl.table_name;
                    duplicate_count := dup_count;
                    check_columns := ARRAY['artist_name', 'date'];
                    RETURN NEXT;
                END IF;
            END IF;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger function for real-time duplicate detection on insights table
CREATE OR REPLACE FUNCTION bedrot_analytics.trigger_duplicate_check() RETURNS TRIGGER AS $$
DECLARE
    dup_count INTEGER;
BEGIN
    -- Check if the inserted/updated record creates duplicates
    SELECT COUNT(*) INTO dup_count
    FROM bedrot_analytics.insights 
    WHERE source_id = NEW.source_id 
    AND date_recorded = NEW.date_recorded;
    
    -- If more than 1 record exists (including the new one), we have duplicates
    IF dup_count > 1 THEN
        PERFORM bedrot_analytics.log_duplicate_alert(
            'insights',
            ARRAY['source_id', 'date_recorded'],
            dup_count,
            format('source_id: %s, date: %s', NEW.source_id, NEW.date_recorded)
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger on insights table
DROP TRIGGER IF EXISTS trigger_insights_duplicate_check ON bedrot_analytics.insights;
CREATE TRIGGER trigger_insights_duplicate_check
    AFTER INSERT OR UPDATE ON bedrot_analytics.insights
    FOR EACH ROW EXECUTE FUNCTION bedrot_analytics.trigger_duplicate_check();

-- Create a view for easy monitoring
CREATE OR REPLACE VIEW bedrot_analytics.duplicate_monitoring AS
SELECT 
    da.detected_at,
    da.table_name,
    da.duplicate_columns,
    da.duplicate_count,
    da.alert_level,
    da.sample_values,
    da.resolved_at,
    CASE 
        WHEN da.resolved_at IS NULL THEN 'OPEN'
        ELSE 'RESOLVED'
    END as status
FROM bedrot_analytics.duplicate_alerts da
ORDER BY da.detected_at DESC;

-- Grant permissions
GRANT SELECT ON bedrot_analytics.duplicate_alerts TO bedrot_app;
GRANT SELECT ON bedrot_analytics.duplicate_monitoring TO bedrot_app;
GRANT EXECUTE ON FUNCTION bedrot_analytics.monitor_all_duplicates() TO bedrot_app;

-- Add helpful comments
COMMENT ON TABLE bedrot_analytics.duplicate_alerts IS 'Stores alerts for duplicate data detection across all tables';
COMMENT ON FUNCTION bedrot_analytics.monitor_all_duplicates() IS 'Runs comprehensive duplicate check across all data tables';
COMMENT ON VIEW bedrot_analytics.duplicate_monitoring IS 'Easy-to-query view for monitoring duplicate alerts';

-- Usage examples (commented out - uncomment to test):
-- SELECT * FROM bedrot_analytics.monitor_all_duplicates();
-- SELECT * FROM bedrot_analytics.duplicate_monitoring WHERE status = 'OPEN';
-- SELECT table_name, COUNT(*) as alert_count FROM bedrot_analytics.duplicate_alerts GROUP BY table_name;