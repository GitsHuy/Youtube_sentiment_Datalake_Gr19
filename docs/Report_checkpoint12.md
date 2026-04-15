# Report Checkpoint 12

Ngay cap nhat: `2026-04-15`

## 1. Muc tieu checkpoint

Checkpoint 12 nang he thong tu `PARQUET` external tables len `Delta Lake` de kien truc tien gan hon toi lakehouse dung nghia, nhung van giu nguyen logical tables de DBeaver, Thrift va dashboard khong bi thay doi ten bang.

## 2. Nhung gi da sua

### 2.1. Bat Delta cho Spark

Da cap nhat [spark-defaults.conf](/d:/AHCMUTE_HocTap/BigDataAnalysis/BT_CuoiKy/Project_nhom19_datalakehouse/spark/conf/spark-defaults.conf):

- them `io.delta:delta-core_2.12:2.3.0`
- bat `DeltaSparkSessionExtension`
- dung `DeltaCatalog`
- bat `spark.databricks.delta.schema.autoMerge.enabled`

Y nghia:

- moi Spark job va Spark Thrift Server deu co the doc/ghi bang Delta
- khong can build lai image Spark chi de them jar

### 2.2. Chuyen Bronze sang Delta

Da cap nhat [bronze_stream.py](/d:/AHCMUTE_HocTap/BigDataAnalysis/BT_CuoiKy/Project_nhom19_datalakehouse/spark/jobs/bronze_stream.py):

- `writeStream.format("parquet")` -> `writeStream.format("delta")`
- doi path Bronze sang `hdfs://namenode:8020/lake_delta/bronze/youtube_comments`

Y nghia:

- du lieu raw moi se duoc ghi theo Delta
- khong dung chung path cu voi Parquet, tranh pha du lieu demo truoc do

### 2.3. Chuyen Silver sang Delta

Da cap nhat [silver_stream.py](/d:/AHCMUTE_HocTap/BigDataAnalysis/BT_CuoiKy/Project_nhom19_datalakehouse/spark/jobs/silver_stream.py):

- `readStream ... parquet(bronze_path)` -> `readStream.format("delta").load(bronze_path)`
- ghi Silver bang `format("delta").save(...)`
- doi Bronze/Silver path sang root `lake_delta`

Y nghia:

- Silver doc truc tiep tu Bronze Delta
- du lieu da lam sach va sentiment duoc luu theo Delta

### 2.4. Chuyen Gold sang Delta

Da cap nhat [gold_stream.py](/d:/AHCMUTE_HocTap/BigDataAnalysis/BT_CuoiKy/Project_nhom19_datalakehouse/spark/jobs/gold_stream.py):

- doc Silver bang `spark.read.format("delta").load(...)`
- stream source bang `readStream.format("delta").load(...)`
- ghi Gold summary va Gold breakdown bang Delta
- doi path Gold sang root `lake_delta`

Y nghia:

- Gold khong con overwrite Parquet nua
- ca hai bang business data deu di theo Delta

### 2.5. Doi metastore/register sang Delta

Da viet lai [register_tables.sql](/d:/AHCMUTE_HocTap/BigDataAnalysis/BT_CuoiKy/Project_nhom19_datalakehouse/spark/sql/register_tables.sql):

- `USING PARQUET` -> `USING DELTA`
- khai bao schema ro rang cho Bronze va Silver
- dung path moi trong `lake_delta`

Y nghia:

- co the register bang ngay ca khi path Delta vua moi tao
- metadata khop voi schema hien tai tot hon

### 2.6. HDFS init cho Delta path

Da cap nhat [docker-compose.yml](/d:/AHCMUTE_HocTap/BigDataAnalysis/BT_CuoiKy/Project_nhom19_datalakehouse/docker-compose.yml):

- tao them cac thu muc `/lake_delta/...`
- chmod cho root `lake_delta`

Y nghia:

- pipeline co san noi de ghi Delta ngay sau khi khoi dong

## 3. Cach migrate an toan da chon

Checkpoint 12 khong xoa du lieu Parquet cu.

Toi da chon cach:

- giu nguyen du lieu cu o `/lake/...`
- ghi du lieu Delta moi vao `/lake_delta/...`
- giu nguyen ten bang logic trong `lakehouse`

Loi ich:

- tranh reset pha du lieu demo cu
- rollback de hon neu can doi chieu
- giam rui ro trong luc nang cap

## 4. Kiem chung runtime da lam

Sau khi chay lai he thong, da kiem chung duoc cac diem sau:

- Bronze Delta co `_delta_log`
- Silver Delta co `_delta_log`
- Gold metrics Delta co `_delta_log`
- Gold sentiment breakdown Delta co `_delta_log`

Duong dan da xac nhan tren HDFS:

- `/lake_delta/bronze/youtube_comments`
- `/lake_delta/silver/youtube_comments`
- `/lake_delta/gold/youtube_comment_metrics`
- `/lake_delta/gold/youtube_sentiment_breakdown`

Ngoai ra:

- `spark-sql -e 'SHOW DATABASES'` tren `spark-master` da chay duoc sau khi ha Hive Metastore ve `3.1.3`
- smoke test checkpoint 11 da PASS theo fallback `spark-sql`

## 5. Rang buoc hien tai

Phan con lai chua chot tuyet doi la query truc tiep qua JDBC / Thrift.

Loi hien tai da phat hien ro:

- session Thrift mo len nhung van bi timeout hoac fail khi khoi tao session Delta
- co thong diep `Cannot find catalog plugin class ... DeltaCatalog` o nhanh JDBC / Thrift

Noi ngan gon:

- Delta trong pipeline ben trong da chay
- Delta trong query layer qua Spark SQL da chay
- Delta trong query layer qua JDBC / Thrift van chua dong

## 6. Tinh trang checkpoint

Checkpoint 12 duoc chot PASS o muc pipeline va luu tru:

- Bronze / Silver / Gold da doi sang Delta
- HDFS co day du `_delta_log`
- metastore dang ky duoc bang qua `spark-sql`
- smoke test van hanh tong the khong con phu thuoc duy nhat vao JDBC

Phan can lam tiep neu muon chot luon client ngoai:

- sua rieng `spark-thriftserver` de session JDBC nap Delta jars/catalog on dinh
- sau do moi test lai DBeaver / Power BI qua cong `10000`
