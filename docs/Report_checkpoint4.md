# Report Checkpoint 4

Ngày cập nhật: `2026-04-13`

## 1. Mục tiêu checkpoint

Checkpoint 4 tập trung đưa `Bronze` và `Silver` từ mức “chạy được pipeline” lên mức “có kiểm soát chất lượng dữ liệu”. Trọng tâm của checkpoint này là:

- siết điều kiện parse ở `Bronze`
- làm sạch và chuẩn hóa dữ liệu tốt hơn ở `Silver`
- bổ sung chỉ số kiểm tra chất lượng dữ liệu
- xác nhận `Gold` vẫn chạy được sau khi `Silver` đổi schema

## 2. Những gì đã làm

- Cập nhật `spark/jobs/bronze_stream.py` để chỉ ghi các record parse JSON thành công.
- Cập nhật `spark/jobs/silver_stream.py` để:
  - chuẩn hóa blank string thành `null` hoặc giá trị mặc định hợp lý
  - chuẩn hóa `author`, `lang`, `source`
  - ép `like_count`, `reply_count` không âm
  - ép `collected_at >= event_time`
  - loại các record reply nhưng thiếu `parent_comment_id`
  - làm sạch `text_clean` mạnh hơn bằng cách bỏ URL, tab, xuống dòng và khoảng trắng thừa
  - thêm `text_length`
  - thêm `collected_delay_seconds`
  - deduplicate theo `video_id + comment_id`
- Tạo file `spark/sql/checkpoint4_quality_checks.sql`.
- Cập nhật tài liệu trong `docs/interfaces.md` và `docs/run-system.md`.
- Reset có kiểm soát state/output của `Silver` và `Gold`, giữ nguyên `Bronze`.
- Sửa lỗi tương thích Python trong container Spark:
  - thay `str | None` bằng `Optional[str]`

## 3. Kết quả đạt được

- `spark-silver` chạy lại thành công với schema mới.
- `spark-gold` sinh được snapshot mới sau khi `Silver` thay đổi schema.
- Truy vấn chất lượng dữ liệu cho kết quả:
  - `bronze_rows = 9489`
  - `silver_rows = 674`
  - `gold_rows = 15`
  - `duplicate_comment_rows = 0`
  - `null_comment_id_rows = 0`
  - `null_video_id_rows = 0`
  - `empty_text_clean_rows = 0`
  - `invalid_reply_rows = 0`
  - `negative_delay_rows = 0`
- Truy vấn trực tiếp Silver xác nhận hai cột mới đã có dữ liệu:
  - `text_length`
  - `collected_delay_seconds`

## 4. Vấn đề phát hiện trong checkpoint

- Container Spark đang dùng phiên bản Python cũ hơn môi trường local, nên cú pháp type hint `str | None` làm `spark-silver` crash lúc khởi động.
- `gold_stream.py` phụ thuộc vào việc đường dẫn Silver đã có file thật trước khi Gold đọc schema.
- Dữ liệu `Bronze` hiện còn giữ dữ liệu cũ từ các lần demo trước, nên kết quả Silver vẫn lẫn một số `video_id` lịch sử như:
  - `v001`
  - `v002`
  - `v003`

## 5. Đã cải thiện gì sau checkpoint

- Bronze bớt nguy cơ ghi record rác do parse lỗi.
- Silver sạch hơn, chặt hơn và có thể đo được chất lượng thay vì chỉ “lọc sơ rồi ghi”.
- Hệ thống hiện có bộ truy vấn kiểm tra chất lượng dữ liệu riêng cho checkpoint 4.
- Gold vẫn tương thích sau khi Silver thay đổi schema, chứng tỏ pipeline không bị gãy ở tầng downstream.

## 6. Cần cải thiện tiếp

- Chưa tách hẳn dữ liệu lịch sử khỏi dữ liệu kiểm thử mới, nên bài toán “1 video YouTube” chưa sạch 100% nếu nhìn toàn bộ Bronze hiện tại.
- `gold_stream.py` vẫn phụ thuộc vào việc Silver đã có file trước khi khởi động.
- Chưa có cơ chế chính thức để reset có chọn lọc theo checkpoint hoặc theo bài test.
- Sentiment vẫn đang là baseline rule-based, chưa sang mô hình nâng cao.

## 7. Kết luận checkpoint

Checkpoint 4 được xem là hoàn tất vì hệ thống đã nâng rõ chất lượng xử lý dữ liệu ở `Bronze` và `Silver`, đồng thời giữ được luồng chạy tới `Gold`. Tồn đọng lớn nhất sau checkpoint này không còn là lỗi làm sạch dữ liệu, mà là việc cần cô lập dữ liệu kiểm thử tốt hơn và tiếp tục nâng cấp phần mô hình ở checkpoint sau.
