# Ke Hoach Nang Cap Giai Doan 2

Tai lieu nay chot lo trinh nang cap tiep theo cua he thong sau checkpoint 8. Muc tieu cua giai doan 2 la nang he thong tu muc demo end-to-end dang chay duoc len muc van hanh on dinh hon, kiem chung duoc hon, va tien gan hon toi kien truc lakehouse hoan chinh.

Huong uu tien da chot:

1. Ingestion
2. Sentiment model
3. Van hanh: smoke test, quality check, metadata
4. Delta Lake
5. Tong kiem tra va chot tai lieu

Ghi chu:

- Tam thoi chua uu tien mo rong them Gold/dashboard vi hien tai Gold da du dung cho demo.
- Script reset du lieu 1 video khong phai uu tien gan, vi nhom dang giu nguyen `video_id`.
- Moi checkpoint deu phai co buoc kiem tra pass/fail truoc khi sang checkpoint tiep.

## Checkpoint 1: Nang cap ingestion tu one-shot sang polling lien tuc

Muc tieu:

- Bien `producer.py` thanh ingestion co tinh chat streaming hon.
- Ho tro lay comment theo chu ky thay vi chay 1 lan roi dung.
- Giam du lieu trung lap ngay tu dau vao.

Pham vi thuc hien:

- `producer/producer.py`
- `producer/requirements.txt` neu can
- `.env.example`
- `docs/run-system.md` neu can bo sung bien moi truong

Cong viec chi tiet:

- Them che do `YOUTUBE_CONTINUOUS_MODE=true|false`
- Them bien `YOUTUBE_POLL_INTERVAL_SECONDS`
- Them co che nho `comment_id` da gui gan day hoac moc thoi gian da lay
- Bo qua comment trung truoc khi gui vao Kafka
- Ghi log ro moi vong polling:
  - video dang chay
  - so record lay duoc
  - so record gui vao Kafka
  - so record bi bo qua vi trung

Kiem tra cuoi checkpoint:

- Chay producer trong che do lien tuc it nhat 2-3 vong polling
- Xac nhan producer khong tu thoat sau 1 lan lay du lieu
- Xac nhan Kafka tiep tuc nhan ban ghi moi theo chu ky
- Xac nhan khong co dau hieu ban ghi trung tang bat thuong o Bronze

Dieu kien pass:

- Producer chay polling on dinh
- Co log ro rang
- Co co che giam trung co ban

Neu fail thi uu tien sua ngay:

- producer dung som
- producer gui lap lai qua nhieu comment cu
- bien moi truong moi chua duoc tai lieu hoa

## Checkpoint 2: Danh gia lai sentiment model bang bo nhan tay tot hon

Muc tieu:

- Kiem chung lai do tin cay cua model sentiment hien tai.
- Tach bach ket qua model that voi truong hop duoc fallback ho tro.

Pham vi thuc hien:

- `data/evaluation/`
- `scripts/evaluate_seed_labels.py`
- `docs/model-evaluation-guide.md`
- `docs/Report_checkpoint...` cua giai doan moi neu can

Cong viec chi tiet:

- Tao bo nhan tay `100-200` comment tu dung video muc tieu
- Ra soat lai cac nhan:
  - positive
  - neutral
  - negative
- Chay danh gia voi cau hinh hien tai
- Chay them voi `SENTIMENT_FALLBACK_TO_KEYWORD=false`
- So sanh:
  - accuracy
  - macro F1
  - nhom comment de
  - nhom comment kho

Kiem tra cuoi checkpoint:

- Co file du lieu nhan tay ro rang
- Co file ket qua danh gia
- Co ket luan ngan:
  - model du dung hay chua
  - fallback dang giup that hay dang lam dep ket qua

Dieu kien pass:

- Co benchmark ro rang tren bo nhan tay
- Biet duoc muc do tin cay hien tai cua model

Neu fail thi uu tien sua ngay:

- bo nhan tay chua dong nhat
- script danh gia chua phan biet duoc che do fallback
- ket qua chua du ro de ra quyet dinh

## Checkpoint 3: Cuong hoa van hanh bang smoke test, quality check va metadata

Muc tieu:

- Giam rui ro "he thong co chay nhung khong biet du lieu co dung khong".
- Chuan hoa cach kiem tra sau moi lan thay doi ingestion hoac model.

Pham vi thuc hien:

- `scripts/`
- `spark/sql/checkpoint4_quality_checks.sql`
- `spark/sql/checkpoint6_gold_quality_checks.sql`
- `spark/sql/register_tables.sql`
- `docs/run-system.md`
- `docs/query-guide.md`

Cong viec chi tiet:

- Gom thanh 2 nhom kiem tra:
  - smoke test van hanh
  - quality check du lieu
- Smoke test nen kiem tra:
  - container chinh da len
  - port `10000` cua thrift da mo
  - `SHOW TABLES IN lakehouse` chay duoc
- Quality check nen kiem tra:
  - Bronze/Silver/Gold co du lieu
  - so `video_id` co hop ly
  - co trung `comment_id` hay khong
  - Silver co du cot sentiment
  - Gold co sinh du 2 bang chinh
- Chuan hoa note khi doi schema streaming:
  - luc nao can reset checkpoint
  - luc nao chi can register lai table
- Bo sung huong dan metadata/query de khi truy van bi lech schema thi xu ly nhanh hon

Kiem tra cuoi checkpoint:

- Chay duoc 1 lan smoke test
- Chay duoc 1 lan quality check
- Co ket qua PASS/FAIL de doc nhanh

Dieu kien pass:

- Sau moi lan nang cap co the kiem tra suc khoe he thong nhanh
- Co cach doc ra loi van hanh va loi du lieu tach biet nhau

Neu fail thi uu tien sua ngay:

- Thrift len khong on dinh
- bang dang ky khong khop schema du lieu
- query kiem tra qua phu thuoc vao thao tac thu cong

## Checkpoint 4: Chuyen Bronze, Silver, Gold tu Parquet sang Delta Lake

Muc tieu:

- Nang cap kien truc de he thong tien gan hon toi data lakehouse dung nghia.
- Giu nguyen luong xu ly nghiep vu, chi doi table format va van hanh lien quan.

Pham vi thuc hien:

- `spark/Dockerfile`
- `spark/jobs/bronze_stream.py`
- `spark/jobs/silver_stream.py`
- `spark/jobs/gold_stream.py`
- `spark/sql/register_tables.sql`
- `docker-compose.yml` neu can package hoac config bo sung
- `docs/interfaces.md`
- `docs/run-system.md`

Cong viec chi tiet:

- Them Delta Lake package cho Spark
- Doi format ghi doc:
  - Bronze tu `parquet` sang `delta`
  - Silver tu `parquet` sang `delta`
  - Gold tu `parquet` sang `delta`
- Doi script dang ky bang trong metastore sang `USING DELTA`
- Kiem tra lai kha nang:
  - Spark doc/ghi streaming
  - Spark SQL truy van
  - Spark Thrift Server truy van
- Kiem tra lai cac external table va metadata
- Cap nhat tai lieu ket noi/query neu co thay doi cu phap

Kiem tra cuoi checkpoint:

- Bronze/Silver/Gold deu ghi duoc du lieu dang Delta
- `SHOW TABLES` va `SELECT` chay duoc qua `spark-sql`
- Truy van qua DBeaver/Thrift van hoat dong

Dieu kien pass:

- Pipeline van chay end-to-end sau khi doi sang Delta
- Query layer van su dung duoc
- Co the giai thich ro day la lakehouse dung nghia hon truoc

Neu fail thi uu tien sua ngay:

- job streaming khong doc/ghi duoc Delta
- register table sai format
- Thrift query bi vo sau khi chuyen doi

## Checkpoint 5: Tong kiem tra end-to-end va chot ban nang cap

Muc tieu:

- Xac nhan toan bo he thong da on sau cac nang cap.
- Chot mot ban demo va van hanh co the dung cho trinh bay.

Pham vi thuc hien:

- toan bo pipeline
- tai lieu van hanh va truy van
- bao cao tong ket checkpoint

Cong viec chi tiet:

- Khoi dong lai he thong tu dau
- Chay producer theo polling
- Xac nhan du lieu di qua Bronze -> Silver -> Gold
- Chay smoke test
- Chay quality check
- Truy van qua `spark-sql`
- Truy van qua DBeaver/Thrift
- Ra soat lai tai lieu:
  - `README.md`
  - `docs/run-system.md`
  - `docs/query-guide.md`
  - `docs/interfaces.md`
- Viet report tong ket cho giai doan nang cap part 2

Kiem tra cuoi checkpoint:

- Co mot quy trinh khoi dong va demo on dinh
- Co bo truy van kiem tra nhanh
- Co tai lieu de doc lai va ban giao

Dieu kien pass:

- He thong chay end-to-end
- Ingestion on hon truoc
- Model da duoc benchmark lai
- Query layer va metadata on
- Delta Lake da vao duoc he thong neu checkpoint 4 pass

## Thu tu thuc thi de nghi

1. Lam xong Checkpoint 1 va test ngay producer
2. Sang Checkpoint 2 de biet model hien dang manh den dau
3. Sang Checkpoint 3 de co bo kiem tra van hanh ro rang
4. Khi he thong da de kiem tra va debug hon, moi sang Checkpoint 4
5. Checkpoint 5 dung de tong kiem tra, chot ban demo va tai lieu

## Nguyen tac lam viec cho part 2

- Khong nhay qua Delta Lake truoc khi co cach kiem tra he thong ro rang
- Moi thay doi lon phai co buoc kiem tra ngay sau khi sua
- Neu checkpoint nao fail, sua xong checkpoint do roi moi sang checkpoint tiep
- Uu tien thay doi lam he thong de giai thich hon, de demo hon, va de van hanh on hon
