# Report Checkpoint 7

Ngày cập nhật: `2026-04-13`

## 1. Mục tiêu checkpoint

Checkpoint 7 ổn định lớp truy vấn và tiêu thụ dữ liệu qua Spark Thrift Server để chuẩn hóa đường nối JDBC cho DBeaver và Power BI.

## 2. Những gì đã chỉnh sửa

Các file chính:

- `docker-compose.yml`
- `scripts/smoke_thriftserver.ps1`
- `docs/run-system.md`

Các thay đổi cấu hình quan trọng:

- thêm `spark.sql.hive.thriftServer.incrementalCollect=true`
- thêm `hive.server2.authentication=NONE`
- thêm `hive.server2.enable.doAs=false`
- thêm `hive.server2.transport.mode=binary`
- bổ sung logic chờ readiness trước khi start `spark-thriftserver`:
  - đợi `hive-metastore:9083`
  - đợi `spark-master:7077`

## 3. Nguyên nhân lỗi gốc đã tìm ra

Trong các lần kiểm tra trước, `spark-thriftserver` không lên hoàn chỉnh vì khởi động quá sớm khi `hive-metastore` chưa sẵn sàng.

Log gốc đã chỉ ra:

- `Failed to connect to the MetaStore Server`
- `Could not connect to meta store using any of the URIs provided`
- `Connection refused`

Tức là lỗi gốc không nằm ở DBeaver mà nằm ở readiness giữa:

- `hive-metastore`
- `spark-master`
- `spark-thriftserver`

## 4. Cách đã sửa

Đã chỉnh `docker-compose.yml` để `spark-thriftserver` chỉ start sau khi:

- `hive-metastore:9083` trả lời kết nối TCP
- `spark-master:7077` trả lời kết nối TCP

Sau đó mới gọi:

- `start-thriftserver.sh`

## 5. Kết quả kiểm tra sau khi sửa

### Ở phía log server

Đã xác nhận trong log:

- `Connected to metastore.`
- `Starting ThriftBinaryCLIService on port 10000`
- `HiveThriftServer2 started`

### Ở phía hệ thống

Đã xác nhận:

- `docker compose ps` thấy `spark-thriftserver` ở trạng thái `Up`
- `Test-NetConnection 127.0.0.1 -Port 10000` trả về `TcpTestSucceeded : True`

### Ở phía client

Đã xác nhận:

- DBeaver kết nối thành công sau khi `spark-thriftserver` được sửa readiness

## 6. Cấu hình JDBC chuẩn đã chốt

- Driver: `Apache Hive 2`
- Host: `127.0.0.1`
- Port: `10000`
- Database: `lakehouse`
- JDBC URL đề xuất:

```text
jdbc:hive2://127.0.0.1:10000/lakehouse;auth=noSasl
```

## 7. Kết luận checkpoint

Checkpoint 7 được xem là hoàn tất.

Kết quả cuối cùng:

- Spark Thrift Server đã lên ổn định hơn
- cổng `10000` đã ready
- DBeaver đã dùng được để truy vấn kiểm tra hệ thống

Phần còn lại về Power BI không nằm ở checkpoint 7 nữa, mà phụ thuộc việc cài ODBC driver phù hợp trên máy Windows.
