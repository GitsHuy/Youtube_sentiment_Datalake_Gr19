# Report Checkpoint 5

Ngày cập nhật: `2026-04-13`

## 1. Mục tiêu checkpoint

Checkpoint 5 nâng phần sentiment từ mức demo rule-based lên mức có mô hình pretrained để pipeline thuyết phục hơn khi trình bày.

## 2. Những gì đã chỉnh sửa

Các file chính:

- `spark/jobs/silver_stream.py`
- `spark/Dockerfile`
- `.env.example`
- `docker-compose.yml`
- `scripts/evaluate_seed_labels.py`
- `docs/model-evaluation-guide.md`

Các thay đổi nổi bật:

- thay keyword baseline bằng transformer chạy trong `foreachBatch`
- giữ fallback keyword để pipeline không gãy cứng khi model lỗi
- ép predictor dùng PyTorch rõ ràng hơn với:
  - `framework="pt"`
  - `USE_TF=0`
  - `TRANSFORMERS_NO_TF=1`
- thêm script đánh giá model trên bộ seed labels cục bộ

## 3. Đã tải về và sử dụng những gì

Trong image Spark:

- `transformers`
- `sentencepiece`
- `torch` bản CPU
- `numpy<2`

Model sử dụng:

- `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual`

Ngoài ra đã dùng bộ dữ liệu đánh giá:

- `data/evaluation/assistant_seed_labels_100.csv`

Và sinh ra:

- `data/evaluation/model_vs_seed_labels_100.csv`
- `data/evaluation/model_vs_seed_labels_100_summary.json`

## 4. Kết quả đánh giá hiện tại

Kết quả từ script `python .\scripts\evaluate_seed_labels.py`:

- `total_rows = 100`
- `correct_rows = 59`
- `agreement_accuracy = 0.59`
- `macro_f1 = 0.5951`

Theo mức độ khó của mẫu:

- `review_needed=no`: `26/38`, accuracy `0.6842`
- `review_needed=yes`: `33/62`, accuracy `0.5323`

Chỉ số theo từng nhãn:

- `positive`: precision `0.6897`, recall `0.5556`, f1 `0.6154`
- `neutral`: precision `0.5000`, recall `0.6500`, f1 `0.5652`
- `negative`: precision `0.6842`, recall `0.5417`, f1 `0.6047`

## 5. Những gì kết quả này cho thấy

Điểm tốt:

- model chạy được ổn định ở local evaluation
- xử lý tương đối ổn với mẫu rõ nghĩa
- không còn là sentiment demo thuần từ khóa

Điểm còn yếu:

- dễ nhầm giữa `neutral` và `positive`
- greeting ngắn như `Hi`, `HI MRBeast` thường bị nghiêng sang `positive`
- câu hỏi hoặc góp ý trung tính đôi khi bị nghiêng sang `negative`
- comment slang, emoji-only, đa ngôn ngữ, mơ hồ vẫn khó

## 6. Checkpoint 5 giúp hệ thống tốt hơn như thế nào

- Silver đã có khả năng gán nhãn bằng model pretrained quốc tế
- Có script đánh giá độc lập để kiểm tra model ngoài pipeline streaming
- Có output CSV và JSON để tiện báo cáo học thuật hoặc review tay
- Đã giảm rủi ro lỗi thư viện bằng cách cố định hướng chạy PyTorch rõ ràng hơn

## 7. Những gì còn thiếu để checkpoint 5 thật sự mạnh

- Cần bộ nhãn tay cuối cùng `100-200` comment đã review thật, không chỉ seed labels ban đầu
- Khi benchmark nghiêm túc, cần đặt:

```env
SENTIMENT_FALLBACK_TO_KEYWORD=false
```

Lý do:

- nếu fallback còn bật, kết quả cuối có thể lẫn giữa transformer và baseline keyword
- khi đó accuracy không còn phản ánh riêng chất lượng model mới

## 8. Kết luận checkpoint

Checkpoint 5 được xem là hoàn tất về mặt tích hợp mô hình và đã có đánh giá bước đầu. Tuy nhiên, độ chính xác hiện tại mới ở mức trung bình khá, chưa đủ để khẳng định đây là cấu hình sentiment cuối cùng của dự án.
