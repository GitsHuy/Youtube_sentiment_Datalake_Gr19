# Run System

Tài liệu này là runbook thực dụng để chạy và kiểm tra hệ thống hiện tại.

Chạy tất cả lệnh tại thư mục gốc repo:

```powershell
D:\AHCMUTE_HocTap\BigDataAnalysis\BT_CuoiKy\Project_nhom19_datalakehouse
```

## 1. Điều kiện trước khi chạy

- Docker Desktop đang bật
- SQL Server local đang chạy
- file `.env` đã có thông số đúng
- các port `8080`, `9871`, `8081`, `9083`, `10000` đang trống

Nếu chưa có `.env` thì tạo từ `.env.example`.

## 2. Kiểm tra cấu hình

Kiểm tra syntax của Docker Compose:

```powershell
docker compose config
```

Kiểm tra nhanh SQL Server local:

```powershell
Test-NetConnection -ComputerName localhost -Port 1433
```

## 3. Cách chạy đầy đủ hệ thống

Khởi động hạ tầng chính:

```powershell
docker compose up -d kafka kafka-ui namenode datanode hdfs-init hive-metastore spark-master spark-worker
```

Khởi động producer và 3 tầng xử lý:

```powershell
docker compose up -d producer spark-bronze spark-silver spark-gold
```

Đăng ký bảng external trong Spark SQL:

```powershell
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -f /opt/sql/register_tables.sql"
```

Khởi động lớp SQL/JDBC:

```powershell
docker compose up -d spark-thriftserver
```

## 4. Cách chạy nhanh nhất từ trạng thái mới

```powershell
docker compose up -d kafka kafka-ui namenode datanode hdfs-init producer hive-metastore spark-master spark-worker spark-bronze spark-silver spark-gold
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -f /opt/sql/register_tables.sql"
docker compose up -d spark-thriftserver
```

## 5. Chạy từng phần riêng lẻ

Chỉ chạy hạ tầng:

```powershell
docker compose up -d kafka kafka-ui namenode datanode hdfs-init hive-metastore spark-master spark-worker
```

Chỉ chạy producer mẫu:

```powershell
docker compose up -d producer
docker compose logs --tail 50 producer
```

Lưu ý:

- ở `INGESTION_MODE=sample`, producer mặc định gửi 1 lượt rồi dừng
- trạng thái `Exited (0)` của producer trong sample mode là bình thường
- nếu muốn lặp lại dữ liệu mẫu để test, đặt `SAMPLE_LOOP=true`

Chỉ chạy Bronze:

```powershell
docker compose up -d spark-bronze
docker compose logs --tail 100 spark-bronze
```

Chỉ chạy Silver:

```powershell
docker compose up -d spark-silver
docker compose logs --tail 100 spark-silver
```

Chỉ chạy Gold:

```powershell
docker compose up -d spark-gold
docker compose logs --tail 100 spark-gold
```

Chỉ chạy lớp SQL/JDBC:

```powershell
docker compose up -d spark-thriftserver
docker compose ps spark-thriftserver
```

## 6. Kiểm tra nhanh sau khi khởi động

Kiểm tra container:

```powershell
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

UI:

- Kafka UI: `http://localhost:8080`
- HDFS NameNode UI: `http://localhost:9871`
- Spark master UI: `http://localhost:8081`

Kiểm tra thư mục HDFS:

```powershell
docker compose exec namenode hdfs dfs -ls /
docker compose exec namenode hdfs dfs -ls /lake
docker compose exec namenode hdfs dfs -ls /checkpoints
```

Kiểm tra file Bronze:

```powershell
docker compose exec namenode hdfs dfs -ls /lake/bronze/youtube_comments
```

Kiểm tra file Silver:

```powershell
docker compose exec namenode hdfs dfs -ls /lake/silver/youtube_comments
```

Kiểm tra file Gold:

```powershell
docker compose exec namenode hdfs dfs -ls /lake/gold/youtube_comment_metrics
```

## 7. Truy vấn các bảng lakehouse

Xem database:

```powershell
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SHOW DATABASES'"
```

Xem bảng:

```powershell
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SHOW TABLES IN lakehouse'"
```

Xem nhanh Bronze:

```powershell
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SELECT * FROM lakehouse.bronze_youtube_comments LIMIT 5'"
```

Xem nhanh Silver:

```powershell
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SELECT comment_id, text_clean, sentiment FROM lakehouse.silver_youtube_comments LIMIT 10'"
```

Xem nhanh Gold:

```powershell
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SELECT * FROM lakehouse.gold_youtube_comment_metrics LIMIT 10'"
```

Kiểm tra nhanh số dòng:

```powershell
docker compose exec spark-master /bin/bash -lc "cat >/tmp/check.sql <<'SQL'
SELECT COUNT(*) AS silver_rows FROM lakehouse.silver_youtube_comments;
SELECT COUNT(*) AS gold_rows FROM lakehouse.gold_youtube_comment_metrics;
SQL
/opt/spark/bin/spark-sql -f /tmp/check.sql"
```

## 8. Log hay dùng khi debug

Producer:

```powershell
docker compose logs --tail 100 producer
```

Bronze:

```powershell
docker compose logs --tail 100 spark-bronze
```

Silver:

```powershell
docker compose logs --tail 100 spark-silver
```

Gold:

```powershell
docker compose logs --tail 100 spark-gold
```

Metastore:

```powershell
docker compose logs --tail 100 hive-metastore
```

Thrift Server:

```powershell
docker compose logs --tail 100 spark-thriftserver
```

## 9. Chuẩn bị JDBC và Power BI

Nếu cần, tải Hive JDBC driver:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\download_hive_jdbc.ps1
```

JDBC endpoint hiện tại:

```text
jdbc:hive2://localhost:10000/lakehouse
```

Thông số mặc định:

- Host: `localhost`
- Port: `10000`
- Database: `lakehouse`
- Username: `hive`
- Password: `hive`

## 10. Dừng và reset

Dừng toàn bộ:

```powershell
docker compose down
```

Reset container:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\reset_demo.ps1
```

Reset cả container và volume:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\reset_demo.ps1 -RemoveVolumes
```

## 11. Mục đích của baseline này

Bộ khung này được giữ để mọi người có thể bắt tay vào việc ngay:

- A làm ingestion YouTube API mà không phải chờ B, C
- B cải tiến Bronze, Silver, Gold và model trên dữ liệu mẫu
- C kiểm tra Metastore, SQL, JDBC và Power BI độc lập
