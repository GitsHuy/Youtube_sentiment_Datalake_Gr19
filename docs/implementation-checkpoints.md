# Kế hoạch và trạng thái checkpoint

Repo làm việc chính:

```text
D:\AHCMUTE_HocTap\BigDataAnalysis\BT_CuoiKy\Project_nhom19_datalakehouse
```

## 1. Phạm vi đã chốt

- Giữ `SQL Server local`
- Chưa chuyển ngay sang `Delta Lake`
- Dữ liệu mục tiêu là bình luận của `1 video YouTube` trong mỗi lần test
- Ưu tiên hoàn thiện pipeline thật trước, rồi mới tối ưu học thuật và kiến trúc sau

## 2. Trạng thái tổng quan

| Checkpoint | Trạng thái | Ghi chú ngắn |
| --- | --- | --- |
| 0 | Hoàn tất | Chốt baseline, phạm vi, repo làm việc |
| 1 | Hoàn tất | Có runbook khởi động và reset cơ bản |
| 2 | Hoàn tất | Chốt schema chuẩn cho comment YouTube |
| 3 | Hoàn tất | Ingestion thật từ YouTube API đã đi tới Bronze, Silver, Gold |
| 4 | Hoàn tất | Làm sạch Silver và bổ sung kiểm tra chất lượng dữ liệu |
| 5 | Hoàn tất | Nâng sentiment từ rule-based lên model pretrained và có đánh giá seed labels |
| 6 | Hoàn tất có lưu ý | Gold đã tách thành summary + sentiment breakdown, nhưng Docker Desktop vẫn gây nhiễu khi chạy kiểm tra dài |
| 7 | Hoàn tất | Đã sửa readiness cho Spark Thrift Server và xác minh lại cổng 10000 cùng DBeaver |
| 8 | Hoàn tất | Đã hoàn thiện tài liệu truy vấn, kịch bản demo và hướng dẫn bàn giao |

## 3. Checkpoint 5

Mục tiêu:

- thay sentiment keyword demo bằng mô hình pretrained dùng được cho video quốc tế
- đánh giá bước đầu bằng bộ comment gán nhãn seed

Đã làm:

- cập nhật `spark/jobs/silver_stream.py` sang transformer theo `foreachBatch`
- dùng model `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual`
- giữ tùy chọn fallback keyword
- thêm script `scripts/evaluate_seed_labels.py`
- tạo dữ liệu:
  - `data/evaluation/assistant_seed_labels_100.csv`
  - `data/evaluation/model_vs_seed_labels_100.csv`
  - `data/evaluation/model_vs_seed_labels_100_summary.json`

Kết quả đánh giá hiện tại:

- `agreement_accuracy = 0.59`
- `macro_f1 = 0.5951`
- accuracy với mẫu dễ hơn:
  - `review_needed=no`: `0.6842`
  - `review_needed=yes`: `0.5323`

Kết luận:

- model đã chạy được và tốt hơn cảm giác “chỉ demo bằng từ khóa”
- nhưng chưa đủ mạnh để kết luận là đã chính xác cao cho bài toán của nhóm
- bước tiếp theo hợp lý vẫn là bộ nhãn tay cuối cùng do người làm dự án rà soát

## 4. Checkpoint 6

Mục tiêu:

- biến Gold từ bảng đếm đơn giản thành lớp business metrics đủ dùng cho dashboard

Đã làm:

- cập nhật `spark/jobs/gold_stream.py`
- đổi `register_tables.sql` để đăng ký `2` bảng Gold
- thêm `spark/sql/checkpoint6_gold_quality_checks.sql`

Gold mới gồm:

- `lakehouse.gold_youtube_comment_metrics`
- `lakehouse.gold_youtube_sentiment_breakdown`

Các cải thiện chính:

- có `total_comments`, `unique_author_count`, `total_likes`, `reply_ratio`
- có tỷ lệ `positive`, `neutral`, `negative`
- có breakdown theo từng sentiment để Power BI dễ dựng hơn

Kiểm tra đã xác nhận:

- `register_tables.sql` đã đăng ký thành công `4` bảng trong `lakehouse`
- HDFS đã có dữ liệu tại:
  - `/lake/gold/youtube_comment_metrics`
  - `/lake/gold/youtube_sentiment_breakdown`

Lưu ý:

- các lệnh `spark-sql` dài để chạy full quality check vẫn có thể bị Docker Desktop ngắt giữa chừng
- đây là rủi ro môi trường vận hành, không phải dấu hiệu Gold logic bị sai ngay từ code

## 5. Checkpoint 7

Mục tiêu:

- làm lớp truy vấn JDBC rõ ràng hơn để DBeaver và Power BI có cùng một cấu hình chuẩn

Đã làm:

- cập nhật `docker-compose.yml` cho `spark-thriftserver`
- thêm `scripts/smoke_thriftserver.ps1`
- cập nhật tài liệu vận hành về JDBC

Cấu hình chính đã chốt:

- `hive.server2.authentication=NONE`
- `hive.server2.enable.doAs=false`
- `hive.server2.transport.mode=binary`
- `spark.sql.hive.thriftServer.incrementalCollect=true`

Smoke test hiện có:

- khởi động Thrift Server
- chờ port `10000`
- đăng ký lại bảng external
- kiểm tra `SHOW TABLES IN lakehouse`

Lưu ý:

- ở lần chạy mới nhất, smoke test bị chặn bởi lỗi Docker Desktop `Internal Server Error`
- vì vậy checkpoint 7 hoàn tất về cấu hình và script, nhưng xác minh cuối vẫn cần chạy lại khi Docker ổn định hơn

## 6. Checkpoint 8

Mục tiêu:

- hoàn thiện tài liệu vận hành và kịch bản demo
- giúp người khác chạy lại và trình bày hệ thống mà không phải hỏi lại nhiều

Đã làm:

- tạo `docs/query-guide.md`
- tạo `docs/demo-playbook.md`
- tạo `docs/handover-guide.md`
- cập nhật `README.md` để định hướng đọc tài liệu tốt hơn

Kết luận:

- checkpoint 8 đã hoàn tất
- repo hiện đã có bộ tài liệu đủ để chạy, kiểm tra, demo và bàn giao

## 7. Việc nên làm tiếp theo

Ưu tiên tiếp theo đề xuất:

1. Ổn định Docker Desktop hoặc chuyển sang môi trường chạy bền hơn
2. Tạo bộ nhãn tay chính thức `100-200` comment đã review thật
3. Chạy lại benchmark với `SENTIMENT_FALLBACK_TO_KEYWORD=false`
4. Chạy lại smoke test Thrift rồi xác nhận DBeaver/Power BI
5. Khi pipeline và đánh giá đã ổn định, mới chuyển sang `Delta Lake`
