-- Voice Feedback Platform - PostgreSQL Schema
-- Option A: Neon PostgreSQL Implementation
-- Version: 1.0.0

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
CREATE EXTENSION IF NOT EXISTS "btree_gin";  -- For GIN indexes

-- ============================================================================
-- TABLE 1: users
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),  -- NULL for OAuth users
    role VARCHAR(50) NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user', 'viewer')),
    auth_provider VARCHAR(50) NOT NULL DEFAULT 'jwt' CHECK (auth_provider IN ('jwt', 'oauth', 'google', 'github')),
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_created_at ON users(created_at);

-- ============================================================================
-- TABLE 2: voice_submissions
-- ============================================================================
CREATE TABLE IF NOT EXISTS voice_submissions (
    submission_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    audio_file_url TEXT,
    audio_file_path TEXT,  -- Local or cloud path
    audio_duration_seconds NUMERIC(10, 2),
    audio_file_size_bytes BIGINT,
    language_code VARCHAR(10) NOT NULL DEFAULT 'en',
    language_detected VARCHAR(10),
    recording_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    upload_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(50) DEFAULT 'pending' CHECK (
        processing_status IN ('pending', 'processing', 'completed', 'failed', 'retry')
    ),
    device_type VARCHAR(50) CHECK (device_type IN ('web', 'chrome', 'ios', 'android')),
    device_info JSONB DEFAULT '{}'::jsonb,
    category_hint VARCHAR(100),  -- User-provided category hint
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for voice_submissions
CREATE INDEX idx_voice_submissions_user_id ON voice_submissions(user_id);
CREATE INDEX idx_voice_submissions_status ON voice_submissions(processing_status);
CREATE INDEX idx_voice_submissions_upload_timestamp ON voice_submissions(upload_timestamp);
CREATE INDEX idx_voice_submissions_recording_timestamp ON voice_submissions(recording_timestamp);
CREATE INDEX idx_voice_submissions_language ON voice_submissions(language_code);
CREATE INDEX idx_voice_submissions_device ON voice_submissions(device_type);

-- Partition by month (example for large-scale deployments)
-- CREATE TABLE voice_submissions_2024_01 PARTITION OF voice_submissions
-- FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- ============================================================================
-- TABLE 3: transcriptions
-- ============================================================================
CREATE TABLE IF NOT EXISTS transcriptions (
    transcription_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    submission_id UUID NOT NULL REFERENCES voice_submissions(submission_id) ON DELETE CASCADE,
    original_text TEXT NOT NULL,
    translated_text TEXT,  -- If not English
    target_language VARCHAR(10) DEFAULT 'en',
    language_detected VARCHAR(10),
    confidence_score NUMERIC(5, 4) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    transcription_engine VARCHAR(50) NOT NULL CHECK (
        transcription_engine IN ('whisper', 'google', 'aws', 'azure', 'deepgram')
    ),
    processing_time_ms INTEGER,
    word_count INTEGER,
    character_count INTEGER,
    audio_quality_score NUMERIC(5, 4),
    metadata JSONB DEFAULT '{}'::jsonb,  -- Engine-specific metadata
    cost_usd NUMERIC(10, 6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for transcriptions
CREATE INDEX idx_transcriptions_submission_id ON transcriptions(submission_id);
CREATE INDEX idx_transcriptions_engine ON transcriptions(transcription_engine);
CREATE INDEX idx_transcriptions_confidence ON transcriptions(confidence_score);
CREATE INDEX idx_transcriptions_language ON transcriptions(language_detected);
-- Full-text search index
CREATE INDEX idx_transcriptions_text_search ON transcriptions USING gin(to_tsvector('english', original_text));

-- ============================================================================
-- TABLE 4: ai_analysis
-- ============================================================================
CREATE TABLE IF NOT EXISTS ai_analysis (
    analysis_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    submission_id UUID NOT NULL REFERENCES voice_submissions(submission_id) ON DELETE CASCADE,
    summary TEXT,
    category_l1 VARCHAR(100),  -- Government, Private, Product, Infrastructure, Health, Other
    category_l2 VARCHAR(100),  -- Subcategory
    category_l3 VARCHAR(100),  -- Specific issue
    sentiment VARCHAR(50) CHECK (sentiment IN ('positive', 'neutral', 'negative', 'mixed')),
    sentiment_score NUMERIC(5, 4) CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
    sentiment_reasoning TEXT,
    urgency_score INTEGER CHECK (urgency_score >= 1 AND urgency_score <= 5),
    urgency_reasoning TEXT,
    entities_extracted JSONB DEFAULT '[]'::jsonb,  -- locations, people, departments
    keywords TEXT[],  -- Array of keywords
    topics TEXT[],  -- Identified topics
    model_used VARCHAR(100) NOT NULL,  -- claude-sonnet, automl, vectorsearch
    model_version VARCHAR(50),
    processing_time_ms INTEGER,
    processing_cost_usd NUMERIC(10, 6),
    confidence_score NUMERIC(5, 4),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for ai_analysis
CREATE INDEX idx_ai_analysis_submission_id ON ai_analysis(submission_id);
CREATE INDEX idx_ai_analysis_category_l1 ON ai_analysis(category_l1);
CREATE INDEX idx_ai_analysis_sentiment ON ai_analysis(sentiment);
CREATE INDEX idx_ai_analysis_urgency ON ai_analysis(urgency_score);
CREATE INDEX idx_ai_analysis_created_at ON ai_analysis(created_at);
-- GIN indexes for arrays and JSONB
CREATE INDEX idx_ai_analysis_keywords ON ai_analysis USING gin(keywords);
CREATE INDEX idx_ai_analysis_topics ON ai_analysis USING gin(topics);
CREATE INDEX idx_ai_analysis_entities ON ai_analysis USING gin(entities_extracted);

-- ============================================================================
-- TABLE 5: sync_metadata
-- ============================================================================
CREATE TABLE IF NOT EXISTS sync_metadata (
    sync_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_table VARCHAR(100) NOT NULL,
    destination_system VARCHAR(50) NOT NULL,  -- databricks, warehouse, etc.
    last_sync_timestamp TIMESTAMP WITH TIME ZONE,
    current_sync_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    records_synced INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    sync_status VARCHAR(50) DEFAULT 'running' CHECK (
        sync_status IN ('running', 'completed', 'failed', 'partial')
    ),
    sync_duration_seconds INTEGER,
    error_message TEXT,
    sync_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for sync_metadata
CREATE INDEX idx_sync_metadata_source_table ON sync_metadata(source_table);
CREATE INDEX idx_sync_metadata_status ON sync_metadata(sync_status);
CREATE INDEX idx_sync_metadata_created_at ON sync_metadata(created_at);

-- ============================================================================
-- TABLE 6: processing_costs
-- ============================================================================
CREATE TABLE IF NOT EXISTS processing_costs (
    cost_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    submission_id UUID REFERENCES voice_submissions(submission_id) ON DELETE CASCADE,
    service_name VARCHAR(100) NOT NULL,  -- whisper, claude, databricks, etc.
    service_type VARCHAR(50) NOT NULL,  -- stt, sentiment, storage, compute
    cost_usd NUMERIC(10, 6) NOT NULL,
    units_consumed NUMERIC(15, 6),  -- minutes, tokens, MB, etc.
    unit_type VARCHAR(50),  -- minutes, tokens, bytes
    billing_period VARCHAR(20),  -- YYYY-MM format
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for processing_costs
CREATE INDEX idx_processing_costs_submission_id ON processing_costs(submission_id);
CREATE INDEX idx_processing_costs_service ON processing_costs(service_name);
CREATE INDEX idx_processing_costs_period ON processing_costs(billing_period);
CREATE INDEX idx_processing_costs_created_at ON processing_costs(created_at);

-- ============================================================================
-- TABLE 7: audit_log
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,  -- login, upload, delete, update, etc.
    resource_type VARCHAR(100),  -- user, submission, analysis
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    request_data JSONB DEFAULT '{}'::jsonb,
    response_status INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for audit_log
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_resource_type ON audit_log(resource_type);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX idx_audit_log_ip_address ON audit_log(ip_address);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on voice_submissions
ALTER TABLE voice_submissions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own submissions
CREATE POLICY user_submissions_select_policy ON voice_submissions
    FOR SELECT
    USING (
        user_id = current_setting('app.user_id', true)::uuid
        OR
        EXISTS (
            SELECT 1 FROM users
            WHERE user_id = current_setting('app.user_id', true)::uuid
            AND role = 'admin'
        )
    );

-- Policy: Users can only insert their own submissions
CREATE POLICY user_submissions_insert_policy ON voice_submissions
    FOR INSERT
    WITH CHECK (user_id = current_setting('app.user_id', true)::uuid);

-- Policy: Users can update their own submissions
CREATE POLICY user_submissions_update_policy ON voice_submissions
    FOR UPDATE
    USING (user_id = current_setting('app.user_id', true)::uuid);

-- Policy: Only admins can delete
CREATE POLICY admin_submissions_delete_policy ON voice_submissions
    FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE user_id = current_setting('app.user_id', true)::uuid
            AND role = 'admin'
        )
    );

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Function: Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_voice_submissions_updated_at
    BEFORE UPDATE ON voice_submissions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_analysis_updated_at
    BEFORE UPDATE ON ai_analysis
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function: Cleanup old audio files
CREATE OR REPLACE FUNCTION cleanup_old_audio(retention_days INTEGER DEFAULT 90)
RETURNS TABLE (submissions_cleaned INTEGER) AS $$
DECLARE
    cleaned_count INTEGER;
BEGIN
    UPDATE voice_submissions
    SET audio_file_url = NULL,
        audio_file_path = NULL,
        updated_at = CURRENT_TIMESTAMP
    WHERE upload_timestamp < CURRENT_DATE - (retention_days || ' days')::INTERVAL
        AND (audio_file_url IS NOT NULL OR audio_file_path IS NOT NULL);

    GET DIAGNOSTICS cleaned_count = ROW_COUNT;
    RETURN QUERY SELECT cleaned_count;
END;
$$ LANGUAGE plpgsql;

-- Function: Get cost summary
CREATE OR REPLACE FUNCTION get_cost_summary(
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE
)
RETURNS TABLE (
    service_name VARCHAR,
    total_cost_usd NUMERIC,
    total_units NUMERIC,
    submission_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        pc.service_name,
        SUM(pc.cost_usd) as total_cost_usd,
        SUM(pc.units_consumed) as total_units,
        COUNT(DISTINCT pc.submission_id) as submission_count
    FROM processing_costs pc
    WHERE pc.created_at BETWEEN start_date AND end_date
    GROUP BY pc.service_name
    ORDER BY total_cost_usd DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Complete submission details with all analysis
CREATE OR REPLACE VIEW v_submissions_complete AS
SELECT
    vs.submission_id,
    vs.user_id,
    u.email,
    u.name as user_name,
    vs.audio_duration_seconds,
    vs.language_code,
    vs.recording_timestamp,
    vs.upload_timestamp,
    vs.processing_status,
    vs.device_type,
    t.original_text,
    t.translated_text,
    t.confidence_score as transcription_confidence,
    t.transcription_engine,
    aa.summary,
    aa.category_l1,
    aa.category_l2,
    aa.category_l3,
    aa.sentiment,
    aa.sentiment_score,
    aa.urgency_score,
    aa.keywords,
    aa.topics,
    aa.entities_extracted,
    vs.created_at
FROM voice_submissions vs
LEFT JOIN users u ON vs.user_id = u.user_id
LEFT JOIN transcriptions t ON vs.submission_id = t.submission_id
LEFT JOIN ai_analysis aa ON vs.submission_id = aa.submission_id;

-- View: Cost analytics
CREATE OR REPLACE VIEW v_cost_analytics AS
SELECT
    DATE_TRUNC('day', created_at) as date,
    service_name,
    service_type,
    SUM(cost_usd) as daily_cost,
    COUNT(*) as transaction_count,
    AVG(cost_usd) as avg_cost_per_transaction
FROM processing_costs
GROUP BY DATE_TRUNC('day', created_at), service_name, service_type
ORDER BY date DESC, daily_cost DESC;

-- View: Sentiment trends
CREATE OR REPLACE VIEW v_sentiment_trends AS
SELECT
    DATE_TRUNC('day', aa.created_at) as date,
    aa.category_l1,
    aa.sentiment,
    COUNT(*) as count,
    AVG(aa.sentiment_score) as avg_sentiment_score,
    AVG(aa.urgency_score) as avg_urgency_score
FROM ai_analysis aa
JOIN voice_submissions vs ON aa.submission_id = vs.submission_id
WHERE vs.processing_status = 'completed'
GROUP BY DATE_TRUNC('day', aa.created_at), aa.category_l1, aa.sentiment
ORDER BY date DESC, count DESC;

-- ============================================================================
-- SAMPLE DATA (for development/testing)
-- ============================================================================

-- Create admin user (password: 'admin123' - CHANGE IN PRODUCTION!)
-- Password hash for 'admin123' using bcrypt
INSERT INTO users (email, name, password_hash, role, email_verified)
VALUES (
    'admin@voyce.local',
    'Admin User',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYb4ZQJx7/u',  -- admin123
    'admin',
    TRUE
) ON CONFLICT (email) DO NOTHING;

-- Create test user
INSERT INTO users (email, name, password_hash, role, email_verified)
VALUES (
    'user@voyce.local',
    'Test User',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYb4ZQJx7/u',  -- admin123
    'user',
    TRUE
) ON CONFLICT (email) DO NOTHING;

-- ============================================================================
-- GRANTS (for PostgREST)
-- ============================================================================

-- Create web_anon role for unauthenticated access
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'web_anon') THEN
        CREATE ROLE web_anon NOLOGIN;
    END IF;
END
$$;

-- Create authenticator role (used by PostgREST)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'authenticator') THEN
        CREATE ROLE authenticator NOINHERIT LOGIN PASSWORD 'change-this-password';
    END IF;
END
$$;

-- Grant permissions
GRANT USAGE ON SCHEMA public TO web_anon;
GRANT SELECT ON users TO web_anon;
GRANT SELECT, INSERT ON voice_submissions TO web_anon;
GRANT SELECT ON transcriptions TO web_anon;
GRANT SELECT ON ai_analysis TO web_anon;
GRANT SELECT ON v_submissions_complete TO web_anon;

GRANT web_anon TO authenticator;

-- ============================================================================
-- PERFORMANCE OPTIMIZATION
-- ============================================================================

-- Analyze tables for query planner
ANALYZE users;
ANALYZE voice_submissions;
ANALYZE transcriptions;
ANALYZE ai_analysis;
ANALYZE processing_costs;

-- Set statistics target for better query planning
ALTER TABLE voice_submissions ALTER COLUMN processing_status SET STATISTICS 1000;
ALTER TABLE transcriptions ALTER COLUMN confidence_score SET STATISTICS 1000;
ALTER TABLE ai_analysis ALTER COLUMN sentiment SET STATISTICS 1000;

COMMENT ON DATABASE voyce_db IS 'Voice Feedback Platform - Production Database';
COMMENT ON TABLE users IS 'User accounts and authentication';
COMMENT ON TABLE voice_submissions IS 'Voice recording submissions from all platforms';
COMMENT ON TABLE transcriptions IS 'Speech-to-text transcription results';
COMMENT ON TABLE ai_analysis IS 'AI-powered sentiment analysis and categorization';
COMMENT ON TABLE sync_metadata IS 'Data synchronization tracking with Databricks';
COMMENT ON TABLE processing_costs IS 'Cost tracking for all processing services';
COMMENT ON TABLE audit_log IS 'Security and audit trail';
