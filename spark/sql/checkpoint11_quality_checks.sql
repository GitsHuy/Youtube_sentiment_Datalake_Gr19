CREATE DATABASE IF NOT EXISTS lakehouse;

SHOW TABLES IN lakehouse;

SELECT 'bronze_row_count' AS check_name, COUNT(*) AS check_value
FROM lakehouse.bronze_youtube_comments;

SELECT 'silver_row_count' AS check_name, COUNT(*) AS check_value
FROM lakehouse.silver_youtube_comments;

SELECT 'gold_metrics_row_count' AS check_name, COUNT(*) AS check_value
FROM lakehouse.gold_youtube_comment_metrics;

SELECT 'gold_breakdown_row_count' AS check_name, COUNT(*) AS check_value
FROM lakehouse.gold_youtube_sentiment_breakdown;

SELECT 'bronze_distinct_video_count' AS check_name, COUNT(DISTINCT video_id) AS check_value
FROM lakehouse.bronze_youtube_comments;

SELECT 'silver_distinct_video_count' AS check_name, COUNT(DISTINCT video_id) AS check_value
FROM lakehouse.silver_youtube_comments;

SELECT 'gold_metrics_distinct_video_count' AS check_name, COUNT(DISTINCT video_id) AS check_value
FROM lakehouse.gold_youtube_comment_metrics;

SELECT 'bronze_null_comment_id' AS check_name, COUNT(*) AS check_value
FROM lakehouse.bronze_youtube_comments
WHERE comment_id IS NULL;

SELECT 'silver_null_comment_id' AS check_name, COUNT(*) AS check_value
FROM lakehouse.silver_youtube_comments
WHERE comment_id IS NULL;

SELECT 'silver_null_sentiment' AS check_name, COUNT(*) AS check_value
FROM lakehouse.silver_youtube_comments
WHERE sentiment IS NULL;

SELECT 'silver_duplicate_comment_id' AS check_name, COUNT(*) AS check_value
FROM (
    SELECT video_id, comment_id
    FROM lakehouse.silver_youtube_comments
    GROUP BY video_id, comment_id
    HAVING COUNT(*) > 1
) duplicate_comments;

SELECT 'silver_sentiment_distribution' AS check_name, sentiment, COUNT(*) AS comment_count
FROM lakehouse.silver_youtube_comments
GROUP BY sentiment
ORDER BY comment_count DESC;

SELECT
    'video_flow_check' AS check_name,
    bronze.video_id,
    bronze.bronze_comments,
    silver.silver_comments,
    gold.metric_rows,
    gold_breakdown.breakdown_rows
FROM (
    SELECT video_id, COUNT(*) AS bronze_comments
    FROM lakehouse.bronze_youtube_comments
    GROUP BY video_id
) bronze
LEFT JOIN (
    SELECT video_id, COUNT(*) AS silver_comments
    FROM lakehouse.silver_youtube_comments
    GROUP BY video_id
) silver
    ON bronze.video_id = silver.video_id
LEFT JOIN (
    SELECT video_id, COUNT(*) AS metric_rows
    FROM lakehouse.gold_youtube_comment_metrics
    GROUP BY video_id
) gold
    ON bronze.video_id = gold.video_id
LEFT JOIN (
    SELECT video_id, COUNT(*) AS breakdown_rows
    FROM lakehouse.gold_youtube_sentiment_breakdown
    GROUP BY video_id
) gold_breakdown
    ON bronze.video_id = gold_breakdown.video_id
ORDER BY bronze.bronze_comments DESC, bronze.video_id;
