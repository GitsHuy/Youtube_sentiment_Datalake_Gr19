# Hướng dẫn đánh giá model sentiment

Tài liệu này mô tả cách đánh giá model sentiment đang dùng ở checkpoint 5.

## 1. Bộ dữ liệu hiện có

Seed labels hiện tại:

- `data/evaluation/assistant_seed_labels_100.csv`

Kết quả model sau khi chạy script:

- `data/evaluation/model_vs_seed_labels_100.csv`
- `data/evaluation/model_vs_seed_labels_100_summary.json`

## 2. Cách chạy đánh giá

```powershell
python .\scripts\evaluate_seed_labels.py
```

Script sẽ:

- đọc file seed labels
- chạy model `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual`
- sinh file CSV chi tiết từng comment
- sinh file JSON tóm tắt accuracy, confusion matrix, precision, recall, f1

## 3. Kết quả hiện tại

Kết quả từ lần chạy mới nhất:

- `agreement_accuracy = 0.59`
- `macro_f1 = 0.5951`

Theo từng nhãn:

- `positive`: precision `0.6897`, recall `0.5556`, f1 `0.6154`
- `neutral`: precision `0.5000`, recall `0.6500`, f1 `0.5652`
- `negative`: precision `0.6842`, recall `0.5417`, f1 `0.6047`

## 4. Cách hiểu đúng kết quả

Đây là kết quả so với `assistant_seed_label`, chưa phải ground truth cuối cùng của đồ án.

Vì vậy:

- nó đủ để biết model đang mạnh ở đâu, yếu ở đâu
- nhưng chưa đủ để kết luận học thuật cuối cùng

## 5. Quy tắc benchmark tiếp theo

Khi benchmark nghiêm túc trên bộ nhãn tay cuối cùng, nên tắt fallback:

```env
SENTIMENT_FALLBACK_TO_KEYWORD=false
```

Nếu không, kết quả đánh giá có thể bị lẫn giữa transformer và keyword baseline.

## 6. Bước hợp lý tiếp theo

1. Tạo bộ nhãn tay `100-200` comment đã review thật
2. Chạy lại `scripts/evaluate_seed_labels.py` hoặc script tương đương trên bộ nhãn đó
3. So sánh với model khác nếu muốn nâng checkpoint tiếp theo
