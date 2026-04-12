# Interfaces

Tài liệu này khóa các điểm giao tiếp dùng chung để A, B, C có thể làm song song mà không va nhau.

## 1. Mục tiêu chung

Luồng nghiệp vụ nhóm đang nhắm tới:

- lấy bình luận từ đúng 1 video YouTube thông qua `videoId`
- đẩy bình luận vào Kafka
- lưu qua Bronze, Silver, Gold
- đăng ký metadata qua Hive Metastore
- mở dữ liệu Gold cho SQL và Power BI

Baseline hiện tại vẫn giữ `data/sample_comments.jsonl` làm nguồn fallback để mỗi thành viên test độc lập.

## 2. Hằng số dùng chung

Kafka topic:

- `youtube-comments`

Đường dẫn HDFS:

- Bronze: `hdfs://namenode:8020/lake/bronze/youtube_comments`
- Silver: `hdfs://namenode:8020/lake/silver/youtube_comments`
- Gold: `hdfs://namenode:8020/lake/gold/youtube_comment_metrics`

Database và bảng Hive:

- database: `lakehouse`
- bảng Bronze: `lakehouse.bronze_youtube_comments`
- bảng Silver: `lakehouse.silver_youtube_comments`
- bảng Gold: `lakehouse.gold_youtube_comment_metrics`

Những tên này phải giữ ổn định nếu chủ chưa cho phép đổi.

## 3. Schema Kafka hiện tại

Đây là schema mà job Bronze hiện tại đã hỗ trợ.

| Field | Type | Bắt buộc | Ghi chú |
| --- | --- | --- | --- |
| `event_time` | timestamp string | có | Spark đang parse về timestamp |
| `comment_id` | string | có | id duy nhất của bình luận |
| `video_id` | string | có | id video đang theo dõi |
| `author` | string | có | tên tác giả bình luận |
| `text` | string | có | nội dung gốc |
| `like_count` | integer | có | số lượt like |
| `reply_count` | integer | có | có thể bằng `0` nếu là reply |
| `is_reply` | boolean | có | `false` nếu là top-level, `true` nếu là reply |
| `lang` | string | không | nếu thiếu thì đưa về `unknown` |

Người A phải giữ tối thiểu schema này để Bronze không vỡ.

## 4. Schema ingestion mở rộng để xét ở bước sau

Những field dưới đây nên thêm ở vòng sau khi A và B thống nhất:

| Field | Type | Bắt buộc | Người liên quan | Ghi chú |
| --- | --- | --- | --- | --- |
| `parent_comment_id` | string | không | A + B | để truy vết reply |
| `source` | string | có | A | gợi ý `youtube_api` hoặc `sample_file` |
| `collected_at` | timestamp string | có | A | thời điểm collector lấy dữ liệu |

Quy tắc:

- A không tự ý thêm field vào luồng chính mà không báo B, vì Bronze schema sẽ phải đổi theo

## 5. Hợp đồng Bronze

Bronze hiện tại ghi ra:

- các field Kafka đã parse ở schema baseline
- `ingested_at`

Bronze phải giữ đúng vai trò:

- gần nguồn nhất có thể
- xử lý nhẹ
- phù hợp để reprocess sau này

Bronze không nên biến thành tầng cleaning hay tầng model.

## 6. Hợp đồng Silver

Cột tối thiểu của Silver hiện tại:

| Column | Ý nghĩa |
| --- | --- |
| `event_time` | thời gian sự kiện gốc |
| `comment_id` | id bình luận |
| `video_id` | id video |
| `author` | tên tác giả |
| `text` | nội dung gốc |
| `text_clean` | text đã làm sạch |
| `like_count` | like đã chuẩn hóa |
| `reply_count` | reply đã chuẩn hóa |
| `is_reply` | có phải reply hay không |
| `lang` | ngôn ngữ đã chuẩn hóa |
| `ingested_at` | thời điểm vào Bronze |
| `silver_processed_at` | thời điểm xử lý Silver |
| `positive_score` | điểm tích cực baseline |
| `negative_score` | điểm tiêu cực baseline |
| `sentiment` | nhãn cảm xúc cuối cùng |

Trạng thái hiện tại của Silver:

- đã làm sạch text
- đã normalize null
- đã dedup theo `comment_id`

Người B có thể mở rộng Silver, nhưng nên giữ những cột tối thiểu này ổn định để Gold và lớp SQL của C không bị gãy.

## 7. Hợp đồng Gold

Cột tối thiểu của Gold hiện tại:

| Column | Ý nghĩa |
| --- | --- |
| `event_date` | ngày suy ra từ `event_time` |
| `video_id` | id video |
| `sentiment` | nhóm cảm xúc |
| `comment_count` | số bình luận trong nhóm |
| `avg_likes` | like trung bình |
| `avg_replies` | reply trung bình |
| `reply_comment_count` | số bình luận là reply |

Người C nên build SQL validation và dashboard trên bộ tối thiểu này trước.

Người B có thể thêm metric mới ở Gold, nhưng cần giữ bộ cột baseline để C không phải sửa lại toàn bộ.

## 8. Quy tắc sở hữu

- A sở hữu mapping dữ liệu từ YouTube API sang schema Kafka
- B sở hữu Bronze, Silver, Gold và logic model
- C sở hữu Metastore, đăng ký bảng, Thrift/JDBC và Power BI
- chủ sở hữu `docker-compose.yml`, `.env.example`, `README.md` và tài liệu interface này

## 9. Quy tắc để làm song song

Để không chờ nhau:

- A làm theo schema Kafka tối thiểu ở trên
- B dùng `data/sample_comments.jsonl` để phát triển tiếp trong khi chờ A
- C làm theo schema Gold tối thiểu trong khi B cải tiến model
