# Report Checkpoint 9

Ngày cập nhật: `2026-04-15`

## 1. Mục tiêu checkpoint

Checkpoint 9 tương ứng với checkpoint 1 của kế hoạch `upgradepart2_checkpoint.md`.

Mục tiêu của checkpoint này là:

- nâng `producer.py` từ kiểu chạy one-shot sang polling liên tục
- giảm gửi trùng comment khi polling nhiều vòng
- làm log ingestion rõ hơn để dễ debug và demo

## 2. Những gì đã chỉnh sửa

Các file đã được cập nhật:

- `.env.example`
- `docker-compose.yml`
- `docs/run-system.md`
- `producer/producer.py`

### 2.1. Nâng producer sang polling liên tục

Trong `producer/producer.py`, phần `youtube_api` mode đã được đổi từ:

- gọi API 1 lần
- gửi dữ liệu vào Kafka
- kết thúc

sang cơ chế:

- gọi API theo từng vòng polling
- ngủ theo `YOUTUBE_POLL_INTERVAL_SECONDS`
- tiếp tục chạy vòng kế tiếp nếu `YOUTUBE_CONTINUOUS_MODE=true`

### 2.2. Thêm chống trùng trong phạm vi phiên chạy

Đã bổ sung bộ nhớ đệm `RecentCommentCache` để giữ các `comment_id` đã gửi gần đây.

Ý nghĩa:

- nếu vòng polling sau lấy lại đúng các comment cũ
- producer sẽ nhận ra comment đã xuất hiện trong cache
- bỏ qua trước khi gửi vào Kafka

Biến cấu hình mới:

- `YOUTUBE_DEDUP_CACHE_SIZE`

### 2.3. Làm log rõ hơn

Producer hiện log rõ theo từng vòng:

- `video_id` đang chạy
- số record lấy được
- số page API đã đọc
- số record trùng bị bỏ qua
- số record mới đã gửi vào Kafka
- thời gian ngủ trước vòng kế tiếp

### 2.4. Cập nhật cấu hình và tài liệu

Đã bổ sung vào `.env.example` và `docker-compose.yml` các biến:

- `YOUTUBE_CONTINUOUS_MODE`
- `YOUTUBE_POLL_INTERVAL_SECONDS`
- `YOUTUBE_DEDUP_CACHE_SIZE`

Đã cập nhật `docs/run-system.md` để hướng dẫn:

- bật polling mode
- hiểu ý nghĩa từng biến mới
- đọc log producer sau mỗi vòng polling

## 3. Kết quả kiểm chứng

### 3.1. Kiểm tra cú pháp

Đã chạy:

```powershell
python -m py_compile producer/producer.py
```

Kết quả:

- không có lỗi cú pháp

### 3.2. Kiểm tra chạy thực tế

Đã chạy producer với cấu hình test tạm thời:

- `YOUTUBE_CONTINUOUS_MODE=true`
- `YOUTUBE_POLL_INTERVAL_SECONDS=15`

Log thực tế xác nhận:

- vòng 1 lấy được `219` record và gửi vào Kafka
- vòng 2 tiếp tục polling, nhận lại `219` record nhưng bỏ qua toàn bộ vì trùng
- vòng 3 và vòng 4 tiếp tục polling và tiếp tục bỏ qua record trùng

Điều này chứng minh được:

- producer không còn one-shot
- producer đã chạy liên tục qua nhiều vòng
- chống trùng trong phạm vi phiên chạy đã hoạt động đúng

## 4. Những gì checkpoint này giúp hệ thống tốt hơn

- ingestion nhìn đúng tinh thần streaming hơn
- giảm nguy cơ bơm lặp comment cũ vào Kafka khi polling liên tục
- dễ giải thích kiến trúc hơn khi demo
- dễ debug producer hơn nhiều nhờ log rõ từng vòng chạy

## 5. Hạn chế còn lại

- chống trùng hiện tại mới ở mức trong phạm vi phiên chạy producer
- nếu container producer bị recreate hoàn toàn thì bộ nhớ cache sẽ mất
- về sau nếu cần ổn định hơn nữa có thể cân nhắc watermark hoặc state bền hơn

## 6. Lưu ý môi trường khi kiểm chứng

Trong quá trình kiểm chứng, Docker Desktop vẫn xuất hiện lại lỗi:

- `Internal Server Error` từ Docker API

Ảnh hưởng:

- một số lệnh quản trị như `docker compose exec`, `docker compose logs`, `docker compose stop` có lúc bị gián đoạn
- việc kiểm tra sâu thêm ở tầng `spark-sql` sau khi producer chạy bị môi trường Docker gây nhiễu

Kết luận kỹ thuật:

- lỗi quan sát được là lỗi môi trường Docker Desktop
- không phải dấu hiệu cho thấy logic mới của `producer.py` bị sai

## 7. Kết luận checkpoint

Checkpoint 9 được xem là hoàn thành phần cốt lõi.

Những gì đã đạt:

- producer chạy polling liên tục
- có cơ chế giảm trùng cơ bản
- có biến môi trường điều khiển rõ ràng
- có log dễ đọc
- có tài liệu vận hành cập nhật

Bước hợp lý tiếp theo:

- sang checkpoint 10 để đánh giá lại sentiment model bằng bộ nhãn tay tốt hơn
