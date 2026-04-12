# Team Assignment

Tai lieu nay la bang phan cong va cach lam viec song song tren baseline hien tai.

## 1. Nguyen tac chung truoc khi chia viec

Repo da co baseline chay duoc. Nhom nen cai tien tren baseline nay, khong lam lai ha tang tu dau.

Nhung file dung chung chi nen do chu sua truc tiep, tru khi co phe duyet:

- `docker-compose.yml`
- `.env.example`
- `README.md`
- `docs/interfaces.md`

Moi thanh vien nen sua chu yeu trong module minh phu trach.

## 2. Kien truc dang co san trong repo

| Tang | Trang thai hien tai | File chinh |
| --- | --- | --- |
| Ingestion fallback | producer mau gui du lieu vao Kafka | `data/sample_comments.jsonl`, `producer/producer.py` |
| Bronze | Kafka sang HDFS raw da noi san | `spark/jobs/bronze_stream.py` |
| Silver | cleaning va sentiment baseline da co | `spark/jobs/silver_stream.py` |
| Gold | metric tong hop da co | `spark/jobs/gold_stream.py` |
| Metadata | Hive Metastore da co va dung SQL Server local | `hive/`, `spark/sql/register_tables.sql` |
| SQL consumption | Spark Thrift Server da co | `docker-compose.yml`, `scripts/download_hive_jdbc.ps1` |

Y nghia:

- moi nguoi deu co the bat dau tu mot bo khung cu the
- khong ai phai ngoi cho nguoi khac lam xong moi toi luot

## 3. Nguoi A: Ingestion, API, Kafka

### Muc tieu chinh

Bien producer hien tai thanh collector dung YouTube Data API cho 1 `videoId`, nhung van giu sample mode de test.

### File A nen lam truoc

- `producer/producer.py`
- `producer/requirements.txt`
- `data/sample_comments.jsonl` neu can cap nhat bo du lieu mau
- `.env` o may cua A de test

### File A nen doc nhung khong so huu

- `docs/interfaces.md`
- `docker-compose.yml`
- `spark/jobs/bronze_stream.py`

### Dau ra A can ban giao

- cach truyen vao 1 `videoId`
- luong goi YouTube API that
- ban ghi Kafka dung schema da khoa trong `docs/interfaces.md`
- sample mode van chay de fallback

### Ke hoach lam viec cho A

Giai doan 1:

- chay producer mau hien tai
- hieu dang message dang day vao Kafka

Giai doan 2:

- them dependency YouTube API va env can thiet
- viet logic lay comment tu 1 `videoId`
- map du lieu ve schema chung

Giai doan 3:

- ho tro ca `sample` va `youtube_api`
- dam bao Bronze van doc duoc binh thuong

Giai doan 4:

- dua cho B va C 5 den 10 ban ghi mau tu API that
- ghi ro cot nao co the null, cot nao luon co

### Vi sao A co the lam doc lap

- sample producer da co san
- Kafka topic da co dinh
- B khong can cho A hoan thien API that moi bat dau duoc

### Lenh A tu kiem tra

```powershell
docker compose up -d producer
docker compose logs --tail 100 producer
```

Kiem tra topic bang Kafka UI:

- `http://localhost:8080`

### Dieu kien de A xem nhu xong

- nhap duoc 1 `videoId`
- Kafka nhan ban ghi tu YouTube API that
- sample mode van chay
- schema Kafka dung hop dong chung

## 4. Nguoi B: Bronze, Silver, Gold va model

### Muc tieu chinh

Cai tien pipeline xu ly du lieu va thay baseline sentiment hien tai bang workflow model tot hon.

### Dieu B can nam ro

B khong can cho A xong API.

B bat dau tu:

- `data/sample_comments.jsonl`
- hop dong message trong `docs/interfaces.md`
- cac Spark job baseline da co

### File B nen lam truoc

- `spark/jobs/bronze_stream.py`
- `spark/jobs/silver_stream.py`
- `spark/jobs/gold_stream.py`
- co the tao them script train/inference trong `spark/jobs/` sau khi thong nhat voi chu

### File B nen doc nhung khong so huu

- `docs/interfaces.md`
- `spark/sql/register_tables.sql`
- `data/sample_comments.jsonl`

### Dau ra B can ban giao

- Bronze on dinh va khong pha hop dong schema
- Silver tot hon o lam sach, dac trung, sentiment
- co duong train model ro rang
- Gold co metric phu hop cho dashboard

### Ke hoach lam viec cho B

Giai doan 1:

- chay baseline Bronze, Silver, Gold bang du lieu mau
- xac nhan schema va output hien tai

Giai doan 2:

- cai tien Bronze neu can bo sung metadata hoac xu ly schema
- khong bien Bronze thanh tang cleaning nang

Giai doan 3:

- cai tien Silver preprocessing
- xu ly null, text ban, ngon ngu khong dong deu
- xac dinh feature sentiment
- giu co che dedup theo `comment_id`

Giai doan 4:

- chuan bi format du lieu train
- chon huong model
- train hoac tich hop model tot hon
- dua ket qua model quay lai Silver

Giai doan 5:

- cai tien Gold de C co nhieu metric hon
- nhung van giu bo cot baseline de C khong bi vo dashboard

### Huong lam viec toi uu cho B

- giu baseline keyword hien tai song song voi huong model moi
- thu nghiem dan dan, khong sua mot lan gay vo toan stream

### Lenh B tu kiem tra

```powershell
docker compose up -d spark-bronze spark-silver spark-gold
docker compose logs --tail 100 spark-bronze
docker compose logs --tail 100 spark-silver
docker compose logs --tail 100 spark-gold
```

Kiem tra 3 bang sau khi dang ky:

```powershell
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SELECT * FROM lakehouse.bronze_youtube_comments LIMIT 5'"
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SELECT comment_id, text_clean, sentiment FROM lakehouse.silver_youtube_comments LIMIT 10'"
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SELECT * FROM lakehouse.gold_youtube_comment_metrics LIMIT 10'"
```

### Dieu kien de B xem nhu xong

- Bronze van ingest dung
- Silver sach hon va sentiment tot hon
- co duong model test duoc
- Gold mo ra metric huu ich cho C

## 5. Nguoi C: Metastore, SQL, JDBC va Power BI

### Muc tieu chinh

So huu lop truy cap du lieu va trinh bay de du lieu xu ly co the query duoc va len dashboard.

### File C nen lam truoc

- `hive/conf/hive-site.xml.template`
- `hive/scripts/start-metastore.sh`
- `spark/sql/register_tables.sql`
- `scripts/download_hive_jdbc.ps1`

### File C nen doc nhung khong so huu

- `docs/interfaces.md`
- `docker-compose.yml`
- `spark/jobs/gold_stream.py`

### Dau ra C can ban giao

- Hive Metastore on dinh tren SQL Server local
- dang ky bang external cho Bronze, Silver, Gold
- Spark Thrift Server truy cap duoc
- JDBC test qua
- Power BI doc duoc Gold va co dashboard dau tien

### Ke hoach lam viec cho C

Giai doan 1:

- chay baseline Metastore
- xac nhan ket noi toi SQL Server local
- xac nhan dang ky bang `lakehouse` thanh cong

Giai doan 2:

- query thu Bronze, Silver, Gold trong Spark SQL
- xac nhan Thrift Server nghe cong `10000`

Giai doan 3:

- test JDBC bang DBeaver hoac cong cu tuong tu
- chuan bi thong tin ket noi cho Power BI

Giai doan 4:

- dung dashboard Power BI dau tien tren Gold
- uu tien don gian, on dinh
- khi B them metric thi cap nhat dashboard sau

### Vi sao C co the lam doc lap

- Metastore, dang ky bang va Thrift Server da co san
- C co the test tren bang baseline truoc khi B nang cap model

### Lenh C tu kiem tra

```powershell
docker compose up -d hive-metastore spark-thriftserver
docker compose logs --tail 100 hive-metastore
docker compose logs --tail 100 spark-thriftserver
```

Dang ky va query bang:

```powershell
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -f /opt/sql/register_tables.sql"
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SHOW TABLES IN lakehouse'"
docker compose exec spark-master /bin/bash -lc "/opt/spark/bin/spark-sql -e 'SELECT * FROM lakehouse.gold_youtube_comment_metrics LIMIT 10'"
```

### Dieu kien de C xem nhu xong

- Metastore on dinh voi SQL Server local
- bang dang ky va query duoc
- JDBC truy cap duoc qua Spark Thrift Server
- Power BI doc duoc Gold

## 6. Vai tro cua chu

Chu nen tap trung vao tich hop va giu pham vi:

- giu on dinh ten dung chung
- phe duyet thay doi schema
- phe duyet thay doi `docker-compose.yml` va file dung chung
- chay full integration sau moi phase cua A, B, C
- quyet dinh khi nao baseline du on de merge chung

## 7. Thu tu tich hop de tranh vo he thong

Khong nen merge tat ca cung luc.

Thu tu goi y:

1. A chung minh collector API that map dung schema chung
2. B xac nhan Bronze va Silver van an schema do
3. B xac nhan Gold van giu bo cot toi thieu C can
4. C dang ky lai va test lop SQL
5. Chu chay full stack end-to-end
