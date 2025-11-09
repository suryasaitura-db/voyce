-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Analytics Queries for Voice Feedback Platform
-- MAGIC
-- MAGIC This SQL notebook contains:
-- MAGIC - Business intelligence queries
-- MAGIC - Sentiment trends analysis
-- MAGIC - User engagement metrics
-- MAGIC - Cost analysis
-- MAGIC - Performance dashboards

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Configuration

-- COMMAND ----------

USE CATALOG voice_feedback_prod;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Daily Feedback Summary

-- COMMAND ----------

-- Create daily aggregations
INSERT INTO voice_feedback_prod.analytics.daily_feedback_summary
SELECT
    DATE(vf.created_at) as date,
    vf.organization_id,
    COUNT(DISTINCT vf.id) as total_feedback_count,
    AVG(vf.audio_duration_seconds) as avg_duration_seconds,
    SUM(CASE WHEN sa.sentiment_label = 'positive' THEN 1 ELSE 0 END) as sentiment_positive_count,
    SUM(CASE WHEN sa.sentiment_label = 'neutral' THEN 1 ELSE 0 END) as sentiment_neutral_count,
    SUM(CASE WHEN sa.sentiment_label = 'negative' THEN 1 ELSE 0 END) as sentiment_negative_count,
    AVG(sa.sentiment_score) as avg_sentiment_score,
    COLLECT_SET(
        FROM_JSON(sa.topics, 'array<string>')
    ) as top_topics,
    COLLECT_SET(t.name) as top_tags,
    SUM(CASE WHEN vf.status = 'processed' THEN 1 ELSE 0 END) / COUNT(*) as processing_success_rate,
    AVG(COALESCE(trans.processing_time_ms, 0) + COALESCE(sa.processing_time_ms, 0)) as avg_processing_time_ms,
    current_timestamp() as created_at
FROM voice_feedback_prod.raw_data.voice_feedback vf
LEFT JOIN voice_feedback_prod.raw_data.transcriptions trans
    ON vf.id = trans.voice_feedback_id
LEFT JOIN voice_feedback_prod.raw_data.sentiment_analysis sa
    ON trans.id = sa.transcription_id
LEFT JOIN voice_feedback_prod.raw_data.feedback_tags ft
    ON vf.id = ft.voice_feedback_id
LEFT JOIN voice_feedback_prod.raw_data.tags t
    ON ft.tag_id = t.id
WHERE DATE(vf.created_at) = current_date() - INTERVAL 1 DAY
GROUP BY DATE(vf.created_at), vf.organization_id;

-- COMMAND ----------

-- View daily summary
SELECT
    date,
    organization_id,
    total_feedback_count,
    avg_duration_seconds,
    sentiment_positive_count,
    sentiment_neutral_count,
    sentiment_negative_count,
    avg_sentiment_score,
    processing_success_rate,
    avg_processing_time_ms
FROM voice_feedback_prod.analytics.daily_feedback_summary
ORDER BY date DESC, organization_id
LIMIT 100;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Sentiment Trends Over Time

-- COMMAND ----------

-- Weekly sentiment trends
SELECT
    DATE_TRUNC('week', date) as week,
    organization_id,
    SUM(total_feedback_count) as total_feedback,
    AVG(avg_sentiment_score) as avg_sentiment,
    SUM(sentiment_positive_count) / SUM(total_feedback_count) * 100 as positive_pct,
    SUM(sentiment_neutral_count) / SUM(total_feedback_count) * 100 as neutral_pct,
    SUM(sentiment_negative_count) / SUM(total_feedback_count) * 100 as negative_pct
FROM voice_feedback_prod.analytics.daily_feedback_summary
WHERE date >= current_date() - INTERVAL 90 DAYS
GROUP BY DATE_TRUNC('week', date), organization_id
ORDER BY week DESC, organization_id;

-- COMMAND ----------

-- Monthly sentiment comparison
SELECT
    DATE_TRUNC('month', date) as month,
    organization_id,
    SUM(total_feedback_count) as total_feedback,
    AVG(avg_sentiment_score) as avg_sentiment,
    SUM(sentiment_positive_count) as positive_count,
    SUM(sentiment_negative_count) as negative_count,
    (SUM(sentiment_positive_count) - SUM(sentiment_negative_count)) as net_sentiment
FROM voice_feedback_prod.analytics.daily_feedback_summary
WHERE date >= current_date() - INTERVAL 365 DAYS
GROUP BY DATE_TRUNC('month', date), organization_id
ORDER BY month DESC, organization_id;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Top Topics and Trends

-- COMMAND ----------

-- Most discussed topics
SELECT
    topic,
    COUNT(*) as mention_count,
    AVG(sa.sentiment_score) as avg_sentiment,
    COUNT(DISTINCT sa.voice_feedback_id) as unique_feedback_count,
    COUNT(DISTINCT vf.organization_id) as organization_count
FROM voice_feedback_prod.raw_data.sentiment_analysis sa
JOIN voice_feedback_prod.raw_data.voice_feedback vf
    ON sa.voice_feedback_id = vf.id
LATERAL VIEW EXPLODE(FROM_JSON(sa.topics, 'array<string>')) t as topic
WHERE sa.created_at >= current_date() - INTERVAL 30 DAYS
GROUP BY topic
ORDER BY mention_count DESC
LIMIT 50;

-- COMMAND ----------

-- Topic sentiment breakdown
SELECT
    topic,
    SUM(CASE WHEN sa.sentiment_label = 'positive' THEN 1 ELSE 0 END) as positive_count,
    SUM(CASE WHEN sa.sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral_count,
    SUM(CASE WHEN sa.sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative_count,
    AVG(sa.sentiment_score) as avg_sentiment_score,
    COUNT(*) as total_mentions
FROM voice_feedback_prod.raw_data.sentiment_analysis sa
LATERAL VIEW EXPLODE(FROM_JSON(sa.topics, 'array<string>')) t as topic
WHERE sa.created_at >= current_date() - INTERVAL 30 DAYS
GROUP BY topic
HAVING COUNT(*) >= 5
ORDER BY total_mentions DESC
LIMIT 30;

-- COMMAND ----------

-- Trending topics (increasing mentions)
WITH topic_counts AS (
    SELECT
        DATE_TRUNC('week', sa.created_at) as week,
        topic,
        COUNT(*) as mention_count
    FROM voice_feedback_prod.raw_data.sentiment_analysis sa
    LATERAL VIEW EXPLODE(FROM_JSON(sa.topics, 'array<string>')) t as topic
    WHERE sa.created_at >= current_date() - INTERVAL 60 DAYS
    GROUP BY DATE_TRUNC('week', sa.created_at), topic
),
topic_trends AS (
    SELECT
        topic,
        MAX(CASE WHEN week = DATE_TRUNC('week', current_date()) - INTERVAL 7 DAYS THEN mention_count ELSE 0 END) as last_week,
        MAX(CASE WHEN week = DATE_TRUNC('week', current_date()) - INTERVAL 14 DAYS THEN mention_count ELSE 0 END) as prev_week
    FROM topic_counts
    GROUP BY topic
)
SELECT
    topic,
    last_week,
    prev_week,
    (last_week - prev_week) as growth,
    CASE
        WHEN prev_week > 0 THEN ((last_week - prev_week) / prev_week * 100)
        ELSE NULL
    END as growth_pct
FROM topic_trends
WHERE last_week >= 5
ORDER BY growth DESC
LIMIT 20;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## User Engagement Metrics

-- COMMAND ----------

-- User activity summary
SELECT
    u.organization_id,
    org.name as organization_name,
    COUNT(DISTINCT u.id) as total_users,
    COUNT(DISTINCT CASE WHEN vf.created_at >= current_date() - INTERVAL 30 DAYS THEN u.id END) as active_users_30d,
    COUNT(DISTINCT vf.id) as total_feedback,
    COUNT(DISTINCT vf.id) / COUNT(DISTINCT u.id) as avg_feedback_per_user,
    MAX(vf.created_at) as last_feedback_date
FROM voice_feedback_prod.raw_data.users u
JOIN voice_feedback_prod.raw_data.organizations org
    ON u.organization_id = org.id
LEFT JOIN voice_feedback_prod.raw_data.voice_feedback vf
    ON u.id = vf.user_id
WHERE u.is_active = TRUE
GROUP BY u.organization_id, org.name
ORDER BY total_feedback DESC;

-- COMMAND ----------

-- Most active users
SELECT
    u.id as user_id,
    u.full_name,
    u.email,
    org.name as organization_name,
    COUNT(vf.id) as feedback_count,
    SUM(vf.audio_duration_seconds) / 60 as total_minutes,
    AVG(sa.sentiment_score) as avg_sentiment,
    MAX(vf.created_at) as last_feedback_date
FROM voice_feedback_prod.raw_data.users u
JOIN voice_feedback_prod.raw_data.organizations org
    ON u.organization_id = org.id
LEFT JOIN voice_feedback_prod.raw_data.voice_feedback vf
    ON u.id = vf.user_id
LEFT JOIN voice_feedback_prod.raw_data.transcriptions t
    ON vf.id = t.voice_feedback_id
LEFT JOIN voice_feedback_prod.raw_data.sentiment_analysis sa
    ON t.id = sa.transcription_id
WHERE vf.created_at >= current_date() - INTERVAL 90 DAYS
GROUP BY u.id, u.full_name, u.email, org.name
HAVING COUNT(vf.id) > 0
ORDER BY feedback_count DESC
LIMIT 50;

-- COMMAND ----------

-- User retention cohorts
WITH user_cohorts AS (
    SELECT
        u.id as user_id,
        u.organization_id,
        DATE_TRUNC('month', MIN(vf.created_at)) as cohort_month,
        DATE_TRUNC('month', vf.created_at) as activity_month
    FROM voice_feedback_prod.raw_data.users u
    JOIN voice_feedback_prod.raw_data.voice_feedback vf
        ON u.id = vf.user_id
    GROUP BY u.id, u.organization_id, DATE_TRUNC('month', vf.created_at)
)
SELECT
    cohort_month,
    COUNT(DISTINCT user_id) as cohort_size,
    COUNT(DISTINCT CASE WHEN activity_month = cohort_month THEN user_id END) as month_0,
    COUNT(DISTINCT CASE WHEN activity_month = cohort_month + INTERVAL 1 MONTH THEN user_id END) as month_1,
    COUNT(DISTINCT CASE WHEN activity_month = cohort_month + INTERVAL 2 MONTH THEN user_id END) as month_2,
    COUNT(DISTINCT CASE WHEN activity_month = cohort_month + INTERVAL 3 MONTH THEN user_id END) as month_3
FROM user_cohorts
WHERE cohort_month >= current_date() - INTERVAL 12 MONTHS
GROUP BY cohort_month
ORDER BY cohort_month DESC;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Organization Metrics

-- COMMAND ----------

-- Update organization metrics table
INSERT INTO voice_feedback_prod.analytics.organization_metrics
SELECT
    org.id as organization_id,
    current_date() - INTERVAL 1 DAY as metric_date,
    COUNT(DISTINCT u.id) as total_users,
    COUNT(DISTINCT CASE WHEN u.last_login >= current_date() - INTERVAL 30 DAYS THEN u.id END) as active_users,
    COUNT(DISTINCT vf.id) as total_feedback_count,
    COUNT(DISTINCT vf.id) / COUNT(DISTINCT u.id) as avg_feedback_per_user,
    SUM(vf.audio_duration_seconds) / 60 as total_audio_minutes,
    SUM(vf.file_size_bytes) / (1024 * 1024 * 1024) as storage_used_gb,
    COUNT(DISTINCT t.id) + COUNT(DISTINCT sa.id) as api_calls_count,
    SUM(ct.total_cost) as processing_cost_usd,
    current_timestamp() as created_at
FROM voice_feedback_prod.raw_data.organizations org
LEFT JOIN voice_feedback_prod.raw_data.users u
    ON org.id = u.organization_id
LEFT JOIN voice_feedback_prod.raw_data.voice_feedback vf
    ON org.id = vf.organization_id
    AND DATE(vf.created_at) = current_date() - INTERVAL 1 DAY
LEFT JOIN voice_feedback_prod.raw_data.transcriptions t
    ON vf.id = t.voice_feedback_id
LEFT JOIN voice_feedback_prod.raw_data.sentiment_analysis sa
    ON t.id = sa.transcription_id
LEFT JOIN voice_feedback_prod.analytics.cost_tracking ct
    ON org.id = ct.organization_id
    AND ct.cost_date = current_date() - INTERVAL 1 DAY
WHERE org.is_active = TRUE
GROUP BY org.id;

-- COMMAND ----------

-- Organization performance dashboard
SELECT
    org.name as organization_name,
    org.subscription_tier,
    om.total_users,
    om.active_users,
    om.total_feedback_count,
    om.avg_feedback_per_user,
    om.total_audio_minutes,
    om.storage_used_gb,
    om.processing_cost_usd,
    om.processing_cost_usd / NULLIF(om.total_feedback_count, 0) as cost_per_feedback
FROM voice_feedback_prod.analytics.organization_metrics om
JOIN voice_feedback_prod.raw_data.organizations org
    ON om.organization_id = org.id
WHERE om.metric_date = current_date() - INTERVAL 1 DAY
ORDER BY om.total_feedback_count DESC;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Cost Analysis

-- COMMAND ----------

-- Daily cost breakdown by resource type
SELECT
    cost_date,
    resource_type,
    operation,
    SUM(quantity) as total_quantity,
    SUM(total_cost) as total_cost_usd,
    AVG(unit_cost) as avg_unit_cost
FROM voice_feedback_prod.analytics.cost_tracking
WHERE cost_date >= current_date() - INTERVAL 30 DAYS
GROUP BY cost_date, resource_type, operation
ORDER BY cost_date DESC, total_cost_usd DESC;

-- COMMAND ----------

-- Monthly cost summary
SELECT
    DATE_TRUNC('month', cost_date) as month,
    resource_type,
    SUM(total_cost) as total_cost_usd,
    SUM(quantity) as total_quantity,
    AVG(unit_cost) as avg_unit_cost
FROM voice_feedback_prod.analytics.cost_tracking
WHERE cost_date >= current_date() - INTERVAL 365 DAYS
GROUP BY DATE_TRUNC('month', cost_date), resource_type
ORDER BY month DESC, total_cost_usd DESC;

-- COMMAND ----------

-- Organization cost analysis
SELECT
    org.name as organization_name,
    org.subscription_tier,
    SUM(ct.total_cost) as total_cost_usd,
    COUNT(DISTINCT vf.id) as total_feedback_count,
    SUM(ct.total_cost) / NULLIF(COUNT(DISTINCT vf.id), 0) as cost_per_feedback,
    SUM(CASE WHEN ct.resource_type = 'voice_processing' THEN ct.total_cost ELSE 0 END) as processing_cost,
    SUM(CASE WHEN ct.resource_type = 'sentiment_analysis' THEN ct.total_cost ELSE 0 END) as sentiment_cost,
    SUM(CASE WHEN ct.resource_type = 'data_ingestion' THEN ct.total_cost ELSE 0 END) as ingestion_cost
FROM voice_feedback_prod.raw_data.organizations org
LEFT JOIN voice_feedback_prod.analytics.cost_tracking ct
    ON org.id = ct.organization_id
    AND ct.cost_date >= current_date() - INTERVAL 30 DAYS
LEFT JOIN voice_feedback_prod.raw_data.voice_feedback vf
    ON org.id = vf.organization_id
    AND DATE(vf.created_at) >= current_date() - INTERVAL 30 DAYS
WHERE org.is_active = TRUE
GROUP BY org.name, org.subscription_tier
ORDER BY total_cost_usd DESC;

-- COMMAND ----------

-- Cost optimization opportunities
WITH cost_metrics AS (
    SELECT
        ct.organization_id,
        ct.resource_type,
        AVG(ct.unit_cost) as avg_unit_cost,
        PERCENTILE(ct.unit_cost, 0.5) as median_unit_cost,
        PERCENTILE(ct.unit_cost, 0.9) as p90_unit_cost
    FROM voice_feedback_prod.analytics.cost_tracking ct
    WHERE ct.cost_date >= current_date() - INTERVAL 30 DAYS
    GROUP BY ct.organization_id, ct.resource_type
)
SELECT
    org.name as organization_name,
    cm.resource_type,
    cm.avg_unit_cost,
    cm.median_unit_cost,
    cm.p90_unit_cost,
    CASE
        WHEN cm.avg_unit_cost > cm.p90_unit_cost * 1.2 THEN 'High cost - review usage'
        WHEN cm.avg_unit_cost > cm.median_unit_cost * 1.5 THEN 'Above average - optimize'
        ELSE 'Normal'
    END as recommendation
FROM cost_metrics cm
JOIN voice_feedback_prod.raw_data.organizations org
    ON cm.organization_id = org.id
ORDER BY cm.avg_unit_cost DESC;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Audio Processing Performance

-- COMMAND ----------

-- Transcription accuracy metrics
SELECT
    transcription_engine,
    COUNT(*) as total_transcriptions,
    AVG(confidence_score) as avg_confidence,
    AVG(word_count) as avg_word_count,
    AVG(processing_time_ms) as avg_processing_time_ms,
    PERCENTILE(processing_time_ms, 0.5) as median_processing_time_ms,
    PERCENTILE(processing_time_ms, 0.95) as p95_processing_time_ms,
    COUNT(CASE WHEN error_message IS NOT NULL THEN 1 END) as error_count,
    COUNT(CASE WHEN error_message IS NOT NULL THEN 1 END) / COUNT(*) * 100 as error_rate_pct
FROM voice_feedback_prod.raw_data.transcriptions
WHERE created_at >= current_date() - INTERVAL 30 DAYS
GROUP BY transcription_engine
ORDER BY total_transcriptions DESC;

-- COMMAND ----------

-- Audio duration distribution
SELECT
    CASE
        WHEN audio_duration_seconds < 10 THEN '0-10s'
        WHEN audio_duration_seconds < 30 THEN '10-30s'
        WHEN audio_duration_seconds < 60 THEN '30-60s'
        WHEN audio_duration_seconds < 120 THEN '1-2min'
        WHEN audio_duration_seconds < 300 THEN '2-5min'
        ELSE '5min+'
    END as duration_bucket,
    COUNT(*) as feedback_count,
    AVG(t.confidence_score) as avg_confidence,
    AVG(t.processing_time_ms) as avg_processing_time_ms
FROM voice_feedback_prod.raw_data.voice_feedback vf
JOIN voice_feedback_prod.raw_data.transcriptions t
    ON vf.id = t.voice_feedback_id
WHERE vf.created_at >= current_date() - INTERVAL 30 DAYS
GROUP BY
    CASE
        WHEN audio_duration_seconds < 10 THEN '0-10s'
        WHEN audio_duration_seconds < 30 THEN '10-30s'
        WHEN audio_duration_seconds < 60 THEN '30-60s'
        WHEN audio_duration_seconds < 120 THEN '1-2min'
        WHEN audio_duration_seconds < 300 THEN '2-5min'
        ELSE '5min+'
    END
ORDER BY
    MIN(audio_duration_seconds);

-- COMMAND ----------

-- Processing funnel analysis
SELECT
    COUNT(DISTINCT vf.id) as total_feedback,
    COUNT(DISTINCT t.id) as transcribed,
    COUNT(DISTINCT sa.id) as sentiment_analyzed,
    COUNT(DISTINCT et.id) as enhanced,
    COUNT(DISTINCT t.id) / COUNT(DISTINCT vf.id) * 100 as transcription_rate,
    COUNT(DISTINCT sa.id) / COUNT(DISTINCT vf.id) * 100 as sentiment_rate,
    COUNT(DISTINCT et.id) / COUNT(DISTINCT vf.id) * 100 as enhancement_rate
FROM voice_feedback_prod.raw_data.voice_feedback vf
LEFT JOIN voice_feedback_prod.raw_data.transcriptions t
    ON vf.id = t.voice_feedback_id
LEFT JOIN voice_feedback_prod.raw_data.sentiment_analysis sa
    ON t.id = sa.transcription_id
LEFT JOIN voice_feedback_prod.processed_data.enhanced_transcriptions et
    ON t.id = et.id
WHERE vf.created_at >= current_date() - INTERVAL 7 DAYS;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Action Items Analysis

-- COMMAND ----------

-- Action items by status
SELECT
    status,
    priority,
    COUNT(*) as count,
    AVG(DATEDIFF(COALESCE(completed_at, current_timestamp()), created_at)) as avg_days_to_complete
FROM voice_feedback_prod.raw_data.action_items
WHERE created_at >= current_date() - INTERVAL 30 DAYS
GROUP BY status, priority
ORDER BY priority, status;

-- COMMAND ----------

-- Action items completion rate
SELECT
    DATE_TRUNC('week', created_at) as week,
    COUNT(*) as total_items,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_items,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) / COUNT(*) * 100 as completion_rate,
    AVG(CASE WHEN status = 'completed' THEN DATEDIFF(completed_at, created_at) END) as avg_days_to_complete
FROM voice_feedback_prod.raw_data.action_items
WHERE created_at >= current_date() - INTERVAL 90 DAYS
GROUP BY DATE_TRUNC('week', created_at)
ORDER BY week DESC;

-- COMMAND ----------

-- Overdue action items
SELECT
    ai.id,
    ai.description,
    ai.priority,
    ai.status,
    ai.due_date,
    DATEDIFF(current_date(), ai.due_date) as days_overdue,
    vf.organization_id,
    org.name as organization_name,
    u.full_name as assigned_to_name
FROM voice_feedback_prod.raw_data.action_items ai
JOIN voice_feedback_prod.raw_data.voice_feedback vf
    ON ai.voice_feedback_id = vf.id
JOIN voice_feedback_prod.raw_data.organizations org
    ON vf.organization_id = org.id
LEFT JOIN voice_feedback_prod.raw_data.users u
    ON ai.assigned_to = u.id
WHERE ai.status != 'completed'
    AND ai.due_date < current_date()
ORDER BY days_overdue DESC, ai.priority
LIMIT 100;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Summary Statistics

-- COMMAND ----------

-- Overall platform statistics
SELECT
    'Total Organizations' as metric,
    COUNT(*) as value
FROM voice_feedback_prod.raw_data.organizations
WHERE is_active = TRUE

UNION ALL

SELECT
    'Total Users' as metric,
    COUNT(*) as value
FROM voice_feedback_prod.raw_data.users
WHERE is_active = TRUE

UNION ALL

SELECT
    'Total Feedback (All Time)' as metric,
    COUNT(*) as value
FROM voice_feedback_prod.raw_data.voice_feedback

UNION ALL

SELECT
    'Total Feedback (Last 30 Days)' as metric,
    COUNT(*) as value
FROM voice_feedback_prod.raw_data.voice_feedback
WHERE created_at >= current_date() - INTERVAL 30 DAYS

UNION ALL

SELECT
    'Total Audio Minutes' as metric,
    CAST(SUM(audio_duration_seconds) / 60 as BIGINT) as value
FROM voice_feedback_prod.raw_data.voice_feedback

UNION ALL

SELECT
    'Avg Sentiment Score (Last 30 Days)' as metric,
    CAST(AVG(sentiment_score) * 100 as BIGINT) as value
FROM voice_feedback_prod.raw_data.sentiment_analysis
WHERE created_at >= current_date() - INTERVAL 30 DAYS

UNION ALL

SELECT
    'Total Processing Cost (Last 30 Days)' as metric,
    CAST(SUM(total_cost) as BIGINT) as value
FROM voice_feedback_prod.analytics.cost_tracking
WHERE cost_date >= current_date() - INTERVAL 30 DAYS;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Optimize Analytics Tables

-- COMMAND ----------

OPTIMIZE voice_feedback_prod.analytics.daily_feedback_summary;
OPTIMIZE voice_feedback_prod.analytics.organization_metrics;
OPTIMIZE voice_feedback_prod.analytics.cost_tracking;

-- COMMAND ----------

-- Clean up old data (optional - use with caution)
-- VACUUM voice_feedback_prod.analytics.daily_feedback_summary RETAIN 168 HOURS;
-- VACUUM voice_feedback_prod.analytics.organization_metrics RETAIN 168 HOURS;
-- VACUUM voice_feedback_prod.analytics.cost_tracking RETAIN 168 HOURS;

-- COMMAND ----------
