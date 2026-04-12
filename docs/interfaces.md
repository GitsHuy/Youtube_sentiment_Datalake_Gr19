# Interfaces

Tai lieu nay khoa cac diem giao tiep dung chung de A, B, C co the lam song song ma khong va nhau.

## 1. Muc tieu chung

Luong nghiep vu nhom dang nham toi:

- lay binh luan tu dung 1 video YouTube thong qua `videoId`
- day binh luan vao Kafka
- luu qua Bronze, Silver, Gold
- dang ky metadata qua Hive Metastore
- mo du lieu Gold cho SQL va Power BI

Baseline hien tai van giu `data/sample_comments.jsonl` lam nguon fallback de moi thanh vien test doc lap.

## 2. Hang so dung chung

Kafka topic:

- `youtube-comments`

Duong dan HDFS:

- Bronze: `hdfs://namenode:8020/lake/bronze/youtube_comments`
- Silver: `hdfs://namenode:8020/lake/silver/youtube_comments`
- Gold: `hdfs://namenode:8020/lake/gold/youtube_comment_metrics`

Database va bang Hive:

- database: `lakehouse`
- bang Bronze: `lakehouse.bronze_youtube_comments`
- bang Silver: `lakehouse.silver_youtube_comments`
- bang Gold: `lakehouse.gold_youtube_comment_metrics`

Nhung ten nay phai giu on dinh neu chu chua cho phep doi.

## 3. Schema Kafka hien tai

Day la schema ma job Bronze hien tai da ho tro.

| Field | Type | Bat buoc | Ghi chu |
| --- | --- | --- | --- |
| `event_time` | timestamp string | co | Spark dang parse ve timestamp |
| `comment_id` | string | co | id duy nhat cua binh luan |
| `video_id` | string | co | id video dang theo doi |
| `author` | string | co | ten tac gia binh luan |
| `text` | string | co | noi dung goc |
| `like_count` | integer | co | so luot like |
| `reply_count` | integer | co | co the bang `0` neu la reply |
| `is_reply` | boolean | co | `false` neu la top-level, `true` neu la reply |
| `lang` | string | khong | neu thieu thi dua ve `unknown` |

Nguoi A phai giu toi thieu schema nay de Bronze khong vo.

## 4. Schema ingestion mo rong de xet o buoc sau

Nhung field duoi day nen them o vong sau khi A va B thong nhat:

| Field | Type | Bat buoc | Nguoi lien quan | Ghi chu |
| --- | --- | --- | --- | --- |
| `parent_comment_id` | string | khong | A + B | de truy vet reply |
| `source` | string | co | A | goi y `youtube_api` hoac `sample_file` |
| `collected_at` | timestamp string | co | A | thoi diem collector lay du lieu |

Quy tac:

- A khong tu y them field vao luong chinh ma khong bao B, vi Bronze schema se phai doi theo

## 5. Hop dong Bronze

Bronze hien tai ghi ra:

- cac field Kafka da parse o schema baseline
- `ingested_at`

Bronze phai giu dung vai tro:

- gan nguon nhat co the
- xu ly nhe
- phu hop de reprocess sau nay

Bronze khong nen bien thanh tang cleaning hay tang model.

## 6. Hop dong Silver

Cot toi thieu cua Silver hien tai:

| Column | Y nghia |
| --- | --- |
| `event_time` | thoi gian su kien goc |
| `comment_id` | id binh luan |
| `video_id` | id video |
| `author` | ten tac gia |
| `text` | noi dung goc |
| `text_clean` | text da lam sach |
| `like_count` | like da chuan hoa |
| `reply_count` | reply da chuan hoa |
| `is_reply` | co phai reply hay khong |
| `lang` | ngon ngu da chuan hoa |
| `ingested_at` | thoi diem vao Bronze |
| `silver_processed_at` | thoi diem xu ly Silver |
| `positive_score` | diem tich cuc baseline |
| `negative_score` | diem tieu cuc baseline |
| `sentiment` | nhan cam xuc cuoi cung |

Trang thai hien tai cua Silver:

- da lam sach text
- da normalize null
- da dedup theo `comment_id`

Nguoi B co the mo rong Silver, nhung nen giu nhung cot toi thieu nay on dinh de Gold va lop SQL cua C khong bi gay.

## 7. Hop dong Gold

Cot toi thieu cua Gold hien tai:

| Column | Y nghia |
| --- | --- |
| `event_date` | ngay suy ra tu `event_time` |
| `video_id` | id video |
| `sentiment` | nhom cam xuc |
| `comment_count` | so binh luan trong nhom |
| `avg_likes` | like trung binh |
| `avg_replies` | reply trung binh |
| `reply_comment_count` | so binh luan la reply |

Nguoi C nen build SQL validation va dashboard tren bo toi thieu nay truoc.

Nguoi B co the them metric moi o Gold, nhung can giu bo cot baseline de C khong phai sua lai toan bo.

## 8. Quy tac so huu

- A so huu mapping du lieu tu YouTube API sang schema Kafka
- B so huu Bronze, Silver, Gold va logic model
- C so huu Metastore, dang ky bang, Thrift/JDBC va Power BI
- chu so huu `docker-compose.yml`, `.env.example`, `README.md` va tai lieu interface nay

## 9. Quy tac de lam song song

De khong cho nhau:

- A lam theo schema Kafka toi thieu o tren
- B dung `data/sample_comments.jsonl` de phat trien tiep trong khi cho A
- C lam theo schema Gold toi thieu trong khi B cai tien model
