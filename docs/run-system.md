# Hướng dẫn chạy hệ thống

Chạy tất cả lệnh tại thư mục gốc repo:

```powershell
D:\AHCMUTE_HocTap\BigDataAnalysis\BT_CuoiKy\Project_nhom19_datalakehouse
```

## 1. Điều kiện trước khi chạy

- Docker Desktop đang bật
- SQL Server local đang chạy
- `.env` đã có giá trị đúng cho `YOUTUBE_API_KEY`, `YOUTUBE_VIDEO_ID` nếu dùng ingestion thật
- Các port chính còn trống: `8080`, `8081`, `9083`, `9871`, `10000`

Nếu chưa có `.env`, tạo từ `.env.example`.

## 2. Khởi động nhanh toàn hệ thống

Khởi động hạ tầng và pipeline:

```powershell
docker compose up -d kafka kafka-ui namenode datanode hdfs-init hive-metastore spark-master spark-worker
docker compose up -d producer spark-bronze spark-silver spark-gold
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -f /opt/sql/register_tables.sql"
docker compose up -d spark-thriftserver
```

Nếu muốn kiểm tra cú pháp Compose trước:

```powershell
docker compose config
```

## 3. Chạy ingestion thật từ YouTube API

Cập nhật `.env`:

```env
INGESTION_MODE=youtube_api
YOUTUBE_API_KEY=your_api_key
YOUTUBE_VIDEO_ID=your_video_id
YOUTUBE_ORDER=time
YOUTUBE_MAX_RESULTS=100
YOUTUBE_PAGE_LIMIT=5
YOUTUBE_RETRY_DELAY_SECONDS=5
YOUTUBE_PUBLISH_DELAY_MS=0
YOUTUBE_CONTINUOUS_MODE=true
YOUTUBE_POLL_INTERVAL_SECONDS=60
YOUTUBE_DEDUP_CACHE_SIZE=5000
```

Khởi động producer:

```powershell
docker compose up -d producer
docker compose logs --tail 100 producer
```

Lưu ý:

- `YOUTUBE_VIDEO_ID` có thể là `videoId` thuần hoặc URL YouTube
- Nếu `YOUTUBE_CONTINUOUS_MODE=true`, producer sẽ polling liên tục theo chu kỳ `YOUTUBE_POLL_INTERVAL_SECONDS`
- Nếu `YOUTUBE_CONTINUOUS_MODE=false`, producer sẽ chạy một vòng rồi dừng
- `YOUTUBE_DEDUP_CACHE_SIZE` dùng để giữ danh sách `comment_id` gần nhất đã gửi, giúp giảm gửi trùng khi polling
- Nếu comment API trả về bị rỗng `text`, producer sẽ bỏ qua record đó và ghi log
- Log producer sẽ thể hiện rõ từng vòng polling: số record lấy được, số record trùng bị bỏ qua, số record mới đã gửi vào Kafka

## 4. Kiểm tra HDFS và dữ liệu các lớp

Kiểm tra thư mục HDFS:

```powershell
docker compose exec namenode hdfs dfs -ls /
docker compose exec namenode hdfs dfs -ls /lake
docker compose exec namenode hdfs dfs -ls /checkpoints
```

Kiểm tra từng lớp:

```powershell
docker compose exec namenode hdfs dfs -ls /lake/bronze/youtube_comments
docker compose exec namenode hdfs dfs -ls /lake/silver/youtube_comments
docker compose exec namenode hdfs dfs -ls /lake/gold/youtube_comment_metrics
docker compose exec namenode hdfs dfs -ls /lake/gold/youtube_sentiment_breakdown
```

## 5. Truy vấn nhanh bằng Spark SQL

Đăng ký lại bảng external nếu vừa khởi động lại metastore:

```powershell
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -f /opt/sql/register_tables.sql"
```

Xem database và bảng:

```powershell
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SHOW DATABASES'"
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SHOW TABLES IN lakehouse'"
```

Xem mẫu dữ liệu:

```powershell
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SELECT * FROM lakehouse.bronze_youtube_comments LIMIT 5'"
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SELECT comment_id, text_clean, sentiment FROM lakehouse.silver_youtube_comments LIMIT 10'"
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SELECT * FROM lakehouse.gold_youtube_comment_metrics LIMIT 10'"
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SELECT * FROM lakehouse.gold_youtube_sentiment_breakdown LIMIT 10'"
```

## 6. Đánh giá model sentiment của checkpoint 5

Chạy script đánh giá với bộ `100` comment seed:

```powershell
python .\scripts\evaluate_seed_labels.py
```

Đầu ra:

- `data/evaluation/model_vs_seed_labels_100.csv`
- `data/evaluation/model_vs_seed_labels_100_summary.json`

Khi benchmark nghiêm túc, nên tắt fallback để biết chắc kết quả là của transformer:

```env
SENTIMENT_FALLBACK_TO_KEYWORD=false
```

## 7. Kiểm tra chất lượng Gold của checkpoint 6

Chạy bộ kiểm tra:

```powershell
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -f /opt/sql/checkpoint6_gold_quality_checks.sql"
```

Nếu Docker Desktop đang chập chờn và lệnh SQL dài dễ treo, vẫn nên kiểm tra tối thiểu:

```powershell
docker compose exec namenode hdfs dfs -ls /lake/gold/youtube_comment_metrics
docker compose exec namenode hdfs dfs -ls /lake/gold/youtube_sentiment_breakdown
```

## 8. Kiểm tra Spark Thrift Server và JDBC ở checkpoint 7

Chạy smoke test:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_thriftserver.ps1
```

Script sẽ:

- khởi động `spark-thriftserver`
- chờ port `10000`
- chạy lại `register_tables.sql`
- kiểm tra `SHOW TABLES IN lakehouse`

Thông số JDBC:

- Driver: `Apache Hive 2`
- Host: `localhost`
- Port: `10000`
- Database: `lakehouse`
- Authentication: `None`
- JDBC URL: `jdbc:hive2://localhost:10000/lakehouse`

## 9. Nếu Docker Desktop báo `Internal Server Error`

Đây là lỗi môi trường đã lặp lại nhiều lần trên máy hiện tại. Cách khôi phục nhanh:

```powershell
Get-Process -Name 'Docker Desktop','com.docker.backend','com.docker.build','com.docker.dev-envs' -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 8
Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
docker context use desktop-linux
```

Sau khi Docker lên lại, chạy lại:

```powershell
docker compose up -d kafka kafka-ui namenode datanode hdfs-init hive-metastore spark-master spark-worker
docker compose up -d producer spark-bronze spark-silver spark-gold
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -f /opt/sql/register_tables.sql"
```

## 10. Dừng hệ thống

```powershell
docker compose down
```

Reset container:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\reset_demo.ps1
```

Reset cả volume:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\reset_demo.ps1 -RemoveVolumes
```

## 11. Smoke test tong quat

Chay smoke test tong quat:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_test.ps1
```

Script nay se:

- kiem tra service nen tang chinh
- dam bao `spark-thriftserver` mo cong `10000`
- chay lai `register_tables.sql`
- kiem tra `SHOW TABLES IN lakehouse`
- chay `spark/sql/checkpoint11_quality_checks.sql`

Luu y:

- day la buoc kiem tra tuy chon
- khong chay smoke test thi he thong van dung duoc binh thuong
- neu he thong dang tat, script se fail som va bao ro service nao chua chay

## 12. Cap nhat checkpoint 12

Sau checkpoint 12:

- Bronze, Silver, Gold da chuyen sang `Delta Lake`
- ten bang trong `lakehouse` giu nguyen
- du lieu moi duoc ghi vao:
  - `/lake_delta/bronze/youtube_comments`
  - `/lake_delta/silver/youtube_comments`
  - `/lake_delta/gold/youtube_comment_metrics`
  - `/lake_delta/gold/youtube_sentiment_breakdown`

Kiem tra file tren HDFS:

```powershell
docker compose exec namenode hdfs dfs -ls /lake_delta/bronze/youtube_comments
docker compose exec namenode hdfs dfs -ls /lake_delta/silver/youtube_comments
docker compose exec namenode hdfs dfs -ls /lake_delta/gold/youtube_comment_metrics
docker compose exec namenode hdfs dfs -ls /lake_delta/gold/youtube_sentiment_breakdown
```

Neu migration Delta chay dung, trong moi thu muc se thay them `_delta_log`.
