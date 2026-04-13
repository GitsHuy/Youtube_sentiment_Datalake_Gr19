# Report Checkpoint 8

Ngày cập nhật: `2026-04-13`

## 1. Mục tiêu checkpoint

Checkpoint 8 tập trung hoàn thiện phần tài liệu và kịch bản demo, để repo đủ rõ ràng cho:

- chạy lại hệ thống
- kiểm tra dữ liệu
- demo trước giảng viên
- bàn giao cho người khác đọc lại

## 2. Những gì đã thực hiện

Các tài liệu được bổ sung hoặc chuẩn hóa:

- `docs/query-guide.md`
- `docs/demo-playbook.md`
- `docs/handover-guide.md`
- `docs/run-system.md`
- `docs/implementation-checkpoints.md`

## 3. Nội dung chính của checkpoint 8

### Hoàn thiện bộ truy vấn kiểm tra

Đã gom toàn bộ các câu truy vấn kiểm tra hệ thống vào:

- `docs/query-guide.md`

Tài liệu này bao phủ:

- kiểm tra tổng quan bảng
- kiểm tra Bronze
- kiểm tra Silver
- kiểm tra Gold summary
- kiểm tra Gold breakdown
- truy vấn đối chiếu giữa các lớp
- bộ truy vấn demo ngắn gọn 1 mạch

### Hoàn thiện kịch bản demo

Đã tạo:

- `docs/demo-playbook.md`

Tài liệu này giúp demo theo đúng luồng:

- giới thiệu kiến trúc
- chứng minh ingestion
- chứng minh Silver có sentiment
- chứng minh Gold có KPI
- kết luận hệ thống end-to-end

### Hoàn thiện tài liệu bàn giao

Đã tạo:

- `docs/handover-guide.md`

Tài liệu này trả lời nhanh:

- người mới nên đọc gì trước
- nếu muốn chạy thì đọc file nào
- nếu muốn demo thì mở file nào
- nếu muốn xem tiến độ thì xem report nào

## 4. Checkpoint 8 giúp hệ thống tốt hơn như thế nào

- Repo bớt phụ thuộc vào trí nhớ người vận hành
- Khi demo không cần nghĩ lại nên query câu nào
- Người đọc mới có đường dẫn đọc tài liệu rõ ràng hơn
- Dễ bàn giao hơn cho thành viên nhóm hoặc giảng viên xem lại

## 5. Kết luận checkpoint

Checkpoint 8 được xem là hoàn tất. Sau checkpoint này, repo đã có đủ:

- tài liệu vận hành
- tài liệu kiểm tra truy vấn
- tài liệu đánh giá model
- kịch bản demo
- hướng dẫn bàn giao nhanh

Phần còn lại hợp lý nhất về sau là checkpoint 9 nếu nhóm quyết định chuyển từ Parquet sang Delta Lake.
