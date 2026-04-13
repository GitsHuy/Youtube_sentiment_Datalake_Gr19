# Hợp đồng dữ liệu và giao tiếp giữa các lớp

Tài liệu này khóa những điểm giao tiếp chính để mọi thay đổi sau này vẫn bám cùng một chuẩn.

## 1. Phạm vi bài toán hiện tại

- Ingestion lấy bình luận từ đúng `1 video YouTube` tại một thời điểm chạy
- Dữ liệu đi qua `Kafka -> Bronze -> Silver -> Gold -> Thrift/JDBC`
- Dữ liệu Bronze, Silver, Gold đang lưu dưới dạng `PARQUET`
- Metadata bảng được quản lý qua `Hive Metastore`

## 2. Hằng số dùng chung

Kafka:

- Topic: `youtube-comments`

HDFS:

- Bronze: `hdfs://namenode:8020/lake/bronze/youtube_comments`
- Silver: `hdfs://namenode:8020/lake/silver/youtube_comments`
- Gold summary: `hdfs://namenode:8020/lake/gold/youtube_comment_metrics`
- Gold breakdown: `hdfs://namenode:8020/lake/gold/youtube_sentiment_breakdown`

Hive:

- Database: `lakehouse`
- Bronze table: `lakehouse.bronze_youtube_comments`
- Silver table: `lakehouse.silver_youtube_comments`
- Gold summary table: `lakehouse.gold_youtube_comment_metrics`
- Gold breakdown table: `lakehouse.gold_youtube_sentiment_breakdown`

## 3. Schema chuẩn cho một comment YouTube

Các trường nền mà producer, Kafka, Bronze và Silver phải cùng hiểu:

| Trường | Kiểu | Bắt buộc | Ý nghĩa |
| --- | --- | --- | --- |
| `event_time` | timestamp | có | thời điểm comment xuất hiện trên YouTube |
| `collected_at` | timestamp | có | thời điểm collector lấy được comment |
| `comment_id` | string | có | khóa nghiệp vụ duy nhất của comment |
| `video_id` | string | có | id video đang theo dõi |
| `author` | string | có | tên hiển thị của người bình luận |
| `text` | string | có | nội dung gốc của comment |
| `like_count` | int | có | số like tại thời điểm thu thập |
| `reply_count` | int | có | số reply của comment |
| `is_reply` | boolean | có | `true` nếu là reply |
| `parent_comment_id` | string/null | không | id comment cha nếu là reply |
| `lang` | string | không | mã ngôn ngữ hoặc `unknown` |
| `source` | string | có | nguồn dữ liệu như `sample_file` hoặc `youtube_api` |

## 4. Hợp đồng của lớp Bronze

Bronze giữ dữ liệu raw nhưng đã parse JSON thành công.

Bronze phải có:

- toàn bộ trường chuẩn của comment
- `ingested_at`

Bronze không làm:

- suy luận sentiment
- tổng hợp business metric
- làm sạch text nặng

## 5. Hợp đồng của lớp Silver

Silver kế thừa Bronze và bổ sung xử lý làm sạch, deduplicate và sentiment.

Silver hiện có các nhóm cột chính:

- Cột nguồn: `event_time`, `collected_at`, `comment_id`, `video_id`, `author`, `text`, `like_count`, `reply_count`, `is_reply`, `parent_comment_id`, `lang`, `source`, `ingested_at`
- Cột làm sạch: `text_clean`, `text_length`, `collected_delay_seconds`, `silver_processed_at`
- Cột sentiment: `positive_score`, `negative_score`, `sentiment`

Quy ước checkpoint 5:

- Model mặc định: `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual`
- Nhãn đầu ra luôn chuẩn hóa về `positive`, `neutral`, `negative`
- `positive_score` và `negative_score` đang scale về thang `0-100`
- Có thể bật fallback keyword qua `SENTIMENT_FALLBACK_TO_KEYWORD=true`
- Khi benchmark nghiêm túc, nên đặt `SENTIMENT_FALLBACK_TO_KEYWORD=false`

## 6. Hợp đồng của lớp Gold

Từ checkpoint 6, Gold được tách thành `2` bảng để thuận tiện cho dashboard.

### Gold summary

Table: `lakehouse.gold_youtube_comment_metrics`

Mục đích:

- lưu các chỉ số tổng hợp theo `event_date + video_id`

Các cột:

- `event_date`
- `video_id`
- `total_comments`
- `top_level_comment_count`
- `reply_comment_count`
- `unique_author_count`
- `total_likes`
- `avg_likes_per_comment`
- `avg_reply_count`
- `avg_text_length`
- `avg_collected_delay_seconds`
- `positive_comment_count`
- `neutral_comment_count`
- `negative_comment_count`
- `positive_ratio`
- `neutral_ratio`
- `negative_ratio`
- `reply_ratio`
- `engagement_score`

### Gold sentiment breakdown

Table: `lakehouse.gold_youtube_sentiment_breakdown`

Mục đích:

- lưu breakdown theo `event_date + video_id + sentiment`

Các cột:

- `event_date`
- `video_id`
- `sentiment`
- `comment_count`
- `comment_ratio`
- `avg_likes`
- `avg_replies`
- `reply_comment_count`
- `avg_text_length`

## 7. Quy tắc nghiệp vụ đang áp dụng

- `comment_id` là khóa deduplicate chính ở Silver
- `collected_at` phải lớn hơn hoặc bằng `event_time`
- Reply phải có `parent_comment_id`
- Text rỗng sau khi làm sạch sẽ bị loại ở Silver
- Một bài test “1 video” nên giữ cùng một `video_id` trong toàn bộ lần ingest đó

## 8. Tài liệu và script liên quan

- Đánh giá model: `scripts/evaluate_seed_labels.py`
- Seed labels 100 comment: `data/evaluation/assistant_seed_labels_100.csv`
- Kết quả so sánh model: `data/evaluation/model_vs_seed_labels_100.csv`
- Tóm tắt chỉ số đánh giá: `data/evaluation/model_vs_seed_labels_100_summary.json`
- Kiểm tra chất lượng Gold: `spark/sql/checkpoint6_gold_quality_checks.sql`
- Smoke test Thrift: `scripts/smoke_thriftserver.ps1`
