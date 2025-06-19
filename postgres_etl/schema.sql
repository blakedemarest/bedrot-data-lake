-- BEDROT Data Lake PostgreSQL Schema
-- Designed for semi-structured analytics data with JSONB support

-- Create main database schema
CREATE SCHEMA IF NOT EXISTS bedrot_analytics;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Meta table to track data sources and ingestion status
CREATE TABLE bedrot_analytics.data_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name VARCHAR(100) NOT NULL UNIQUE,
    source_type VARCHAR(50) NOT NULL, -- 'streaming', 'social', 'advertising', 'financial'
    file_path TEXT NOT NULL,
    schema_version INTEGER DEFAULT 1,
    last_ingested_at TIMESTAMP WITH TIME ZONE,
    row_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Core analytics table with flexible JSONB structure
CREATE TABLE bedrot_analytics.insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID NOT NULL REFERENCES bedrot_analytics.data_sources(id),
    
    -- Common structured fields for efficient querying
    date_recorded DATE NOT NULL,
    metric_type VARCHAR(50) NOT NULL, -- 'streams', 'views', 'clicks', 'spend', etc.
    entity_name VARCHAR(200), -- artist name, campaign name, platform name
    platform VARCHAR(50), -- 'spotify', 'tiktok', 'instagram', 'linktree', etc.
    
    -- Flexible JSONB for all data attributes
    raw_data JSONB NOT NULL,
    
    -- Computed insights (can be populated by transformation logic)
    computed_metrics JSONB,
    
    -- Metadata
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    file_source VARCHAR(500), -- original file path for audit trail
    hash_key VARCHAR(64) -- for deduplication
);

-- Streaming-specific view for easy access to music streaming data
CREATE VIEW bedrot_analytics.streaming_insights AS
SELECT 
    i.id,
    i.date_recorded,
    i.entity_name as artist_name,
    i.platform,
    (i.raw_data->>'spotify_streams')::INTEGER as spotify_streams,
    (i.raw_data->>'apple_streams')::INTEGER as apple_streams,
    (i.raw_data->>'combined_streams')::INTEGER as combined_streams,
    i.raw_data->>'source' as data_source,
    i.ingested_at,
    i.file_source
FROM bedrot_analytics.insights i
WHERE i.metric_type = 'streams';

-- Social media analytics view
CREATE VIEW bedrot_analytics.social_insights AS
SELECT 
    i.id,
    i.date_recorded,
    i.platform,
    (i.raw_data->>'totalViews')::INTEGER as total_views,
    (i.raw_data->>'uniqueViews')::INTEGER as unique_views,
    (i.raw_data->>'totalClicks')::INTEGER as total_clicks,
    (i.raw_data->>'uniqueClicks')::INTEGER as unique_clicks,
    (i.raw_data->>'clickThroughRate')::DECIMAL as click_through_rate,
    i.raw_data,
    i.ingested_at,
    i.file_source
FROM bedrot_analytics.insights i
WHERE i.metric_type IN ('views', 'clicks', 'engagement');

-- Advertising insights view for complex campaign data
CREATE VIEW bedrot_analytics.advertising_insights AS
SELECT 
    i.id,
    i.date_recorded,
    i.entity_name as campaign_name,
    i.platform,
    (i.raw_data->>'spend')::DECIMAL as spend,
    (i.raw_data->>'impressions')::INTEGER as impressions,
    (i.raw_data->>'clicks')::INTEGER as clicks,
    (i.raw_data->>'cpc')::DECIMAL as cost_per_click,
    (i.raw_data->>'ctr')::DECIMAL as click_through_rate,
    (i.raw_data->>'reach')::INTEGER as reach,
    i.raw_data->'targeting' as targeting_data,
    i.raw_data,
    i.ingested_at,
    i.file_source
FROM bedrot_analytics.insights i
WHERE i.metric_type = 'advertising';

-- Indexes for performance
CREATE INDEX idx_insights_date_recorded ON bedrot_analytics.insights(date_recorded);
CREATE INDEX idx_insights_metric_type ON bedrot_analytics.insights(metric_type);
CREATE INDEX idx_insights_platform ON bedrot_analytics.insights(platform);
CREATE INDEX idx_insights_source_id ON bedrot_analytics.insights(source_id);
CREATE UNIQUE INDEX idx_insights_hash_key ON bedrot_analytics.insights(hash_key);
CREATE INDEX idx_insights_raw_data_gin ON bedrot_analytics.insights USING GIN(raw_data);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION bedrot_analytics.update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update timestamps
CREATE TRIGGER update_data_sources_modtime 
    BEFORE UPDATE ON bedrot_analytics.data_sources 
    FOR EACH ROW EXECUTE FUNCTION bedrot_analytics.update_modified_column();

-- Function for intelligent data type detection and conversion
CREATE OR REPLACE FUNCTION bedrot_analytics.safe_cast_to_numeric(input_text TEXT)
RETURNS NUMERIC AS $$
BEGIN
    RETURN input_text::NUMERIC;
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to extract date patterns from various formats
CREATE OR REPLACE FUNCTION bedrot_analytics.parse_flexible_date(input_text TEXT)
RETURNS DATE AS $$
BEGIN
    -- Try standard ISO format first
    BEGIN
        RETURN input_text::DATE;
    EXCEPTION WHEN OTHERS THEN
        NULL;
    END;
    
    -- Try MM/DD/YYYY format
    BEGIN
        RETURN TO_DATE(input_text, 'MM/DD/YYYY');
    EXCEPTION WHEN OTHERS THEN
        NULL;
    END;
    
    -- Try other common formats as needed
    RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;