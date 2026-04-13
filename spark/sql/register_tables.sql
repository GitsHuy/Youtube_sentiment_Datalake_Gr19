CREATE DATABASE IF NOT EXISTS lakehouse;

CREATE TABLE IF NOT EXISTS lakehouse.bronze_youtube_comments
USING PARQUET
LOCATION 'hdfs://namenode:8020/lake/bronze/youtube_comments';

CREATE TABLE IF NOT EXISTS lakehouse.silver_youtube_comments
USING PARQUET
LOCATION 'hdfs://namenode:8020/lake/silver/youtube_comments';

DROP TABLE IF EXISTS lakehouse.gold_youtube_comment_metrics;
CREATE TABLE lakehouse.gold_youtube_comment_metrics (
    event_date DATE,
    video_id STRING,
    total_comments BIGINT,
    top_level_comment_count BIGINT,
    reply_comment_count BIGINT,
    unique_author_count BIGINT,
    total_likes BIGINT,
    avg_likes_per_comment DOUBLE,
    avg_reply_count DOUBLE,
    avg_text_length DOUBLE,
    avg_collected_delay_seconds DOUBLE,
    positive_comment_count BIGINT,
    neutral_comment_count BIGINT,
    negative_comment_count BIGINT,
    positive_ratio DOUBLE,
    neutral_ratio DOUBLE,
    negative_ratio DOUBLE,
    reply_ratio DOUBLE,
    engagement_score BIGINT
)
USING PARQUET
LOCATION 'hdfs://namenode:8020/lake/gold/youtube_comment_metrics';

DROP TABLE IF EXISTS lakehouse.gold_youtube_sentiment_breakdown;
CREATE TABLE lakehouse.gold_youtube_sentiment_breakdown (
    event_date DATE,
    video_id STRING,
    sentiment STRING,
    comment_count BIGINT,
    comment_ratio DOUBLE,
    avg_likes DOUBLE,
    avg_replies DOUBLE,
    reply_comment_count BIGINT,
    avg_text_length DOUBLE
)
USING PARQUET
LOCATION 'hdfs://namenode:8020/lake/gold/youtube_sentiment_breakdown';

SHOW TABLES IN lakehouse;
