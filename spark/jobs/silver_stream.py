from functools import reduce

from pyspark.sql import Column, SparkSession
from pyspark.sql.functions import (
    col,
    current_timestamp,
    instr,
    length,
    lit,
    lower,
    regexp_replace,
    trim,
    when,
)
from pyspark.sql.types import (
    BooleanType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)


POSITIVE_KEYWORDS = [
    "hay",
    "tot",
    "xuat sac",
    "cam on",
    "thich",
    "yeu",
    "dep",
    "tuyet",
    "awesome",
    "great",
    "good",
    "useful",
]

NEGATIVE_KEYWORDS = [
    "chan",
    "te",
    "do",
    "khong thich",
    "that vong",
    "toi",
    "met",
    "bad",
    "terrible",
    "boring",
    "poor",
]


def create_spark() -> SparkSession:
    return SparkSession.builder.appName("silver-youtube-comments").getOrCreate()


def build_schema() -> StructType:
    return StructType(
        [
            StructField("event_time", TimestampType(), True),
            StructField("comment_id", StringType(), True),
            StructField("video_id", StringType(), True),
            StructField("author", StringType(), True),
            StructField("text", StringType(), True),
            StructField("like_count", IntegerType(), True),
            StructField("reply_count", IntegerType(), True),
            StructField("is_reply", BooleanType(), True),
            StructField("lang", StringType(), True),
            StructField("ingested_at", TimestampType(), True),
        ]
    )


def keyword_score(text_column: Column, keywords: list[str]) -> Column:
    return reduce(
        lambda acc, keyword: acc + when(instr(text_column, keyword) > 0, 1).otherwise(0),
        keywords,
        lit(0),
    )


def main() -> None:
    spark = create_spark()
    schema = build_schema()

    bronze_path = "hdfs://namenode:8020/lake/bronze/youtube_comments"
    silver_path = "hdfs://namenode:8020/lake/silver/youtube_comments"
    checkpoint_path = "hdfs://namenode:8020/checkpoints/silver_youtube_comments"

    bronze_stream = spark.readStream.schema(schema).parquet(bronze_path)

    cleaned = (
        bronze_stream.withColumn("text_clean", trim(regexp_replace(lower(col("text")), r"\s+", " ")))
        .filter(col("event_time").isNotNull())
        .filter(col("comment_id").isNotNull())
        .filter(col("video_id").isNotNull())
        .filter(col("text").isNotNull())
        .filter(length(col("text_clean")) > 0)
        .withColumn("like_count", when(col("like_count").isNull(), lit(0)).otherwise(col("like_count")))
        .withColumn("reply_count", when(col("reply_count").isNull(), lit(0)).otherwise(col("reply_count")))
        .withColumn("lang", when(col("lang").isNull(), lit("unknown")).otherwise(col("lang")))
        .withColumn("silver_processed_at", current_timestamp())
    )

    deduplicated = cleaned.withWatermark("event_time", "1 day").dropDuplicates(["comment_id"])

    with_scores = (
        deduplicated.withColumn("positive_score", keyword_score(col("text_clean"), POSITIVE_KEYWORDS))
        .withColumn("negative_score", keyword_score(col("text_clean"), NEGATIVE_KEYWORDS))
        .withColumn(
            "sentiment",
            when(col("positive_score") > col("negative_score"), lit("positive"))
            .when(col("negative_score") > col("positive_score"), lit("negative"))
            .otherwise(lit("neutral")),
        )
    )

    (
        with_scores.writeStream.format("parquet")
        .outputMode("append")
        .option("checkpointLocation", checkpoint_path)
        .start(silver_path)
        .awaitTermination()
    )


if __name__ == "__main__":
    main()
