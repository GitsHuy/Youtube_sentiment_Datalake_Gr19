# Bộ truy vấn kiểm tra toàn hệ thống

Tài liệu này gom lại các câu truy vấn dùng để kiểm tra và demo hệ thống qua `Spark Thrift Server` hoặc `spark-sql`.

Chạy các câu lệnh này trên:

- `DBeaver` qua JDBC
- hoặc `spark-sql` trong container `spark-master`

Database dùng chung:

```sql
USE lakehouse;
```

## 1. Kiểm tra tổng quan hệ thống

Xem các database:

```sql
SHOW DATABASES;
```

Xem các bảng trong `lakehouse`:

```sql
SHOW TABLES IN lakehouse;
```

Kỳ vọng thấy ít nhất:

- `bronze_youtube_comments`
- `silver_youtube_comments`
- `gold_youtube_comment_metrics`
- `gold_youtube_sentiment_breakdown`

## 2. Truy vấn lớp Bronze

### Xem mẫu dữ liệu thô

```sql
SELECT *
FROM lakehouse.bronze_youtube_comments
LIMIT 10;
```

### Đếm tổng số dòng Bronze

```sql
SELECT COUNT(*) AS bronze_rows
FROM lakehouse.bronze_youtube_comments;
```

### Kiểm tra đang có những video nào

```sql
SELECT video_id, COUNT(*) AS comment_count
FROM lakehouse.bronze_youtube_comments
GROUP BY video_id
ORDER BY comment_count DESC;
```

### Xem dữ liệu mới nhất của Bronze

Lưu ý:

- nếu bảng Bronze trong metastore chưa đồng bộ schema mới, dùng `ingested_at`
- không dùng `collected_at` cho đến khi xác nhận metadata đã khớp

```sql
SELECT comment_id, video_id, author, text, event_time, ingested_at
FROM lakehouse.bronze_youtube_comments
ORDER BY ingested_at DESC
LIMIT 20;
```

## 3. Truy vấn lớp Silver

### Xem mẫu dữ liệu đã làm sạch và có sentiment

```sql
SELECT comment_id, video_id, author, text_clean, sentiment, positive_score, negative_score
FROM lakehouse.silver_youtube_comments
LIMIT 20;
```

### Đếm tổng số dòng Silver

```sql
SELECT COUNT(*) AS silver_rows
FROM lakehouse.silver_youtube_comments;
```

### Xem phân bố sentiment ở Silver

```sql
SELECT sentiment, COUNT(*) AS comment_count
FROM lakehouse.silver_youtube_comments
GROUP BY sentiment
ORDER BY comment_count DESC;
```

### Xem dữ liệu Silver mới nhất

```sql
SELECT comment_id, video_id, text_clean, sentiment, silver_processed_at
FROM lakehouse.silver_youtube_comments
ORDER BY silver_processed_at DESC
LIMIT 20;
```

### Nếu schema Silver đã khớp đầy đủ, có thể dùng truy vấn này

```sql
SELECT comment_id, video_id, author, text_clean, sentiment, collected_at, silver_processed_at
FROM lakehouse.silver_youtube_comments
ORDER BY silver_processed_at DESC
LIMIT 20;
```

### Kiểm tra dữ liệu lỗi hoặc thiếu

```sql
SELECT
    SUM(CASE WHEN comment_id IS NULL THEN 1 ELSE 0 END) AS null_comment_id,
    SUM(CASE WHEN video_id IS NULL THEN 1 ELSE 0 END) AS null_video_id,
    SUM(CASE WHEN text_clean IS NULL OR TRIM(text_clean) = '' THEN 1 ELSE 0 END) AS empty_text_clean
FROM lakehouse.silver_youtube_comments;
```

### Kiểm tra phân bố top-level và reply

```sql
SELECT is_reply, COUNT(*) AS row_count
FROM lakehouse.silver_youtube_comments
GROUP BY is_reply;
```

## 4. Truy vấn lớp Gold summary

### Xem toàn bộ Gold summary

```sql
SELECT *
FROM lakehouse.gold_youtube_comment_metrics
LIMIT 20;
```

### Truy vấn gọn để đọc như dashboard KPI

```sql
SELECT
    event_date,
    video_id,
    total_comments,
    positive_comment_count,
    neutral_comment_count,
    negative_comment_count,
    positive_ratio,
    neutral_ratio,
    negative_ratio,
    engagement_score
FROM lakehouse.gold_youtube_comment_metrics
ORDER BY event_date DESC;
```

## 5. Truy vấn lớp Gold breakdown

### Xem mẫu dữ liệu breakdown

```sql
SELECT *
FROM lakehouse.gold_youtube_sentiment_breakdown
LIMIT 20;
```

### Xem breakdown theo sentiment

```sql
SELECT
    event_date,
    video_id,
    sentiment,
    comment_count,
    comment_ratio,
    avg_likes,
    avg_replies
FROM lakehouse.gold_youtube_sentiment_breakdown
ORDER BY event_date DESC, sentiment;
```

## 6. Truy vấn đối chiếu giữa các lớp

### So sánh số dòng giữa Bronze, Silver, Gold

```sql
SELECT 'bronze' AS layer, COUNT(*) AS row_count FROM lakehouse.bronze_youtube_comments
UNION ALL
SELECT 'silver' AS layer, COUNT(*) AS row_count FROM lakehouse.silver_youtube_comments
UNION ALL
SELECT 'gold_summary' AS layer, COUNT(*) AS row_count FROM lakehouse.gold_youtube_comment_metrics
UNION ALL
SELECT 'gold_breakdown' AS layer, COUNT(*) AS row_count FROM lakehouse.gold_youtube_sentiment_breakdown;
```

### So sánh phân bố sentiment giữa Silver và Gold

```sql
SELECT sentiment, COUNT(*) AS silver_count
FROM lakehouse.silver_youtube_comments
GROUP BY sentiment
ORDER BY sentiment;
```

```sql
SELECT sentiment, SUM(comment_count) AS gold_count
FROM lakehouse.gold_youtube_sentiment_breakdown
GROUP BY sentiment
ORDER BY sentiment;
```

## 7. Truy vấn kiểm tra bài toán 1 video

### Bronze đang chứa những video nào

```sql
SELECT DISTINCT video_id
FROM lakehouse.bronze_youtube_comments;
```

### Silver đang chứa những video nào

```sql
SELECT DISTINCT video_id
FROM lakehouse.silver_youtube_comments;
```

### Gold summary đang chứa những video nào

```sql
SELECT DISTINCT video_id
FROM lakehouse.gold_youtube_comment_metrics;
```

Nếu chỉ ra đúng `1 video_id`, bài test hiện tại đang sạch theo bài toán 1 video.

## 8. Truy vấn kiểm tra dữ liệu mới nhất theo thời gian

### Bronze mới nhất

```sql
SELECT MAX(ingested_at) AS latest_bronze_ingested_at
FROM lakehouse.bronze_youtube_comments;
```

### Silver mới nhất

```sql
SELECT MAX(silver_processed_at) AS latest_silver_processed_at
FROM lakehouse.silver_youtube_comments;
```

### Nếu schema Silver đã đồng bộ đầy đủ

```sql
SELECT MAX(collected_at) AS latest_collected_at
FROM lakehouse.silver_youtube_comments;
```

## 9. Bộ truy vấn demo ngắn gọn 1 mạch

Nếu muốn demo nhanh theo đúng luồng hệ thống, chạy lần lượt:

### Bước 1. Xem hệ thống có đủ bảng không

```sql
SHOW TABLES IN lakehouse;
```

### Bước 2. Xác nhận Bronze có dữ liệu mới

```sql
SELECT comment_id, video_id, author, text, event_time, ingested_at
FROM lakehouse.bronze_youtube_comments
ORDER BY ingested_at DESC
LIMIT 10;
```

### Bước 3. Xác nhận Silver đã làm sạch và gán sentiment

```sql
SELECT comment_id, text_clean, sentiment, silver_processed_at
FROM lakehouse.silver_youtube_comments
ORDER BY silver_processed_at DESC
LIMIT 10;
```

### Bước 4. Xác nhận Gold đã tổng hợp

```sql
SELECT
    event_date,
    video_id,
    total_comments,
    positive_ratio,
    neutral_ratio,
    negative_ratio,
    engagement_score
FROM lakehouse.gold_youtube_comment_metrics
ORDER BY event_date DESC;
```

### Bước 5. Xác nhận breakdown theo sentiment

```sql
SELECT
    event_date,
    video_id,
    sentiment,
    comment_count,
    comment_ratio
FROM lakehouse.gold_youtube_sentiment_breakdown
ORDER BY event_date DESC, sentiment;
```

## 10. Ghi chú quan trọng

- `SQL Server local` hiện không phải nơi chứa dữ liệu Bronze/Silver/Gold
- dữ liệu thật của hệ thống được query qua `Spark Thrift Server`
- nếu gặp lỗi kiểu thiếu cột ở Bronze hoặc Silver, nhiều khả năng metastore đang lệch schema so với parquet thực tế
