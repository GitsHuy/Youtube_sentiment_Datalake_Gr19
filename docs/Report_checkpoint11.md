# Report Checkpoint 11

Ngay cap nhat: `2026-04-15`

## 1. Muc tieu checkpoint

Checkpoint 11 tap trung vao van hanh:

- co smoke test tong quat
- co quality check du lieu cho Bronze, Silver, Gold
- co cach phan biet loi ha tang voi loi du lieu

## 2. Cac file da tao va cap nhat

- [scripts/smoke_test.ps1](/d:/AHCMUTE_HocTap/BigDataAnalysis/BT_CuoiKy/Project_nhom19_datalakehouse/scripts/smoke_test.ps1)
- [scripts/invoke_hive_jdbc_sql.ps1](/d:/AHCMUTE_HocTap/BigDataAnalysis/BT_CuoiKy/Project_nhom19_datalakehouse/scripts/invoke_hive_jdbc_sql.ps1)
- [scripts/download_hive_jdbc.ps1](/d:/AHCMUTE_HocTap/BigDataAnalysis/BT_CuoiKy/Project_nhom19_datalakehouse/scripts/download_hive_jdbc.ps1)
- [spark/sql/checkpoint11_quality_checks.sql](/d:/AHCMUTE_HocTap/BigDataAnalysis/BT_CuoiKy/Project_nhom19_datalakehouse/spark/sql/checkpoint11_quality_checks.sql)
- [docs/smoke-test-guide.md](/d:/AHCMUTE_HocTap/BigDataAnalysis/BT_CuoiKy/Project_nhom19_datalakehouse/docs/smoke-test-guide.md)

## 3. Nhung gi da cai thien

### 3.1. Smoke test khong con phu thuoc hoan toan vao docker exec

Ban dau checkpoint 11 phu thuoc nhieu vao:

- `docker ps`
- `docker exec spark-master ... spark-sql`

Tren may Windows hien tai, Docker Desktop bi loi `Internal Server Error` lap lai, nen cach cu khong on dinh.

Da doi huong smoke test sang:

- kiem tra port nen tang tren host
- dung JDBC/Thrift de kiem tra metastore va bang

Y nghia:

- sat hon voi cach DBeaver va Power BI ket noi that
- giam phu thuoc vao Docker API

### 3.2. Them helper JDBC query

Da tao script `invoke_hive_jdbc_sql.ps1` de:

- tu dong tai Hive JDBC driver neu chua co
- dung Java JDBC query toi `jdbc:hive2://localhost:10000/lakehouse`
- chay query string hoac file SQL

Y nghia:

- co mot duong query ngoai container
- de su dung lai cho smoke test va kiem tra thu cong

### 3.3. Chuan hoa quality checks

File `checkpoint11_quality_checks.sql` gom:

- row count cua Bronze, Silver, Gold summary, Gold breakdown
- distinct `video_id`
- null check o cot quan trong
- duplicate `comment_id` tai Silver
- sentiment distribution
- doi chieu luong du lieu theo `video_id`

Y nghia:

- sau moi lan restart hoac nang cap co the kiem nhanh suc khoe du lieu

## 4. Loi ha tang da phat hien

Trong luc chot checkpoint 11, phat hien 2 nhom loi van hanh:

### 4.1. Docker Desktop API khong on dinh

Trieu chung:

- `docker ps`
- `docker logs`
- `docker exec`

co luc tra ve:

- `Internal Server Error for API route ... dockerDesktopLinuxEngine`

Anh huong:

- kho truy vet container bang lenh Docker CLI
- build/recreate service de bi treo

### 4.2. Hive Metastore va Thrift Server len port nhung chua on dinh session

Da thay:

- cong `9083` mo
- cong `10000` mo

nhung co luc:

- `spark-sql` khong mo duoc session metastore
- JDBC vao Thrift bi `Read timed out`

Y nghia:

- service level "port open" chua du de ket luan checkpoint PASS
- van can query that su thanh cong

## 5. Cac sua ha tang da ap dung

### 5.1. Hive Metastore

Da cap nhat:

- [hive/conf/hive-site.xml.template](/d:/AHCMUTE_HocTap/BigDataAnalysis/BT_CuoiKy/Project_nhom19_datalakehouse/hive/conf/hive-site.xml.template)
- [hive/scripts/start-metastore.sh](/d:/AHCMUTE_HocTap/BigDataAnalysis/BT_CuoiKy/Project_nhom19_datalakehouse/hive/scripts/start-metastore.sh)
- [docker-compose.yml](/d:/AHCMUTE_HocTap/BigDataAnalysis/BT_CuoiKy/Project_nhom19_datalakehouse/docker-compose.yml)

Noi dung chinh:

- them bind host cho metastore
- uu tien IPv4 cho JVM
- them healthcheck cho `hive-metastore`
- mount truc tiep file cau hinh/script de tranh build image lai khong can thiet

### 5.2. Spark -> Metastore

Da cap nhat Spark dung `host.docker.internal:9083` cho `hive.metastore.uris` trong cau hinh moi de hop voi moi truong Windows hon.

## 6. Cap nhat bo sung sau khi chay lai he thong

Sau lan kiem tra moi nhat, da bo sung them 2 cai thien quan trong:

### 6.1. Smoke test co fallback sang `spark-sql`

File [scripts/smoke_test.ps1](/d:/AHCMUTE_HocTap/BigDataAnalysis/BT_CuoiKy/Project_nhom19_datalakehouse/scripts/smoke_test.ps1) hien tai uu tien:

- JDBC / Thrift

neu nhanh do that bai thi tu dong fallback sang:

- `spark-sql` trong `spark-master`

Y nghia:

- van co bai test van hanh PASS/FALL ro rang
- khong bi khet boi DBeaver/JDBC tren Windows trong luc pipeline ben trong van chay

### 6.2. Ha Hive Metastore ve ban tuong thich hon

Da doi [hive/Dockerfile](/d:/AHCMUTE_HocTap/BigDataAnalysis/BT_CuoiKy/Project_nhom19_datalakehouse/hive/Dockerfile):

- tu `apache/hive:4.0.0`
- ve `apache/hive:3.1.3`

Ly do:

- Spark hien tai la `3.3.0`
- Hive `4.0.0` gay loi metastore `TTransportException`
- `spark-sql` khong the on dinh voi metastore cu

Sau khi ha ve `3.1.3`:

- `spark-sql -e 'SHOW DATABASES'` tren `spark-master` chay lai duoc
- smoke test fallback qua `spark-sql` chay PASS

## 7. Ket qua checkpoint

Checkpoint 11 duoc chot PASS theo huong van hanh thuc dung:

- port nen tang san sang
- metastore da tuong thich lai voi Spark
- register table va quality check chay duoc qua `spark-sql` fallback
- smoke test tong the da ra `PASS`

Trang thai con lai chua dong:

- truy van truc tiep qua JDBC / Thrift van chua on dinh 100%
- nghia la bai test van hanh da co, nhung ket noi client ngoai nhu DBeaver van can xu ly them

## 8. Buoc tiep theo

Sau checkpoint 11, he thong duoc tiep tuc nang cap sang checkpoint 12:

- chuyen Bronze, Silver, Gold sang Delta Lake
- giu nguyen ten bang logic de query layer khong doi
