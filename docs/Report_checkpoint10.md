# Report Checkpoint 10

Ngày cập nhật: `2026-04-15`

## 1. Mục tiêu checkpoint

Checkpoint 10 tương ứng với checkpoint 2 trong kế hoạch `docs/upgradepart2_checkpoint.md`.

Mục tiêu:

- tạo bộ nhãn tay 100 comment cho đúng video mục tiêu
- benchmark lại model sentiment hiện tại trên bộ nhãn tay đó
- so sánh transformer với keyword baseline
- thử cải thiện thêm bằng slang lexicon và xử lý emoji/sticker

## 2. Những gì đã thực hiện

Các file chính đã dùng hoặc cập nhật:

- `data/evaluation/manual_labels_100.csv`
- `data/evaluation/manual_labeling_cheatsheet.md`
- `scripts/evaluate_seed_labels.py`
- `spark/jobs/slang_sentiment_lexicon.json`
- `spark/jobs/silver_stream.py`
- `docs/model-evaluation-guide.md`

Các file kết quả tạo mới hoặc cập nhật:

- `data/evaluation/model_vs_manual_labels_100.csv`
- `data/evaluation/model_vs_manual_labels_100_summary.json`
- `data/evaluation/keyword_vs_manual_labels_100.csv`
- `data/evaluation/keyword_vs_manual_labels_100_summary.json`
- `data/evaluation/model_vs_manual_labels_100_with_lexicon.csv`
- `data/evaluation/model_vs_manual_labels_100_with_lexicon_summary.json`

## 3. Cải tiến kỹ thuật trong checkpoint này

### 3.1. Bộ nhãn tay 100 comment

Đã chốt file:

- `data/evaluation/manual_labels_100.csv`

File này dùng nhãn:

- `positive`
- `neutral`
- `negative`

và có cột ghi chú để gom các ca khó như:

- greeting
- question
- supportive
- complaint
- request with sadness
- unclear foreign language
- slang / Gen Z

### 3.2. Script benchmark linh hoạt hơn

`scripts/evaluate_seed_labels.py` đã được mở rộng để:

- đọc được nhiều file nhãn khác nhau
- chọn cột nhãn bằng `--label-column`
- chọn cột ghi chú bằng `--notes-column`
- chạy được cả `transformer` và `keyword`
- nhận `--slang-lexicon` để benchmark cùng một logic chuẩn hóa với runtime

### 3.3. Lexicon cho slang và emoji

Đã tạo và mở rộng:

- `spark/jobs/slang_sentiment_lexicon.json`

Lexicon hiện gồm:

- slang kiểu `W`, `L`, `goat`, `mid`, `ragebait`
- reaction ngắn như `omg`, `no way`
- emoji/sticker như tim, cười, khóc, buồn, sốc
- một số cụm comment ngắn có ích như `justice for`, `0 like`, `niceeeee`

### 3.4. Xử lý được emoji ở dạng escape

Đây là cải tiến quan trọng nhất ở cuối checkpoint này.

Trước đó, nhiều comment trong bộ đánh giá lưu emoji ở dạng chuỗi escape như:

- `\\u2764`
- `\\U0001f60a`

Trong khi lexicon lại khớp theo emoji thật như:

- `❤`
- `😊`

Vì vậy, nhiều mapping đúng về ý tưởng nhưng không được áp dụng.

Đã sửa:

- `scripts/evaluate_seed_labels.py`
- `spark/jobs/silver_stream.py`

để giải mã các token escape Unicode trước khi áp dụng lexicon.

Ý nghĩa:

- benchmark offline và runtime Silver cùng đọc được cả emoji thật lẫn emoji ở dạng escape
- giúp tăng chất lượng dự đoán ở nhóm comment ngắn, greeting with heart, emoji only, reaction ngắn

### 3.5. Chuẩn hóa chữ bị kéo dài

Đã bổ sung thêm bước chuẩn hóa cho các từ kiểu:

- `niceeeee`
- `omgggg`
- `soooo`
- `crazyyyy`

Theo hướng:

- không xóa hẳn từ gốc
- giữ lại từ gốc để không làm mất sắc thái cảm xúc
- đồng thời thêm dạng chuẩn hóa để model và lexicon hiểu tốt hơn

Ví dụ:

- `niceeeeeeeee` -> giữ `niceeeeeeeee` và bổ sung thêm `nice`
- `Ishowspeeddd` -> giữ `ishowspeeddd` và bổ sung thêm `ishowspeed`

Ý nghĩa:

- tránh phải thêm vô hạn biến thể vào `slang_sentiment_lexicon.json`
- bền hơn với comment mạng xã hội thực tế
- tránh regression kiểu chuẩn hóa quá mạnh làm mất tín hiệu excited reaction

## 4. Kết quả benchmark

### 4.1. Transformer trên manual labels, chưa dùng lexicon

Model:

- `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual`

Kết quả:

- `agreement_accuracy = 0.65`
- `macro_f1 = 0.6476`

### 4.2. Keyword baseline trên manual labels

Kết quả:

- `agreement_accuracy = 0.31`
- `macro_f1 = 0.2599`

Nhận xét:

- keyword baseline yếu rõ rệt
- không đủ tốt cho comment ngắn, đa ngôn ngữ, slang và emoji

### 4.3. Transformer với lexicon, trước khi xử lý escape

Kết quả:

- `agreement_accuracy = 0.67`
- `macro_f1 = 0.6644`

So với chưa có lexicon:

- accuracy tăng từ `0.65` lên `0.67`
- macro F1 tăng từ `0.6476` lên `0.6644`

### 4.4. Transformer với lexicon, sau khi xử lý escape + bổ sung sticker/slang

Kết quả mới nhất:

- `agreement_accuracy = 0.83`
- `macro_f1 = 0.8163`
- `mismatch_count = 17`

So với bản có lexicon trước đó:

- accuracy tăng từ `0.67` lên `0.83`
- macro F1 tăng từ `0.6644` lên `0.8163`
- mismatch giảm từ `33` xuống `17`

Theo từng nhãn:

- `positive`: precision `0.8667`, recall `0.9750`, f1 `0.9176`
- `neutral`: precision `0.8889`, recall `0.6667`, f1 `0.7619`
- `negative`: precision `0.7143`, recall `0.8333`, f1 `0.7692`

Các nhóm được cải thiện rõ:

- `greeting with heart`
- `emoji only`
- `supportive`
- `complaint`
- `excited reaction`
- `request with sadness`

Ví dụ những ca đã được sửa đúng:

- `W`
- `Hi❤❤`
- `Payal gaming ❤`
- `Today is my birthday but 0 like 😢`
- `No way 😮😮😮 impossible`

## 5. Các mismatch còn lại

Sau cải tiến, các nhóm còn khó chủ yếu là:

- câu hỏi nhưng không mang cực tính rõ
- request trung tính nhưng model đọc thành tích cực hoặc tiêu cực
- câu mơ hồ / sai chính tả / đa ngôn ngữ
- câu châm biếm, mỉa mai, mocking

Một vài ví dụ còn lệch:

- `Who noticed payal gaming ❤`
- `i wanted speed to compete`
- `bro where tf is cory?`
- `why is mister beast crawling like that 😭`

## 6. Kết luận checkpoint

Checkpoint 10 được xem là hoàn thành tốt.

Kết luận chính:

- transformer vẫn tốt hơn keyword baseline rất rõ
- slang lexicon là hướng đúng
- xử lý emoji escape là thay đổi mang lại tác động lớn nhất ở nhịp cải thiện này
- model hiện tại đã mạnh hơn đáng kể cho demo kỹ thuật và đánh giá nội bộ
- phần còn lại chủ yếu là bài toán policy gán nhãn và các ca mơ hồ, không còn là lỗi dễ sửa bằng vài keyword đơn lẻ

## 7. Gợi ý bước tiếp theo

- nếu muốn tăng tiếp độ chính xác, nên ưu tiên chuẩn hóa policy gán nhãn cho các câu hỏi có heart, request, suggestion và mocking
- nếu muốn tập trung vận hành hệ thống, có thể xem checkpoint 10 là đủ tốt để chuyển sang smoke test, metadata và Delta Lake ở checkpoint sau
