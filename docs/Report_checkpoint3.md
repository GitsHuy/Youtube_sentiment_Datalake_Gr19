# Report Checkpoint 3

Ngày cập nhật: `2026-04-13`

## 1. Mục tiêu checkpoint

Checkpoint 3 có mục tiêu thay ingestion mẫu bằng ingestion thật từ `YouTube Data API v3`, nhưng vẫn giữ được khả năng fallback về `sample mode` để test nhanh. Sau khi chạy thực tế, checkpoint này được mở rộng thêm một bước kỹ thuật cần thiết: xử lý lỗi `StateSchemaNotCompatible` ở `spark-silver` để toàn pipeline đi được tới `Gold`.

## 2. Những gì đã làm

- Thêm dependency `requests` cho producer để gọi `YouTube Data API`.
- Hoàn thiện `youtube_api mode` trong `producer/producer.py`.
- Bổ sung các biến môi trường `YOUTUBE_*` vào `.env.example`.
- Bổ sung truyền các biến `YOUTUBE_*` từ `docker-compose.yml` vào container `producer`.
- Thêm logic chuẩn hóa `YOUTUBE_VIDEO_ID` để chấp nhận cả `videoId` thuần hoặc URL YouTube đầy đủ.
- Thêm cơ chế bỏ qua record lỗi có `text` rỗng thay vì làm hỏng cả batch.
- Cập nhật `docs/run-system.md` để hướng dẫn chạy ingestion thật.
- Kiểm tra lại pipeline sau khi ingest thật và phát hiện lỗi `StateSchemaNotCompatible` ở `spark-silver`.
- Reset có kiểm soát checkpoint/output của `Silver` và `Gold` trên HDFS để khớp với schema mới từ checkpoint 2.
- Chạy lại `spark-silver` và `spark-gold`, sau đó kiểm tra trực tiếp bằng `spark-sql`.

## 3. Kết quả đạt được

- Producer gọi được `YouTube Data API v3` thật với `HTTP 200`.
- Producer gửi được dữ liệu thật vào Kafka cho `video_id=DXVHmGoCTco`.
- Bronze tiếp nhận và ghi thêm dữ liệu thật lên HDFS.
- Silver chạy lại thành công sau khi reset state cũ.
- Gold sinh được dữ liệu tổng hợp mới từ Silver.
- Kiểm thử trực tiếp bằng `spark-sql` xác nhận:
  - `silver_rows = 220`
  - `gold_rows = 5`
- Luồng hiện tại đã đi được hết chặng:
  - `YouTube API -> Kafka -> Bronze -> Silver -> Gold`

## 4. Vấn đề phát hiện trong checkpoint

- `producer` ban đầu chưa nhận các biến `YOUTUBE_*` từ `docker-compose.yml`.
- `YOUTUBE_VIDEO_ID` dễ bị nhập sai khi người dùng dán cả URL hoặc thêm tham số như `&t=...`.
- Dữ liệu thực tế từ YouTube có thể chứa reply bị rỗng `text`.
- `spark-silver` bị lỗi `StateSchemaNotCompatible` vì state/checkpoint cũ vẫn giữ schema trước checkpoint 2, trong khi schema mới đã thêm:
  - `collected_at`
  - `parent_comment_id`
  - `source`

## 5. Đã cải thiện gì sau checkpoint

- Ingestion không còn chỉ là demo bằng file mẫu, mà đã lấy được dữ liệu thật từ YouTube.
- Producer chịu lỗi tốt hơn khi gặp dữ liệu thực tế không sạch.
- Quy trình nhập `YOUTUBE_VIDEO_ID` thân thiện hơn cho người vận hành.
- Pipeline không còn bị kẹt ở `Silver` do state cũ không tương thích.
- Hệ thống hiện đã có bằng chứng kiểm thử end-to-end tới `Gold`, không chỉ dừng ở `Bronze`.

## 6. Cần cải thiện tiếp

- Chưa triển khai `Delta Lake`, hiện vẫn dùng `PARQUET`.
- Phần sentiment ở `Silver` vẫn là baseline, chưa phải mô hình nâng cao.
- Chưa có quy trình tự động migrate/reset checkpoint khi schema streaming thay đổi.
- Kết nối `DBeaver` và `Spark Thrift Server` vẫn cần tiếp tục ổn định hóa để người khác làm theo là ra kết quả giống nhau.
- Chưa có bộ test tự động cho ingestion thật và cho các truy vấn xác nhận dữ liệu ở `Bronze/Silver/Gold`.

## 7. Kết luận checkpoint

Checkpoint 3 được xem là hoàn tất vì hệ thống đã ingest được dữ liệu thật từ đúng 1 video YouTube và đẩy dữ liệu đi hết toàn pipeline tới `Gold`. Điểm còn lại không còn là lỗi chặn luồng chính, mà là các hạng mục nâng cấp chất lượng hệ thống ở các checkpoint tiếp theo.
