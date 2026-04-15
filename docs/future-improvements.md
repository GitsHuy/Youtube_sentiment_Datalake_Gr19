# Đề Xuất Cải Thiện Và Bước Tiếp Theo

Tài liệu này dùng để note lại các đề xuất cải thiện hệ thống sau các checkpoint đã hoàn thành. Đây không phải log thực thi, mà là danh sách định hướng để tránh quên các việc cần làm tiếp.

## 1. Hướng ưu tiên hiện tại

Với quyết định hiện tại là giữ nguyên `1 video_id` ổn định để phát triển tiếp, thứ tự ưu tiên gần nên là:

1. Nâng ingestion từ kiểu theo đợt sang polling liên tục ổn định hơn.
2. Đánh giá lại sentiment model bằng bộ nhãn tay `100-200` comment thật.
3. Mở rộng Gold và dashboard để tăng giá trị trình bày.
4. Chuẩn hóa smoke test, quality check và metadata/query.
5. Chỉ sau khi pipeline đã ổn định mới nâng kiến trúc sang `Delta Lake`.

Ghi chú:

- Script reset dữ liệu test `1 video` vẫn có giá trị, nhưng hiện không còn là ưu tiên số 1.
- Reset nên được xem là công cụ hỗ trợ kỹ thuật dùng khi cần, không phải bước bắt buộc cho mọi lần chạy.

## 2. Đề xuất reset dữ liệu có kiểm soát

Mục tiêu:

- giữ nguyên code và hạ tầng
- chỉ làm sạch dữ liệu vận hành để test lại đúng bài toán `1 video`

Phạm vi reset nên ưu tiên:

- `Bronze`
- `Silver`
- `Gold`
- các thư mục `checkpoint` tương ứng

Những gì cần giữ:

- `docker-compose.yml`
- cấu hình HDFS, Hive, Spark
- `.env`
- code `producer`, `bronze`, `silver`, `gold`
- tài liệu và SQL

Kết quả mong muốn sau reset:

- `Bronze` chỉ còn dữ liệu mới của đúng `YOUTUBE_VIDEO_ID` đang test
- `Silver` chỉ sinh dữ liệu từ đúng video đó
- `Gold` chỉ tổng hợp trên đúng dữ liệu mới

Khi nào nên làm reset:

- khi đổi `YOUTUBE_VIDEO_ID`
- khi đổi schema ở `Bronze`, `Silver` hoặc `Gold`
- khi đổi logic streaming khiến checkpoint cũ không còn an toàn
- khi cần benchmark sạch cho báo cáo hoặc demo chính thức
- khi nghi ngờ dữ liệu cũ đang làm nhiễu kết quả

Khi nào chưa cần reset:

- khi vẫn giữ nguyên `video_id`
- khi chỉ sửa tài liệu, truy vấn, dashboard hoặc kiểm tra hệ thống còn chạy
- khi đang phát triển tăng dần trên cùng một luồng dữ liệu ổn định

## 3. Đề xuất cải thiện Producer

### 3.1. Producer chạy liên tục

Hiện tại `producer.py` đang chạy theo kiểu one-shot:

- gọi YouTube API
- gửi một đợt record vào Kafka
- kết thúc

Đề xuất nâng cấp:

- thêm chế độ polling liên tục theo chu kỳ, ví dụ mỗi `30s`, `60s`, `120s`
- cho phép cấu hình bằng biến môi trường như:
  - `YOUTUBE_POLL_INTERVAL_SECONDS`
  - `YOUTUBE_CONTINUOUS_MODE=true|false`

Lợi ích:

- hệ thống nhìn “ra ingestion streaming” hơn
- phù hợp hơn với cách giải thích Kafka nhận dữ liệu mới liên tục

### 3.2. Tránh gửi trùng từ Producer

Đề xuất:

- lưu mốc lần lấy dữ liệu gần nhất
- hoặc lưu tập `comment_id` đã gửi gần đây
- trước khi gửi Kafka thì bỏ qua record trùng

Lợi ích:

- giảm dữ liệu trùng đẩy vào Kafka
- giảm tải cho `Bronze` và `Silver`

### 3.3. Ghi log vận hành rõ hơn

Đề xuất:

- log rõ số record lấy được theo từng page
- log số record hợp lệ
- log số record bị bỏ qua
- log rõ `video_id` hiện đang chạy

Lợi ích:

- dễ debug hơn
- dễ trình bày khi demo

## 4. Đề xuất cải thiện Bronze và Silver

### 4.1. Có script reset dữ liệu theo bài test

Đề xuất:

- tạo script reset riêng cho bài test `1 video`
- script này chỉ dọn:
  - HDFS path của `Bronze`, `Silver`, `Gold`
  - checkpoint tương ứng
- không đụng vào các file code hay cấu hình

Lợi ích:

- mỗi lần cần test sạch sẽ không phải nhớ lệnh thủ công
- giảm rủi ro xóa nhầm

### 4.2. Tự động hóa kiểm tra chất lượng dữ liệu

Hiện tại đã có:

- `spark/sql/checkpoint4_quality_checks.sql`

Đề xuất tiếp:

- gom truy vấn kiểm tra chất lượng thành smoke test
- chạy sau mỗi lần ingest lớn
- lưu kết quả ra file báo cáo ngắn

Lợi ích:

- đo được chất lượng dữ liệu định kỳ
- dễ chứng minh hệ thống đã sạch hơn

### 4.3. Ổn định hơn khi đổi schema streaming

Đề xuất:

- có note hoặc script hỗ trợ reset state khi schema `Silver/Gold` thay đổi
- về sau nếu nâng thêm cột mới sẽ không bị động như lỗi `StateSchemaNotCompatible`

## 5. Đề xuất cải thiện Gold

### 5.1. Làm Gold ít phụ thuộc vào timing khởi động hơn

Hiện tại `gold_stream.py` còn phụ thuộc vào việc `Silver` đã có file thật trước khi Gold đọc schema.

Đề xuất:

- thêm bước chờ đường dẫn Silver có dữ liệu
- hoặc đọc schema theo contract ổn định thay vì phụ thuộc file đầu tiên

Lợi ích:

- giảm lỗi khởi động Gold quá sớm
- startup ổn định hơn

### 5.2. Mở rộng metric business

Sau checkpoint 5 có thể bổ sung:

- tỷ lệ positive / negative / neutral
- top comment theo like
- số lượng reply theo ngày
- xu hướng cảm xúc theo thời gian

## 6. Ưu tiên tiếp theo theo góc nhìn hiện tại

Các hướng đang đáng làm tiếp nhất:

1. `Ingestion`: cho `producer.py` chạy polling liên tục và giảm trùng comment.
2. `Sentiment model`: tạo bộ nhãn tay tốt hơn và benchmark lại với `SENTIMENT_FALLBACK_TO_KEYWORD=false`.
3. `Gold + dashboard`: mở rộng thêm metric business để phục vụ trình bày.
4. `Vận hành`: tăng độ tin cậy bằng smoke test, quality check, refresh metadata khi cần.
5. `Kiến trúc`: chỉ chuyển sang `Delta Lake` sau khi các phần trên đủ ổn định.

Các hướng hiện chưa cần ưu tiên ngay:

- script reset dữ liệu test cho `1 video` nếu hệ thống vẫn giữ nguyên `video_id`
- huấn luyện mô hình riêng từ đầu khi chưa đánh giá đủ tốt mô hình pretrained hiện tại

## 7. Đề xuất dài hạn

Các việc để làm sau khi checkpoint 5 và 6 ổn hơn:

- chuẩn hóa kết nối `DBeaver` và `Spark Thrift Server`
- viết smoke test startup đầy đủ
- tự động đăng ký lại bảng hoặc refresh metadata khi cần
- chuyển `Bronze`, `Silver`, `Gold` từ `PARQUET` sang `Delta Lake`
- hoàn thiện tài liệu demo cuối cùng và dashboard

## 8. Ghi chú điều hành

Nguyên tắc tiếp tục làm việc:

- ưu tiên cô lập dữ liệu test trước khi nâng model
- ưu tiên ổn định luồng chạy trước khi mở rộng tính năng
- mọi thay đổi có khả năng làm mất dữ liệu test cần được xác nhận trước khi thực thi
