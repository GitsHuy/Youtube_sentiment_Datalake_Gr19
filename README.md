# Project Nhóm 19 Datalakehouse

Đây là bộ khung dùng chung cho đồ án phân tích cảm xúc bình luận YouTube theo hướng lakehouse.

## Mục tiêu dự án

Hệ thống hướng tới luồng xử lý sau:

- lấy bình luận từ đúng 1 video YouTube thông qua `videoId`
- đưa dữ liệu vào Kafka
- xử lý qua 3 lớp Bronze, Silver, Gold trên HDFS
- quản lý metadata bằng Hive Metastore
- mở dữ liệu cho truy vấn SQL, JDBC và Power BI qua Spark Thrift Server

## Thành phần hiện đã có

Hệ thống hiện tại đã có sẵn:

- Kafka và Kafka UI
- HDFS gồm NameNode, DataNode và bước khởi tạo thư mục
- producer mẫu để bơm dữ liệu fallback
- Spark master, worker và 3 job Bronze, Silver, Gold
- Hive Metastore dùng SQL Server local
- Spark Thrift Server để nối JDBC và Power BI

## Quyết định hiện tại của nhóm

- giữ SQL Server local
- chưa đưa Delta Lake vào ngay
- giữ bộ dữ liệu mẫu để mỗi thành viên có thể tự test độc lập
- phát triển tiếp trên bộ khung này, không làm lại hạ tầng từ đầu

## Đọc tài liệu theo thứ tự

- `docs/run-system.md`: cách chạy hệ thống và kiểm tra từng phần
- `docs/interfaces.md`: hợp đồng schema, topic, path và bảng dùng chung
- `docs/team-assignment.md`: bảng phân công chi tiết cho A, B, C

## Nguyên tắc chung

- những tên dùng chung như Kafka topic, HDFS path, database, tên bảng cốt lõi không được đổi nếu chủ chưa đồng ý

## Cấu trúc repository

- `data/`: dữ liệu mẫu để test local
- `producer/`: phần ingestion hiện tại
- `spark/`: Spark jobs, SQL đăng ký bảng và cấu hình runtime
- `hadoop/`: cấu hình HDFS client được mount vào Spark và Hive
- `hive/`: image Hive Metastore, template config và script khởi động
- `sqlserver/`: ghi chú liên quan đến SQL Server local
- `scripts/`: script hỗ trợ reset và tải JDBC driver
- `docs/`: tài liệu vận hành và phối hợp cho nhóm

## Phạm vi baseline hiện tại

Code hiện tại vẫn là baseline để phát triển tiếp:

- ingestion mặc định đọc `data/sample_comments.jsonl`
- producer mẫu mặc định chỉ gửi 1 lượt để tránh nhân bản số liệu demo
- Bronze, Silver, Gold đang ghi ra `PARQUET`
- Silver đang dùng baseline sentiment theo từ khóa
- Silver đã có khâu khử trùng lặp theo `comment_id`
- Spark Thrift Server đã có sẵn cho lớp truy vấn SQL

## Cách chạy nhanh

Chạy lần lượt tại thư mục gốc repo:

```powershell
docker compose up -d kafka kafka-ui namenode datanode hdfs-init hive-metastore spark-master spark-worker
docker compose up -d producer spark-bronze spark-silver spark-gold
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -f /opt/sql/register_tables.sql"
docker compose up -d spark-thriftserver
```

## Cách xem dữ liệu

Xem nhanh dữ liệu Bronze:

```powershell
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SELECT * FROM lakehouse.bronze_youtube_comments LIMIT 10'"
```

Xem nhanh dữ liệu Silver:

```powershell
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SELECT comment_id, text_clean, sentiment FROM lakehouse.silver_youtube_comments LIMIT 10'"
```

Xem nhanh dữ liệu Gold:

```powershell
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SELECT * FROM lakehouse.gold_youtube_comment_metrics LIMIT 10'"
```

## Ghi chú quan trọng

- SQL Server local hiện chỉ đóng vai trò Hive Metastore, không phải nơi lưu dữ liệu thật của Bronze, Silver, Gold
- dữ liệu thật đang nằm trên HDFS
- nếu muốn xem dữ liệu thì ưu tiên dùng `spark-sql`, Spark Thrift Server, DBeaver hoặc Power BI

Bộ khung này được giữ có chủ đích để A, B, C có thể làm song song trên một nền ổn định, thay vì chờ nhau theo kiểu tuần tự.
