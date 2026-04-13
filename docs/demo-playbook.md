# Kịch bản demo hệ thống

Tài liệu này là kịch bản demo ngắn gọn để trình bày hệ thống từ đầu đến cuối mà không bị lan man.

## 1. Mục tiêu của buổi demo

Buổi demo cần chứng minh được 5 ý:

1. Hệ thống nhận bình luận từ đúng một video YouTube
2. Dữ liệu đi qua các lớp Bronze, Silver, Gold
3. Silver đã làm sạch dữ liệu và gán nhãn sentiment
4. Gold đã tổng hợp thành business metrics để phục vụ báo cáo
5. Dữ liệu có thể được truy vấn qua Spark Thrift Server bằng DBeaver

## 2. Chuẩn bị trước khi demo

Trước khi trình bày, nên kiểm tra:

- Docker Desktop đang ổn định
- `spark-thriftserver` đang chạy
- DBeaver vào được `lakehouse`
- video mục tiêu và API key đã đúng trong `.env`

Các lệnh khởi động ngắn gọn:

```powershell
docker compose up -d kafka kafka-ui namenode datanode hdfs-init hive-metastore spark-master spark-worker
docker compose up -d producer spark-bronze spark-silver spark-gold
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -f /opt/sql/register_tables.sql"
docker compose up -d spark-thriftserver
```

## 3. Kịch bản demo 1 mạch

### Bước 1. Giới thiệu kiến trúc

Nói ngắn:

- YouTube API lấy bình luận của 1 video
- producer gửi dữ liệu vào Kafka
- Spark Bronze ghi raw lên HDFS
- Spark Silver làm sạch và phân tích cảm xúc
- Spark Gold tổng hợp chỉ số cho báo cáo
- Spark Thrift Server mở dữ liệu cho DBeaver và Power BI

### Bước 2. Chứng minh hệ thống có đủ bảng

Chạy:

```sql
SHOW TABLES IN lakehouse;
```

Ý nên nói:

- đây là 4 bảng chính của hệ thống hiện tại
- Bronze và Silver là dữ liệu chi tiết
- Gold summary và Gold breakdown là dữ liệu tổng hợp

### Bước 3. Chứng minh Bronze nhận dữ liệu thật

Chạy:

```sql
SELECT comment_id, video_id, author, text, event_time, ingested_at
FROM lakehouse.bronze_youtube_comments
ORDER BY ingested_at DESC
LIMIT 10;
```

Ý nên nói:

- đây là dữ liệu raw gần nguồn nhất
- hệ thống đã ingest bình luận thật từ YouTube API

### Bước 4. Chứng minh Silver làm sạch và gán sentiment

Chạy:

```sql
SELECT comment_id, text_clean, sentiment, silver_processed_at
FROM lakehouse.silver_youtube_comments
ORDER BY silver_processed_at DESC
LIMIT 10;
```

Ý nên nói:

- text đã được làm sạch thành `text_clean`
- mỗi comment đã được gán nhãn `positive`, `neutral`, `negative`
- đây là nơi thể hiện phần xử lý dữ liệu và NLP

### Bước 5. Chứng minh Gold đã tổng hợp KPI

Chạy:

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

Ý nên nói:

- Gold không còn là từng comment riêng lẻ
- dữ liệu ở đây đã sẵn sàng cho dashboard

### Bước 6. Chứng minh breakdown theo sentiment

Chạy:

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

Ý nên nói:

- bảng này hỗ trợ biểu đồ phân bố cảm xúc
- Power BI sẽ dùng bảng này để vẽ chart nhanh hơn

## 4. Câu nói kết luận gợi ý

Có thể kết luận ngắn như sau:

“Nhóm đã hoàn thiện được pipeline lakehouse từ ingestion comment YouTube đến phân tích sentiment và tổng hợp business metrics. Dữ liệu hiện đã truy vấn được qua Spark Thrift Server, đủ để kết nối DBeaver và làm dashboard ở tầng Gold.”

## 5. Nếu gặp lỗi khi demo

### Trường hợp DBeaver không phản hồi

Làm fallback:

- chuyển sang `spark-sql`
- chạy đúng các câu truy vấn trong `docs/query-guide.md`

### Trường hợp Docker Desktop chập chờn

Làm fallback:

```powershell
Get-Process -Name 'Docker Desktop','com.docker.backend','com.docker.build','com.docker.dev-envs' -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 8
Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
docker context use desktop-linux
```

### Trường hợp bảng Bronze lỗi thiếu cột mới

Nói rõ:

- metadata Bronze trong metastore có thể chưa đồng bộ schema mới hoàn toàn
- khi demo phần dữ liệu mới nhất ở Bronze, ưu tiên dùng `ingested_at`

## 6. Tài liệu nên mở cùng lúc khi demo

- `docs/query-guide.md`
- `docs/run-system.md`
- `docs/Report_checkpoint8.md`

