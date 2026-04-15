# Hướng dẫn đánh giá model sentiment

Tài liệu này mô tả cách đánh giá model sentiment hiện tại sau checkpoint 10 và cách đọc đúng các file kết quả.

## 1. Bộ dữ liệu hiện có

### Seed labels

- `data/evaluation/assistant_seed_labels_100.csv`
- `data/evaluation/model_vs_seed_labels_100.csv`
- `data/evaluation/model_vs_seed_labels_100_summary.json`

### Manual labels

- `data/evaluation/manual_labels_100.csv`
- `data/evaluation/model_vs_manual_labels_100.csv`
- `data/evaluation/model_vs_manual_labels_100_summary.json`

### Keyword baseline trên manual labels

- `data/evaluation/keyword_vs_manual_labels_100.csv`
- `data/evaluation/keyword_vs_manual_labels_100_summary.json`

### Transformer với lexicon trên manual labels

- `data/evaluation/model_vs_manual_labels_100_with_lexicon.csv`
- `data/evaluation/model_vs_manual_labels_100_with_lexicon_summary.json`

## 2. Cách chạy đánh giá

### 2.1. Đánh giá trên seed labels

```powershell
python .\scripts\evaluate_seed_labels.py
```

### 2.2. Đánh giá transformer trên manual labels

```powershell
python .\scripts\evaluate_seed_labels.py `
  --input data/evaluation/manual_labels_100.csv `
  --label-column manual_label `
  --notes-column reviewer_notes `
  --mode transformer `
  --output data/evaluation/model_vs_manual_labels_100.csv `
  --summary data/evaluation/model_vs_manual_labels_100_summary.json
```

### 2.3. Đánh giá keyword baseline trên manual labels

```powershell
python .\scripts\evaluate_seed_labels.py `
  --input data/evaluation/manual_labels_100.csv `
  --label-column manual_label `
  --notes-column reviewer_notes `
  --mode keyword `
  --output data/evaluation/keyword_vs_manual_labels_100.csv `
  --summary data/evaluation/keyword_vs_manual_labels_100_summary.json
```

### 2.4. Đánh giá transformer với slang lexicon

```powershell
python .\scripts\evaluate_seed_labels.py `
  --input data/evaluation/manual_labels_100.csv `
  --label-column manual_label `
  --notes-column reviewer_notes `
  --mode transformer `
  --slang-lexicon spark/jobs/slang_sentiment_lexicon.json `
  --output data/evaluation/model_vs_manual_labels_100_with_lexicon.csv `
  --summary data/evaluation/model_vs_manual_labels_100_with_lexicon_summary.json
```

## 3. Kết quả hiện tại

### 3.1. Transformer so với manual labels, chưa dùng lexicon

- `agreement_accuracy = 0.65`
- `macro_f1 = 0.6476`

### 3.2. Keyword baseline so với manual labels

- `agreement_accuracy = 0.31`
- `macro_f1 = 0.2599`

### 3.3. Transformer với lexicon và xử lý emoji/sticker

- `agreement_accuracy = 0.83`
- `macro_f1 = 0.8163`
- `mismatch_count = 17`

So với transformer chưa dùng lexicon:

- accuracy tăng từ `0.65` lên `0.83`
- macro F1 tăng từ `0.6476` lên `0.8163`

## 4. Vì sao kết quả tăng mạnh

Không phải chỉ vì thêm vài từ Gen Z.

Lý do lớn nhất là phần chuẩn hóa hiện đã xử lý được cả:

- emoji thật như `❤`, `😊`, `😭`
- emoji ở dạng chuỗi escape như `\u2764`, `\U0001f60a`, `\U0001f62d`

Điều này đặc biệt hữu ích cho:

- greeting with heart
- emoji only
- excited reaction
- request with sadness
- supportive comment ngắn

Ngoài ra, hệ thống hiện cũng chuẩn hóa các từ bị kéo dài như:

- `niceeeeeeeee`
- `omgggg`
- `crazyyyy`

theo hướng giữ từ gốc và bổ sung thêm dạng chuẩn hóa. Cách này tốt hơn việc thêm vô hạn biến thể thủ công vào lexicon.

## 5. Cách hiểu đúng kết quả

### Với seed labels

Đây chỉ là so sánh với `assistant_seed_label`, chưa phải ground truth cuối cùng.

### Với manual labels

Đây là bộ tham chiếu tốt hơn cho dự án hiện tại vì:

- cùng một cheat sheet gán nhãn
- bám đúng video mục tiêu
- đủ tốt để benchmark kỹ thuật và so sánh các bản cải tiến

Tuy vậy, manual labels vẫn là bộ nhãn nội bộ của nhóm, không phải bộ chuẩn học thuật tuyệt đối.

## 6. Những nhóm còn khó

Cả sau khi tăng lên `0.83`, model vẫn còn dễ sai ở:

- câu hỏi trung tính nhưng có cảm xúc nhẹ
- request trung tính
- câu mơ hồ, sai chính tả, đa ngôn ngữ
- câu mang tính châm biếm hoặc mocking

## 7. Liên hệ với runtime Silver

Lexicon và logic chuẩn hóa hiện không chỉ dùng cho benchmark, mà còn đã được nối vào:

- `spark/jobs/silver_stream.py`

Nghĩa là các cải tiến đã đo được trong benchmark có thể áp dụng lại cho pipeline thật.
