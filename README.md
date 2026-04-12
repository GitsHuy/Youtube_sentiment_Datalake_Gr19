# Project Nhom 19 Datalakehouse

Day la bo khung dung chung cho do an phan tich cam xuc binh luan YouTube theo huong lakehouse.

He thong hien tai da co san:

- Kafka va Kafka UI
- HDFS gom NameNode, DataNode va buoc khoi tao thu muc
- producer mau de bom du lieu fallback
- Spark master, worker va 3 job Bronze, Silver, Gold
- Hive Metastore dung SQL Server local
- Spark Thrift Server de noi JDBC va Power BI

Quyet dinh hien tai cua nhom:

- giu SQL Server local
- chua dua Delta Lake vao ngay
- giu bo du lieu mau de moi thanh vien tu test doc lap
- phat trien tiep tren bo khung nay, khong lam lai ha tang tu dau

Doc tai lieu theo thu tu nay:

- `docs/run-system.md`: cach chay he thong va kiem tra tung phan
- `docs/interfaces.md`: hop dong schema, topic, path va bang dung chung
- `docs/team-assignment.md`: bang phan cong chi tiet cho A, B, C

Nguyen tac chung:

- nhung ten dung chung nhu Kafka topic, HDFS path, database, ten bang cot loi khong duoc doi neu chu chua dong y

## Cau truc repository

- `data/`: du lieu mau de test local
- `producer/`: phan ingestion hien tai
- `spark/`: Spark jobs, SQL dang ky bang va cau hinh runtime
- `hadoop/`: cau hinh HDFS client duoc mount vao Spark va Hive
- `hive/`: image Hive Metastore, template config va script khoi dong
- `sqlserver/`: ghi chu lien quan den SQL Server local
- `scripts/`: script ho tro reset va tai JDBC driver
- `docs/`: tai lieu van hanh va phoi hop cho nhom

## Pham vi baseline hien tai

Code hien tai van la baseline de phat trien tiep:

- ingestion mac dinh doc `data/sample_comments.jsonl`
- producer mau mac dinh chi gui 1 luot de tranh nhan ban so lieu
- Bronze, Silver, Gold dang ghi ra `PARQUET`
- Silver dang dung baseline sentiment theo tu khoa
- Silver da co khau dedup theo `comment_id`
- Spark Thrift Server da co san cho lop truy van SQL

Day la chu y co chu dich de A, B, C co the lam song song tren mot nen on dinh.
