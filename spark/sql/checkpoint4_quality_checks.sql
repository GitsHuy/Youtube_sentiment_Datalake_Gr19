SELECT COUNT(*) AS bronze_rows
FROM parquet.`hdfs://namenode:8020/lake/bronze/youtube_comments`;

SELECT COUNT(*) AS silver_rows
FROM parquet.`hdfs://namenode:8020/lake/silver/youtube_comments`;

SELECT COUNT(*) AS gold_rows
FROM parquet.`hdfs://namenode:8020/lake/gold/youtube_comment_metrics`;

SELECT
  COUNT(*) AS duplicate_comment_rows
FROM (
  SELECT video_id, comment_id, COUNT(*) AS row_count
  FROM parquet.`hdfs://namenode:8020/lake/silver/youtube_comments`
  GROUP BY video_id, comment_id
  HAVING COUNT(*) > 1
) duplicates;

SELECT
  SUM(CASE WHEN comment_id IS NULL THEN 1 ELSE 0 END) AS null_comment_id_rows,
  SUM(CASE WHEN video_id IS NULL THEN 1 ELSE 0 END) AS null_video_id_rows,
  SUM(CASE WHEN text_clean IS NULL OR TRIM(text_clean) = '' THEN 1 ELSE 0 END) AS empty_text_clean_rows,
  SUM(CASE WHEN is_reply = true AND parent_comment_id IS NULL THEN 1 ELSE 0 END) AS invalid_reply_rows,
  SUM(CASE WHEN collected_delay_seconds < 0 THEN 1 ELSE 0 END) AS negative_delay_rows
FROM parquet.`hdfs://namenode:8020/lake/silver/youtube_comments`;

SELECT
  video_id,
  sentiment,
  COUNT(*) AS comment_count
FROM parquet.`hdfs://namenode:8020/lake/silver/youtube_comments`
GROUP BY video_id, sentiment
ORDER BY video_id, sentiment;
