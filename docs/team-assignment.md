# Team Assignment

Tài liệu này là bảng phân công và cách làm việc song song trên baseline hiện tại.

## 1. Nguyên tắc chung trước khi chia việc

Repo đã có baseline chạy được. Nhóm nên cải tiến trên baseline này, không làm lại hạ tầng từ đầu.

Những file dùng chung chỉ nên do chủ sửa trực tiếp, trừ khi có phê duyệt:

- `docker-compose.yml`
- `.env.example`
- `README.md`
- `docs/interfaces.md`

Mỗi thành viên nên sửa chủ yếu trong module mình phụ trách.

## 2. Kiến trúc đang có sẵn trong repo

| Tầng | Trạng thái hiện tại | File chính |
| --- | --- | --- |
| Ingestion fallback | producer mẫu gửi dữ liệu vào Kafka | `data/sample_comments.jsonl`, `producer/producer.py` |
| Bronze | Kafka sang HDFS raw đã nối sẵn | `spark/jobs/bronze_stream.py` |
| Silver | cleaning và sentiment baseline đã có | `spark/jobs/silver_stream.py` |
| Gold | metric tổng hợp đã có | `spark/jobs/gold_stream.py` |
| Metadata | Hive Metastore đã có và dùng SQL Server local | `hive/`, `spark/sql/register_tables.sql` |
| SQL consumption | Spark Thrift Server đã có | `docker-compose.yml`, `scripts/download_hive_jdbc.ps1` |

Ý nghĩa:

- mỗi người đều có thể bắt đầu từ một bộ khung cụ thể
- không ai phải ngồi chờ người khác làm xong mới tới lượt

## 3. Người A: Ingestion, API, Kafka

### Mục tiêu chính

Biến producer hiện tại thành collector dùng YouTube Data API cho 1 `videoId`, nhưng vẫn giữ sample mode để test.

### File A nên làm trước

- `producer/producer.py`
- `producer/requirements.txt`
- `data/sample_comments.jsonl` nếu cần cập nhật bộ dữ liệu mẫu
- `.env` ở máy của A để test

### File A nên đọc nhưng không sở hữu

- `docs/interfaces.md`
- `docker-compose.yml`
- `spark/jobs/bronze_stream.py`

### Đầu ra A cần bàn giao

- cách truyền vào 1 `videoId`
- luồng gọi YouTube API thật
- bản ghi Kafka đúng schema đã khóa trong `docs/interfaces.md`
- sample mode vẫn chạy để fallback

### Kế hoạch làm việc cho A

Giai đoạn 1:

- chạy producer mẫu hiện tại
- hiểu dạng message đang đẩy vào Kafka

Giai đoạn 2:

- thêm dependency YouTube API và env cần thiết
- viết logic lấy comment từ 1 `videoId`
- map dữ liệu về schema chung

Giai đoạn 3:

- hỗ trợ cả `sample` và `youtube_api`
- đảm bảo Bronze vẫn đọc được bình thường

Giai đoạn 4:

- đưa cho B và C 5 đến 10 bản ghi mẫu từ API thật
- ghi rõ cột nào có thể null, cột nào luôn có

### Vì sao A có thể làm độc lập

- sample producer đã có sẵn
- Kafka topic đã cố định
- B không cần chờ A hoàn thiện API thật mới bắt đầu được

### Lệnh A tự kiểm tra

```powershell
docker compose up -d producer
docker compose logs --tail 100 producer
```

Kiểm tra topic bằng Kafka UI:

- `http://localhost:8080`

### Điều kiện để A xem như xong

- nhập được 1 `videoId`
- Kafka nhận bản ghi từ YouTube API thật
- sample mode vẫn chạy
- schema Kafka đúng hợp đồng chung

## 4. Người B: Bronze, Silver, Gold và model

### Mục tiêu chính

Cải tiến pipeline xử lý dữ liệu và thay baseline sentiment hiện tại bằng workflow model tốt hơn.

### Điều B cần nắm rõ

B không cần chờ A xong API.

B bắt đầu từ:

- `data/sample_comments.jsonl`
- hợp đồng message trong `docs/interfaces.md`
- các Spark job baseline đã có

### File B nên làm trước

- `spark/jobs/bronze_stream.py`
- `spark/jobs/silver_stream.py`
- `spark/jobs/gold_stream.py`
- có thể tạo thêm script train/inference trong `spark/jobs/` sau khi thống nhất với chủ

### File B nên đọc nhưng không sở hữu

- `docs/interfaces.md`
- `spark/sql/register_tables.sql`
- `data/sample_comments.jsonl`

### Đầu ra B cần bàn giao

- Bronze ổn định và không phá hợp đồng schema
- Silver tốt hơn ở làm sạch, đặc trưng, sentiment
- có đường train model rõ ràng
- Gold có metric phù hợp cho dashboard

### Kế hoạch làm việc cho B

Giai đoạn 1:

- chạy baseline Bronze, Silver, Gold bằng dữ liệu mẫu
- xác nhận schema và output hiện tại

Giai đoạn 2:

- cải tiến Bronze nếu cần bổ sung metadata hoặc xử lý schema
- không biến Bronze thành tầng cleaning nặng

Giai đoạn 3:

- cải tiến Silver preprocessing
- xử lý null, text bẩn, ngôn ngữ không đồng đều
- xác định feature sentiment
- giữ cơ chế dedup theo `comment_id`

Giai đoạn 4:

- chuẩn bị format dữ liệu train
- chọn hướng model
- train hoặc tích hợp model tốt hơn
- đưa kết quả model quay lại Silver

Giai đoạn 5:

- cải tiến Gold để C có nhiều metric hơn
- nhưng vẫn giữ bộ cột baseline để C không bị vỡ dashboard

### Hướng làm việc tối ưu cho B

- giữ baseline keyword hiện tại song song với hướng model mới
- thử nghiệm dần dần, không sửa một lần gây vỡ toàn stream

### Lệnh B tự kiểm tra

```powershell
docker compose up -d spark-bronze spark-silver spark-gold
docker compose logs --tail 100 spark-bronze
docker compose logs --tail 100 spark-silver
docker compose logs --tail 100 spark-gold
```

Kiểm tra 3 bảng sau khi đăng ký:

```powershell
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SELECT * FROM lakehouse.bronze_youtube_comments LIMIT 5'"
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SELECT comment_id, text_clean, sentiment FROM lakehouse.silver_youtube_comments LIMIT 10'"
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SELECT * FROM lakehouse.gold_youtube_comment_metrics LIMIT 10'"
```

### Điều kiện để B xem như xong

- Bronze vẫn ingest đúng
- Silver sạch hơn và sentiment tốt hơn
- có đường model test được
- Gold mở ra metric hữu ích cho C

## 5. Người C: Metastore, SQL, JDBC và Power BI

### Mục tiêu chính

Sở hữu lớp truy cập dữ liệu và trình bày để dữ liệu xử lý có thể query được và lên dashboard.

### File C nên làm trước

- `hive/conf/hive-site.xml.template`
- `hive/scripts/start-metastore.sh`
- `spark/sql/register_tables.sql`
- `scripts/download_hive_jdbc.ps1`

### File C nên đọc nhưng không sở hữu

- `docs/interfaces.md`
- `docker-compose.yml`
- `spark/jobs/gold_stream.py`

### Đầu ra C cần bàn giao

- Hive Metastore ổn định trên SQL Server local
- đăng ký bảng external cho Bronze, Silver, Gold
- Spark Thrift Server truy cập được
- JDBC test qua
- Power BI đọc được Gold và có dashboard đầu tiên

### Kế hoạch làm việc cho C

Giai đoạn 1:

- chạy baseline Metastore
- xác nhận kết nối tới SQL Server local
- xác nhận đăng ký bảng `lakehouse` thành công

Giai đoạn 2:

- query thử Bronze, Silver, Gold trong Spark SQL
- xác nhận Thrift Server nghe cổng `10000`

Giai đoạn 3:

- test JDBC bằng DBeaver hoặc công cụ tương tự
- chuẩn bị thông tin kết nối cho Power BI

Giai đoạn 4:

- dựng dashboard Power BI đầu tiên trên Gold
- ưu tiên đơn giản, ổn định
- khi B thêm metric thì cập nhật dashboard sau

### Vì sao C có thể làm độc lập

- Metastore, đăng ký bảng và Thrift Server đã có sẵn
- C có thể test trên bảng baseline trước khi B nâng cấp model

### Lệnh C tự kiểm tra

```powershell
docker compose up -d hive-metastore spark-thriftserver
docker compose logs --tail 100 hive-metastore
docker compose logs --tail 100 spark-thriftserver
```

Đăng ký và query bảng:

```powershell
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -f /opt/sql/register_tables.sql"
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SHOW TABLES IN lakehouse'"
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SELECT * FROM lakehouse.gold_youtube_comment_metrics LIMIT 10'"
```

### Điều kiện để C xem như xong

- Metastore ổn định với SQL Server local
- bảng đăng ký và query được
- JDBC truy cập được qua Spark Thrift Server
- Power BI đọc được Gold

## 6. Vai trò của chủ

Chủ nên tập trung vào tích hợp và giữ phạm vi:

- giữ ổn định tên dùng chung
- phê duyệt thay đổi schema
- phê duyệt thay đổi `docker-compose.yml` và file dùng chung
- chạy full integration sau mỗi phase của A, B, C
- quyết định khi nào baseline đủ ổn để merge chung

## 7. Thứ tự tích hợp để tránh vỡ hệ thống

Không nên merge tất cả cùng lúc.

Thứ tự gợi ý:

1. A chứng minh collector API thật map đúng schema chung
2. B xác nhận Bronze và Silver vẫn ăn schema đó
3. B xác nhận Gold vẫn giữ bộ cột tối thiểu C cần
4. C đăng ký lại và test lớp SQL
5. Chủ chạy full stack end-to-end
