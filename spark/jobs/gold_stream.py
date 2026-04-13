from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import avg, col, count, countDistinct, round, sum, to_date, when


SILVER_PATH = "hdfs://namenode:8020/lake/silver/youtube_comments"
GOLD_SUMMARY_PATH = "hdfs://namenode:8020/lake/gold/youtube_comment_metrics"
GOLD_BREAKDOWN_PATH = "hdfs://namenode:8020/lake/gold/youtube_sentiment_breakdown"


def create_spark() -> SparkSession:
    return SparkSession.builder.appName("gold-youtube-comments").getOrCreate()


def build_gold_summary(silver_df: DataFrame) -> DataFrame:
    grouped = silver_df.groupBy("event_date", "video_id").agg(
        count("*").alias("total_comments"),
        sum(when(col("is_reply") == True, 1).otherwise(0)).alias("reply_comment_count"),
        sum(when(col("is_reply") == False, 1).otherwise(0)).alias("top_level_comment_count"),
        countDistinct("author").alias("unique_author_count"),
        sum("like_count").alias("total_likes"),
        avg("like_count").alias("avg_likes_per_comment"),
        avg("reply_count").alias("avg_reply_count"),
        avg("text_length").alias("avg_text_length"),
        avg("collected_delay_seconds").alias("avg_collected_delay_seconds"),
        sum(when(col("sentiment") == "positive", 1).otherwise(0)).alias("positive_comment_count"),
        sum(when(col("sentiment") == "neutral", 1).otherwise(0)).alias("neutral_comment_count"),
        sum(when(col("sentiment") == "negative", 1).otherwise(0)).alias("negative_comment_count"),
    )

    return (
        grouped.withColumn(
            "positive_ratio",
            round(
                when(col("total_comments") > 0, col("positive_comment_count") / col("total_comments")).otherwise(0.0),
                4,
            ),
        )
        .withColumn(
            "neutral_ratio",
            round(
                when(col("total_comments") > 0, col("neutral_comment_count") / col("total_comments")).otherwise(0.0),
                4,
            ),
        )
        .withColumn(
            "negative_ratio",
            round(
                when(col("total_comments") > 0, col("negative_comment_count") / col("total_comments")).otherwise(0.0),
                4,
            ),
        )
        .withColumn(
            "reply_ratio",
            round(
                when(col("total_comments") > 0, col("reply_comment_count") / col("total_comments")).otherwise(0.0),
                4,
            ),
        )
        .withColumn("engagement_score", col("total_likes") + col("reply_comment_count"))
        .select(
            "event_date",
            "video_id",
            "total_comments",
            "top_level_comment_count",
            "reply_comment_count",
            "unique_author_count",
            "total_likes",
            round(col("avg_likes_per_comment"), 2).alias("avg_likes_per_comment"),
            round(col("avg_reply_count"), 2).alias("avg_reply_count"),
            round(col("avg_text_length"), 2).alias("avg_text_length"),
            round(col("avg_collected_delay_seconds"), 2).alias("avg_collected_delay_seconds"),
            "positive_comment_count",
            "neutral_comment_count",
            "negative_comment_count",
            "positive_ratio",
            "neutral_ratio",
            "negative_ratio",
            "reply_ratio",
            "engagement_score",
        )
    )


def build_gold_sentiment_breakdown(silver_df: DataFrame, gold_summary_df: DataFrame) -> DataFrame:
    breakdown = silver_df.groupBy("event_date", "video_id", "sentiment").agg(
        count("*").alias("comment_count"),
        avg("like_count").alias("avg_likes"),
        avg("reply_count").alias("avg_replies"),
        sum(when(col("is_reply") == True, 1).otherwise(0)).alias("reply_comment_count"),
        avg("text_length").alias("avg_text_length"),
    )

    totals = gold_summary_df.select("event_date", "video_id", "total_comments")

    return (
        breakdown.join(totals, on=["event_date", "video_id"], how="left")
        .withColumn(
            "comment_ratio",
            round(when(col("total_comments") > 0, col("comment_count") / col("total_comments")).otherwise(0.0), 4),
        )
        .select(
            "event_date",
            "video_id",
            "sentiment",
            "comment_count",
            "comment_ratio",
            round(col("avg_likes"), 2).alias("avg_likes"),
            round(col("avg_replies"), 2).alias("avg_replies"),
            "reply_comment_count",
            round(col("avg_text_length"), 2).alias("avg_text_length"),
        )
    )


def write_gold_snapshot(batch_df: DataFrame, batch_id: int) -> None:
    spark = batch_df.sparkSession
    silver_df = spark.read.parquet(SILVER_PATH).withColumn("event_date", to_date(col("event_time")))

    gold_summary_df = build_gold_summary(silver_df)
    gold_breakdown_df = build_gold_sentiment_breakdown(silver_df, gold_summary_df)

    gold_summary_df.write.mode("overwrite").parquet(GOLD_SUMMARY_PATH)
    gold_breakdown_df.write.mode("overwrite").parquet(GOLD_BREAKDOWN_PATH)
    print(f"Gold summary and sentiment breakdown refreshed for batch {batch_id}.", flush=True)


def main() -> None:
    spark = create_spark()

    checkpoint_path = "hdfs://namenode:8020/checkpoints/gold_youtube_comment_metrics"
    silver_schema = spark.read.parquet(SILVER_PATH).schema

    silver_stream = spark.readStream.schema(silver_schema).parquet(SILVER_PATH)

    (
        silver_stream.writeStream.foreachBatch(write_gold_snapshot)
        .outputMode("append")
        .option("checkpointLocation", checkpoint_path)
        .start()
        .awaitTermination()
    )


if __name__ == "__main__":
    main()
