# Hướng dẫn Khắc phục lỗi kết nối DBeaver (Lakehouse Nhóm 19)

Tài liệu này ghi lại các vấn đề đã gặp phải và cách xử lý khi kết nối DBeaver với Spark Thrift Server trong điều kiện tài nguyên máy hạn chế (8GB RAM).

## 1. Vấn đề 1: Lỗi "Internal Server Error" hoặc "Connection Refused"
### Nguyên nhân:
- Docker Desktop trên Windows/WSL2 bị treo hoặc crash ngầm do chạy quá nhiều container (13+ services).
- Spark Thrift Server chưa khởi động xong hoặc bị thiếu tài nguyên để mở port 10000.

### Giải pháp:
- Sử dụng script `scripts/reset_demo.ps1` để cưỡng chế dừng các tiến trình Docker và khởi động lại sạch sẽ.
- **Chiến lược tối ưu RAM:** Chỉ bật các container cần thiết phục vụ truy vấn (Serving Layer):
  ```powershell
  docker compose up -d namenode datanode hive-metastore spark-master spark-worker spark-thriftserver
  ```
- Tắt các container thu thập/xử lý (Kafka, Producer, Spark-bronze/silver/gold) nếu chỉ cần xem dữ liệu.

## 2. Vấn đề 2: Lỗi "TTransportException"
### Nguyên nhân:
- Sai phương thức xác thực (Authentication). Spark Thrift Server trong dự án này dùng cơ chế **NOSASL**.

### Giải pháp trong DBeaver:
- Chuyển `Connect by` sang **URL**.
- Sử dụng JDBC URL theo cấu trúc:
  ```text
  jdbc:hive2://localhost:10000/;auth=noSasl
  ```

## 3. Vấn đề 3: Lỗi "Cannot find catalog plugin class ... DeltaCatalog"
### Nguyên nhân:
- Spark Thrift Server không tìm thấy thư viện Delta Lake (thường do folder `/tmp/.ivy2` bị xóa khi reset Docker).

### Giải pháp:
- Đã được cập nhật trực tiếp vào `spark/Dockerfile` để tự động tải các file Jar: `delta-core` và `delta-storage` vào thư mục `/opt/spark/jars/`.

## 4. Vấn đề 4: Kết nối bị treo (Determine default catalog/schema)
### Nguyên nhân:
- Spark Master/Worker không có đủ tài nguyên hoặc **Spark Worker chưa được bật**. 
- DBeaver cố gắng quét toàn bộ Metadata (cấu trúc bảng) ngay khi vừa kết nối, gây quá tải cho Thrift Server.

### Giải pháp:
- **Bắt buộc phải bật Spark Worker** cùng với Thrift Server.
- Xóa tên database `lakehouse` trong ô cấu hình `Database/Schema` của DBeaver. Để trống phần này để vào nhanh hơn, sau đó dùng lệnh `USE lakehouse;` trong SQL.

---
*Ghi chú: Luôn đảm bảo biểu tượng Docker Desktop dưới Taskbar hiện màu xanh lá cây trước khi bấm "Test Connection".*
