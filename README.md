# Cập nhật Hệ thống Real-Time Sentiment Datalakehouse (Youtube Comments)

Tài liệu này tổng hợp toàn bộ các thay đổi cốt lõi đã được đội ngũ tinh chỉnh để hệ thống chạy trơn tru, lấy dữ liệu thời gian thực từ Youtube API thay vì dữ liệu tĩnh, đồng thời xử lý triệt để lỗi sập RAM cục bộ và mất kết nối Hive Metastore trên môi trường Laptop.

## 🛠️ Danh sách các tệp (Files) đã được nâng cấp Cốt Lõi:

### 1. `docker-compose.yml`
- **Thêm dịch vụ `sqlserver`**: Đây là trái tim lưu trữ siêu dữ liệu (Metadata) cho `hive-metastore`. Cấu hình thành công SQL Server giúp Hive ghi nhận và cấp phát danh mục Bảng dữ liệu một cách bảo mật.
- **Vá lỗi môi trường `producer`**: Đã cắm thành công biến môi trường `YOUTUBE_API_KEY` và `YOUTUBE_VIDEO_ID` trực tiếp vào luồng rễ Docker của `producer`, giúp nó có quyền lực ngỏ lời nạp dữ liệu từ kho Google Youtube.

### 2. `spark/Dockerfile`
- **Nâng cấp Image nền tảng**: Đổi sang sử dụng base `apache/spark-py:v3.3.0` để hệ thống tự động tích hợp sẵn nhân PySpark. Đã lược bỏ các biến dư thừa không cần thiết để Docker nhẹ gọn hơn khi Build khởi động.

### 3. `producer/producer.py` & `requirements.txt`
- **Chuyển đổi Ingestion Mode**: Đã nâng cấp chế độ từ chọc dữ liệu mẫu tĩnh (`sample`) sang thực chiến hút dữ liệu thật bằng API (`youtube_api`).
- **Thêm vòng lặp hút rễ nhánh**: Bổ sung thuật toán vào chuỗi `build_reply_record`, cho phép kéo không chỉ bình luận gốc mà còn duyệt bộ đệ quy kéo thêm cả luồng trả lời bên dưới (Thread replies), giúp thu hoạch hàng ngàn comment một cách triệt để không sót 1 ai.

### 4. `spark/jobs/bronze_stream.py`
- **Chỉnh tiêu cự Kafka**: Chuyển tín hiệu đầu vào `startingOffsets` từ `latest` (bỏ rơi quá khứ) sang `earliest` (vét cạn rương). Đảm bảo Spark Consumer đọc trọn vẹn dòng chảy lịch sử ngay cả sau khi máy sập.

### 5. `spark/jobs/silver_stream.py`
- **Tối ưu hóa Màng lọc AI (PhoBERT Tiếng Việt)**: Lắp ghép hoàn chỉnh mô hình Học Sâu `wonrax/phobert-base-vietnamese-sentiment` chạy kẹp trong hệ thống nhúng Pandas UDF thần thánh. Đây là bước đột phá kiến trúc giúp chia nhỏ gánh nặng, để CPU Laptop không bị nghẽn cổ chai khi nuốt cả ngàn bình luận cùng lúc.

### 6. `spark/jobs/gold_stream.py` & `register_tables.sql`
- **Sản xuất Báo cáo Vàng (Gold Bar)**: Hoàn thiện logic tổng hợp cảm xúc trích xuất kết quả thành 2 siêu chỉ báo phục vụ Dashboard: Bảng Metrics Tổng (`gold_youtube_comment_metrics`) và Bảng tỷ trọng Cảm xúc (`gold_youtube_sentiment_breakdown`).
- **Đăng kí Sổ Đỏ thành công**: Vá lỗi kết nối DDL DBeaver, cắm hoàn mỹ các bảng trên vào Hive Metastore để Thriftserver phát sóng chảo HTTP đi muôn phương.


