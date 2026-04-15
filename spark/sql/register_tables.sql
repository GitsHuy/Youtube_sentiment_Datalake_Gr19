CREATE DATABASE IF NOT EXISTS lakehouse;

DROP TABLE IF EXISTS lakehouse.bronze_youtube_comments;
CREATE TABLE lakehouse.bronze_youtube_comments (
    event_time TIMESTAMP,
    collected_at TIMESTAMP,
    comment_id STRING,
    video_id STRING,
    author STRING,
    text STRING,
    like_count INT,
    reply_count INT,
    is_reply BOOLEAN,
    parent_comment_id STRING,
    lang STRING,
    source STRING,
    ingested_at TIMESTAMP
)
USING DELTA
LOCATION 'hdfs://namenode:8020/lake_delta/bronze/youtube_comments';

DROP TABLE IF EXISTS lakehouse.silver_youtube_comments;
CREATE TABLE lakehouse.silver_youtube_comments (
    event_time TIMESTAMP,
    collected_at TIMESTAMP,
    comment_id STRING,
    video_id STRING,
    author STRING,
    text STRING,
    like_count INT,
    reply_count INT,
    is_reply BOOLEAN,
    parent_comment_id STRING,
    lang STRING,
    source STRING,
    ingested_at TIMESTAMP,
    text_clean STRING,
    text_length INT,
    collected_delay_seconds BIGINT,
    silver_processed_at TIMESTAMP,
    positive_score INT,
    negative_score INT,
    sentiment STRING
)
USING DELTA
LOCATION 'hdfs://namenode:8020/lake_delta/silver/youtube_comments';

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
USING DELTA
LOCATION 'hdfs://namenode:8020/lake_delta/gold/youtube_comment_metrics';

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
USING DELTA
LOCATION 'hdfs://namenode:8020/lake_delta/gold/youtube_sentiment_breakdown';

SHOW TABLES IN lakehouse;
