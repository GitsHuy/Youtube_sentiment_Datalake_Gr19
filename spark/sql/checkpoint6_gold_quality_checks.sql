SELECT COUNT(*) AS gold_summary_rows
FROM lakehouse.gold_youtube_comment_metrics;

SELECT COUNT(*) AS gold_breakdown_rows
FROM lakehouse.gold_youtube_sentiment_breakdown;

SELECT
    SUM(
        CASE
            WHEN total_comments <> top_level_comment_count + reply_comment_count THEN 1
            ELSE 0
        END
    ) AS invalid_comment_total_rows,
    SUM(
        CASE
            WHEN total_comments <> positive_comment_count + neutral_comment_count + negative_comment_count THEN 1
            ELSE 0
        END
    ) AS invalid_sentiment_total_rows,
    SUM(
        CASE
            WHEN ABS((positive_ratio + neutral_ratio + negative_ratio) - 1.0) > 0.01 THEN 1
            ELSE 0
        END
    ) AS invalid_ratio_rows
FROM lakehouse.gold_youtube_comment_metrics;

SELECT
    g.event_date,
    g.video_id,
    g.total_comments,
    b.breakdown_total
FROM lakehouse.gold_youtube_comment_metrics g
LEFT JOIN (
    SELECT
        event_date,
        video_id,
        SUM(comment_count) AS breakdown_total
    FROM lakehouse.gold_youtube_sentiment_breakdown
    GROUP BY event_date, video_id
) b
ON g.event_date = b.event_date AND g.video_id = b.video_id;

SELECT *
FROM lakehouse.gold_youtube_comment_metrics
LIMIT 10;

SELECT *
FROM lakehouse.gold_youtube_sentiment_breakdown
LIMIT 10;
