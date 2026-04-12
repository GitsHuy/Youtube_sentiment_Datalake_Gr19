from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import avg, col, count, sum, to_date, when


def create_spark() -> SparkSession:
    return SparkSession.builder.appName("gold-youtube-comments").getOrCreate()


def build_gold_snapshot(spark: SparkSession, silver_path: str) -> DataFrame:
    silver_df = spark.read.parquet(silver_path)

    return (
        silver_df.withColumn("event_date", to_date(col("event_time")))
        .groupBy("event_date", "video_id", "sentiment")
        .agg(
            count("*").alias("comment_count"),
            avg("like_count").alias("avg_likes"),
            avg("reply_count").alias("avg_replies"),
            sum(when(col("is_reply") == True, 1).otherwise(0)).alias("reply_comment_count"),
        )
    )


def write_gold_snapshot(batch_df: DataFrame, batch_id: int) -> None:
    spark = batch_df.sparkSession
    silver_path = "hdfs://namenode:8020/lake/silver/youtube_comments"
    gold_path = "hdfs://namenode:8020/lake/gold/youtube_comment_metrics"

    gold_df = build_gold_snapshot(spark, silver_path)
    gold_df.write.mode("overwrite").parquet(gold_path)
    print(f"Gold snapshot refreshed for batch {batch_id}.", flush=True)


def main() -> None:
    spark = create_spark()

    silver_path = "hdfs://namenode:8020/lake/silver/youtube_comments"
    checkpoint_path = "hdfs://namenode:8020/checkpoints/gold_youtube_comment_metrics"
    silver_schema = spark.read.parquet(silver_path).schema

    silver_stream = spark.readStream.schema(silver_schema).parquet(silver_path)

    (
        silver_stream.writeStream.foreachBatch(write_gold_snapshot)
        .outputMode("append")
        .option("checkpointLocation", checkpoint_path)
        .start()
        .awaitTermination()
    )


if __name__ == "__main__":
    main()
