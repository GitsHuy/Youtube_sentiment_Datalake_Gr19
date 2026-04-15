CREATE DATABASE IF NOT EXISTS lakehouse;

CREATE TABLE IF NOT EXISTS lakehouse.bronze_youtube_comments
USING PARQUET
LOCATION 'hdfs://namenode:8020/lake/bronze/youtube_comments';

CREATE TABLE IF NOT EXISTS lakehouse.silver_youtube_comments
USING PARQUET
LOCATION 'hdfs://namenode:8020/lake/silver/youtube_comments';

CREATE TABLE IF NOT EXISTS lakehouse.gold_youtube_comment_metrics
USING PARQUET
LOCATION 'hdfs://namenode:8020/lake/gold/youtube_comment_metrics';

CREATE TABLE IF NOT EXISTS lakehouse.gold_youtube_sentiment_breakdown
USING PARQUET
LOCATION 'hdfs://namenode:8020/lake/gold/youtube_sentiment_breakdown';

SHOW TABLES IN lakehouse;
