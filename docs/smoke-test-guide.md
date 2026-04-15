# Hướng dẫn smoke test

Tài liệu này hướng dẫn cách kiểm tra nhanh sức khỏe hệ thống mà không ảnh hưởng việc chạy pipeline bình thường.

## 1. Mục đích

`smoke_test.ps1` là script kiểm tra nhanh:

- các container nền tảng chính có đang chạy không
- Spark Thrift Server có mở cổng `10000` không
- metastore có thấy các bảng trong `lakehouse` không
- dữ liệu Bronze, Silver, Gold có tồn tại và truy vấn được không

Script này là tùy chọn:

- không chạy cũng không làm hệ thống dừng
- chỉ chạy khi muốn xác minh hệ thống sau khi khởi động lại, sau khi sửa code, hoặc trước khi demo

## 2. Cách chạy

Chạy tại thư mục gốc repo:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_test.ps1
```

Nếu không muốn script tự khởi động lại `spark-thriftserver`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_test.ps1 -SkipThriftStart
```

Nếu chỉ muốn test cổng và metastore, bỏ qua quality checks:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_test.ps1 -SkipQualityChecks
```

## 3. Script làm gì

Script sẽ lần lượt:

1. Kiểm tra các service chính:
   - `kafka`
   - `namenode`
   - `datanode`
   - `hive-metastore`
   - `spark-master`
   - `spark-worker`
2. Đảm bảo `spark-thriftserver` đang chạy
3. Chờ cổng `10000` sẵn sàng
4. Chạy lại `register_tables.sql`
5. Chạy `SHOW TABLES IN lakehouse`
6. Chạy `spark/sql/checkpoint11_quality_checks.sql`

## 4. Ý nghĩa file quality checks

File:

- `spark/sql/checkpoint11_quality_checks.sql`

gồm các truy vấn kiểm tra:

- số dòng của Bronze, Silver, Gold
- số `video_id` khác nhau
- số dòng bị null ở cột quan trọng
- duplicate `comment_id` ở Silver
- phân bố `sentiment`
- luồng dữ liệu từ Bronze -> Silver -> Gold theo từng `video_id`

## 5. Khi nào xem là PASS

PASS khi:

- script chạy hết không lỗi
- `SHOW TABLES IN lakehouse` nhìn thấy các bảng chính
- các bảng Bronze, Silver, Gold trả về số dòng hợp lý

## 6. Khi nào cần kiểm tra thêm

Nên kiểm tra sâu hơn nếu:

- Thrift mở cổng nhưng query không ra bảng
- Bronze có dữ liệu nhưng Silver hoặc Gold không tăng
- `silver_duplicate_comment_id` lớn bất thường
- `silver_null_sentiment` khác `0`

## 7. Lưu ý

- Đây là kiểm tra nhanh, không thay thế việc đọc log chi tiết nếu pipeline lỗi
- Script không bắt buộc phải chạy mỗi lần dùng hệ thống
- Có thể dùng script này như bước “khám nhanh” trước khi mở DBeaver hoặc Power BI
