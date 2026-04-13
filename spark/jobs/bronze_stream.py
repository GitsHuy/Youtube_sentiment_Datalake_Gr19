from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp, from_json
from pyspark.sql.types import (
    BooleanType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)


def create_spark() -> SparkSession:
    return SparkSession.builder.appName("bronze-youtube-comments").getOrCreate()


def build_schema() -> StructType:
    return StructType(
        [
            StructField("event_time", TimestampType(), True),
            StructField("collected_at", TimestampType(), True),
            StructField("comment_id", StringType(), True),
            StructField("video_id", StringType(), True),
            StructField("author", StringType(), True),
            StructField("text", StringType(), True),
            StructField("like_count", IntegerType(), True),
            StructField("reply_count", IntegerType(), True),
            StructField("is_reply", BooleanType(), True),
            StructField("parent_comment_id", StringType(), True),
            StructField("lang", StringType(), True),
            StructField("source", StringType(), True),
        ]
    )


def main() -> None:
    spark = create_spark()
    schema = build_schema()

    kafka_bootstrap = "kafka:9092"
    topic = "youtube-comments"
    bronze_path = "hdfs://namenode:8020/lake/bronze/youtube_comments"
    checkpoint_path = "hdfs://namenode:8020/checkpoints/bronze_youtube_comments"

    raw_stream = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap)
        .option("subscribe", topic)
        .option("startingOffsets", "latest")
        .load()
    )

    parsed_stream = raw_stream.select(
        from_json(
            col("value").cast("string"),
            schema,
            {"timestampFormat": "yyyy-MM-dd'T'HH:mm:ssX"},
        ).alias("json")
    )

    bronze_df = (
        parsed_stream.filter(col("json").isNotNull())
        .select("json.*")
        .withColumn("ingested_at", current_timestamp())
    )

    (
        bronze_df.writeStream.format("parquet")
        .outputMode("append")
        .option("checkpointLocation", checkpoint_path)
        .start(bronze_path)
        .awaitTermination()
    )


if __name__ == "__main__":
    main()
