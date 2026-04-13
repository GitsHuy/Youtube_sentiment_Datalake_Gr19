# Report Checkpoint 6

Ngày cập nhật: `2026-04-13`

## 1. Mục tiêu checkpoint

Checkpoint 6 nâng Gold từ lớp tổng hợp demo thành lớp business metrics dùng được hơn cho dashboard và báo cáo.

## 2. Những gì đã chỉnh sửa

Các file chính:

- `spark/jobs/gold_stream.py`
- `spark/sql/register_tables.sql`
- `spark/sql/checkpoint6_gold_quality_checks.sql`
- `docs/interfaces.md`
- `docs/run-system.md`

Các thay đổi kỹ thuật chính:

- tách Gold thành `2` bảng thay vì chỉ `1` bảng cũ
- bổ sung bảng summary theo `event_date + video_id`
- bổ sung bảng breakdown theo `event_date + video_id + sentiment`

## 3. Cấu trúc Gold mới

### Bảng summary

`lakehouse.gold_youtube_comment_metrics`

Các nhóm metric mới:

- sản lượng: `total_comments`, `top_level_comment_count`, `reply_comment_count`
- người dùng: `unique_author_count`
- tương tác: `total_likes`, `engagement_score`
- chất lượng nội dung: `avg_text_length`, `avg_collected_delay_seconds`
- phân bố cảm xúc: `positive_comment_count`, `neutral_comment_count`, `negative_comment_count`
- tỷ lệ: `positive_ratio`, `neutral_ratio`, `negative_ratio`, `reply_ratio`

### Bảng breakdown

`lakehouse.gold_youtube_sentiment_breakdown`

Các metric:

- `comment_count`
- `comment_ratio`
- `avg_likes`
- `avg_replies`
- `reply_comment_count`
- `avg_text_length`

## 4. Kết quả kiểm tra đã xác nhận

Đã xác nhận được các điểm sau:

- `register_tables.sql` đăng ký thành công:
  - `bronze_youtube_comments`
  - `silver_youtube_comments`
  - `gold_youtube_comment_metrics`
  - `gold_youtube_sentiment_breakdown`
- HDFS có dữ liệu đầu ra mới tại:
  - `/lake/gold/youtube_comment_metrics`
  - `/lake/gold/youtube_sentiment_breakdown`
- Tại thời điểm kiểm tra, HDFS hiển thị:
  - summary parquet ghi lúc `2026-04-13 14:10`
  - breakdown parquet ghi lúc `2026-04-13 14:11`

## 5. Checkpoint 6 giúp hệ thống tốt hơn như thế nào

- Gold phù hợp hơn cho Power BI vì có cả bảng tổng hợp và bảng phân rã
- Không cần dồn quá nhiều logic tính toán sang tầng BI
- Có thể dựng dashboard theo hai hướng:
  - xem bức tranh tổng quan của video
  - xem phân bố sentiment chi tiết

## 6. Vấn đề phát sinh trong lúc kiểm tra

Trong lúc chạy full quality check bằng `spark-sql`, Docker Desktop trên máy hiện tại tiếp tục bị lỗi backend:

- `Bad Gateway`
- `Internal Server Error`

Điều này ảnh hưởng đến:

- `docker compose exec`
- các lệnh `spark-sql` chạy lâu

Nhưng không phủ nhận các bằng chứng đã có:

- Gold mới đã sinh ra parquet thật trên HDFS
- metastore đã đăng ký đủ hai bảng Gold mới

## 7. Kết luận checkpoint

Checkpoint 6 được xem là hoàn tất về mặt code, cấu trúc dữ liệu và đầu ra Gold. Phần còn lại cần làm lại khi Docker Desktop ổn định hơn là chạy trọn bộ quality check SQL để chốt bằng số liệu đầy đủ hơn.
