# Run System

Tai lieu nay la runbook thuc dung de chay va kiem tra he thong hien tai.

Chay tat ca lenh tai thu muc goc repo:

```powershell
D:\AHCMUTE_HocTap\BigDataAnalysis\BT_CuoiKy\Project_nhom19_datalakehouse
```

## 1. Dieu kien truoc khi chay

- Docker Desktop dang bat
- SQL Server local dang chay
- file `.env` da co thong so dung
- cac port `8080`, `9871`, `8081`, `9083`, `10000` dang trong

Neu chua co `.env` thi tao tu `.env.example`.

## 2. Kiem tra cau hinh

Kiem tra syntax cua Docker Compose:

```powershell
docker compose config
```

Kiem tra nhanh SQL Server local:

```powershell
Test-NetConnection -ComputerName localhost -Port 1433
```

## 3. Cach chay day du he thong

Khoi dong ha tang chinh:

```powershell
docker compose up -d kafka kafka-ui namenode datanode hdfs-init hive-metastore spark-master spark-worker
```

Khoi dong producer va 3 tang xu ly:

```powershell
docker compose up -d producer spark-bronze spark-silver spark-gold
```

Dang ky bang external trong Spark SQL:

```powershell
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -f /opt/sql/register_tables.sql"
```

Khoi dong lop SQL/JDBC:

```powershell
docker compose up -d spark-thriftserver
```

## 4. Cach chay nhanh nhat tu trang thai moi

```powershell
docker compose up -d kafka kafka-ui namenode datanode hdfs-init producer hive-metastore spark-master spark-worker spark-bronze spark-silver spark-gold
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -f /opt/sql/register_tables.sql"
docker compose up -d spark-thriftserver
```

## 5. Chay tung phan rieng le

Chi chay ha tang:

```powershell
docker compose up -d kafka kafka-ui namenode datanode hdfs-init hive-metastore spark-master spark-worker
```

Chi chay producer mau:

```powershell
docker compose up -d producer
docker compose logs --tail 50 producer
```

Luu y:

- o `INGESTION_MODE=sample`, producer mac dinh gui 1 luot roi dung
- trang thai `Exited (0)` cua producer trong sample mode la binh thuong
- neu muon lap lai du lieu mau de test, dat `SAMPLE_LOOP=true`

Chi chay Bronze:

```powershell
docker compose up -d spark-bronze
docker compose logs --tail 100 spark-bronze
```

Chi chay Silver:

```powershell
docker compose up -d spark-silver
docker compose logs --tail 100 spark-silver
```

Chi chay Gold:

```powershell
docker compose up -d spark-gold
docker compose logs --tail 100 spark-gold
```

Chi chay lop SQL/JDBC:

```powershell
docker compose up -d spark-thriftserver
docker compose ps spark-thriftserver
```

## 6. Kiem tra nhanh sau khi khoi dong

Kiem tra container:

```powershell
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

UI:

- Kafka UI: `http://localhost:8080`
- HDFS NameNode UI: `http://localhost:9871`
- Spark master UI: `http://localhost:8081`

Kiem tra thu muc HDFS:

```powershell
docker compose exec namenode hdfs dfs -ls /
docker compose exec namenode hdfs dfs -ls /lake
docker compose exec namenode hdfs dfs -ls /checkpoints
```

Kiem tra file Bronze:

```powershell
docker compose exec namenode hdfs dfs -ls /lake/bronze/youtube_comments
```

Kiem tra file Silver:

```powershell
docker compose exec namenode hdfs dfs -ls /lake/silver/youtube_comments
```

Kiem tra file Gold:

```powershell
docker compose exec namenode hdfs dfs -ls /lake/gold/youtube_comment_metrics
```

## 7. Truy van cac bang lakehouse

Xem database:

```powershell
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SHOW DATABASES'"
```

Xem bang:

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

Kiem tra nhanh so dong:

```powershell
docker compose exec spark-master /bin/bash -lc "cat >/tmp/check.sql <<'SQL'
SELECT COUNT(*) AS silver_rows FROM lakehouse.silver_youtube_comments;
SELECT COUNT(*) AS gold_rows FROM lakehouse.gold_youtube_comment_metrics;
SQL
/opt/spark/bin/spark-sql -f /tmp/check.sql"
```

## 8. Log hay dung khi debug

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

## 9. Chuan bi JDBC va Power BI

Neu can, tai Hive JDBC driver:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\download_hive_jdbc.ps1
```

JDBC endpoint hien tai:

```text
jdbc:hive2://localhost:10000/lakehouse
```

Thong so mac dinh:

- Host: `localhost`
- Port: `10000`
- Database: `lakehouse`
- Username: `hive`
- Password: `hive`

## 10. Dung va reset

Dung toan bo:

```powershell
docker compose down
```

Reset container:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\reset_demo.ps1
```

Reset ca container va volume:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\reset_demo.ps1 -RemoveVolumes
```

## 11. Muc dich cua baseline nay

Bo khung nay duoc giu de moi nguoi co the bat tay vao viec ngay:

- A lam ingestion YouTube API ma khong phai cho B, C
- B cai tien Bronze, Silver, Gold va model tren du lieu mau
- C kiem tra Metastore, SQL, JDBC va Power BI doc lap
