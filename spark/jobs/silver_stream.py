import json
import logging
import os
import re
from functools import reduce
from typing import Optional, Union

from pyspark.sql import Column, DataFrame, SparkSession
from pyspark.sql.functions import (
    coalesce,
    col,
    current_timestamp,
    greatest,
    instr,
    length,
    lit,
    lower,
    regexp_replace,
    trim,
    unix_timestamp,
    when,
)
from pyspark.sql.types import (
    BooleanType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("silver-youtube-comments")

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

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

UNICODE_ESCAPE_PATTERN = re.compile(r"(\\u[0-9a-fA-F]{4}|\\U[0-9a-fA-F]{8})")
REPEATED_LATIN_CHAR_PATTERN = re.compile(r"([a-z])\1{2,}")
ELONGATED_LATIN_WORD_PATTERN = re.compile(r"\b[a-z]*([a-z])\1{2,}[a-z]*\b")

SENTIMENT_MODE = os.getenv("SENTIMENT_MODE", "transformer").strip().lower()
SENTIMENT_MODEL_NAME = os.getenv(
    "SENTIMENT_MODEL_NAME",
    "wonrax/phobert-base-vietnamese-sentiment",
).strip()
SENTIMENT_BATCH_SIZE = int(os.getenv("SENTIMENT_BATCH_SIZE", "16"))
SENTIMENT_MAX_LENGTH = int(os.getenv("SENTIMENT_MAX_LENGTH", "256"))
SENTIMENT_FALLBACK_TO_KEYWORD = os.getenv(
    "SENTIMENT_FALLBACK_TO_KEYWORD",
    "true",
).strip().lower() == "true"
SENTIMENT_SLANG_LEXICON_PATH = os.getenv(
    "SENTIMENT_SLANG_LEXICON_PATH",
    "/opt/jobs/slang_sentiment_lexicon.json",
).strip()

_SENTIMENT_PREDICTOR = None
_SLANG_LEXICON = None


def create_spark() -> SparkSession:
    return SparkSession.builder.appName("silver-youtube-comments").getOrCreate()


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
            StructField("ingested_at", TimestampType(), True),
        ]
    )


def build_prediction_schema() -> StructType:
    return StructType(
        [
            StructField("video_id", StringType(), False),
            StructField("comment_id", StringType(), False),
            StructField("positive_score", IntegerType(), False),
            StructField("negative_score", IntegerType(), False),
            StructField("sentiment", StringType(), False),
        ]
    )


def build_silver_output_schema() -> StructType:
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
            StructField("ingested_at", TimestampType(), True),
            StructField("text_clean", StringType(), True),
            StructField("text_length", IntegerType(), True),
            StructField("collected_delay_seconds", LongType(), True),
            StructField("silver_processed_at", TimestampType(), True),
            StructField("positive_score", IntegerType(), True),
            StructField("negative_score", IntegerType(), True),
            StructField("sentiment", StringType(), True),
        ]
    )


def ensure_delta_table(spark: SparkSession, path: str, schema: StructType) -> None:
    spark.createDataFrame([], schema).write.format("delta").mode("ignore").save(path)


def keyword_score(text_column: Column, keywords: list[str]) -> Column:
    return reduce(
        lambda acc, keyword: acc + when(instr(text_column, keyword) > 0, 1).otherwise(0),
        keywords,
        lit(0),
    )


def normalize_blank_string(column: Column, default_value: Optional[str] = None) -> Column:
    normalized = trim(regexp_replace(coalesce(column, lit("")), r"\s+", " "))
    if default_value is None:
        return when(length(normalized) == 0, lit(None)).otherwise(normalized)
    return when(length(normalized) == 0, lit(default_value)).otherwise(normalized)


def normalize_text(text_column: Column) -> Column:
    return trim(
        regexp_replace(
            regexp_replace(
                regexp_replace(lower(coalesce(text_column, lit(""))), r"https?://\S+|www\.\S+", " "),
                r"[\r\n\t]+",
                " ",
            ),
            r"\s+",
            " ",
        )
    )


def sanitize_non_negative_int(column: Column) -> Column:
    return when(column.isNull() | (column < 0), lit(0)).otherwise(column)


def normalize_label(label: str) -> str:
    normalized = label.strip().lower()

    direct_mapping = {
        "positive": "positive",
        "pos": "positive",
        "negative": "negative",
        "neg": "negative",
        "neutral": "neutral",
        "neu": "neutral",
    }
    if normalized in direct_mapping:
        return direct_mapping[normalized]

    if "star" in normalized:
        star_value = int(normalized.split()[0])
        if star_value <= 2:
            return "negative"
        if star_value == 3:
            return "neutral"
        return "positive"

    if normalized in {"label_0", "0"}:
        return "negative"
    if normalized in {"label_1", "1"}:
        return "neutral"
    if normalized in {"label_2", "2"}:
        return "positive"

    raise ValueError(f"Unsupported sentiment label: {label}")


def load_slang_lexicon(path: str) -> list[dict]:
    if not path:
        return []

    if not os.path.exists(path):
        logger.info("Slang lexicon file not found at %s. Continuing without lexicon.", path)
        return []

    raw_entries = json.loads(open(path, "r", encoding="utf-8").read())
    prepared_entries = []
    for item in raw_entries:
        term = str(item["term"]).strip().lower()
        normalized = str(item["normalized"]).strip().lower()
        if not term or not normalized:
            continue

        if re.search(r"[a-z0-9]", term):
            pattern = re.compile(rf"(?<!\w){re.escape(term)}(?!\w)")
        else:
            pattern = re.compile(re.escape(term))

        prepared_entries.append(
            {
                "term": term,
                "normalized": normalized,
                "pattern": pattern,
            }
        )

    prepared_entries.sort(key=lambda item: len(item["term"]), reverse=True)
    logger.info("Loaded %s slang lexicon entries from %s", len(prepared_entries), path)
    return prepared_entries


def get_slang_lexicon() -> list[dict]:
    global _SLANG_LEXICON

    if _SLANG_LEXICON is None:
        _SLANG_LEXICON = load_slang_lexicon(SENTIMENT_SLANG_LEXICON_PATH)

    return _SLANG_LEXICON


def apply_slang_lexicon(text: str, lexicon_entries: list[dict]) -> str:
    if not lexicon_entries:
        return text

    updated_text = expand_elongated_latin_words(decode_unicode_escapes(text))
    for item in lexicon_entries:
        updated_text = item["pattern"].sub(f" {item['normalized']} ", updated_text)

    updated_text = re.sub(r"\s+", " ", updated_text).strip()
    return updated_text


def decode_unicode_escapes(text: str) -> str:
    if not text or "\\" not in text:
        return text

    def replace_match(match: re.Match[str]) -> str:
        token = match.group(0)
        try:
            return token.encode("ascii").decode("unicode_escape")
        except UnicodeDecodeError:
            return token

    return UNICODE_ESCAPE_PATTERN.sub(replace_match, text)


def canonicalize_repeated_latin_chars(text: str) -> str:
    if not text:
        return text
    return REPEATED_LATIN_CHAR_PATTERN.sub(r"\1", text)


def expand_elongated_latin_words(text: str) -> str:
    if not text:
        return text

    def replace_match(match: re.Match[str]) -> str:
        original = match.group(0)
        normalized = canonicalize_repeated_latin_chars(original)
        if normalized == original:
            return original
        return f"{original} {normalized}"

    return ELONGATED_LATIN_WORD_PATTERN.sub(replace_match, text)


class KeywordSentimentPredictor:
    def predict(self, texts: list[str]) -> list[dict[str, Union[int, str]]]:
        predictions = []
        for text in texts:
            normalized_text = (text or "").strip().lower()
            positive_score = sum(1 for keyword in POSITIVE_KEYWORDS if keyword in normalized_text)
            negative_score = sum(1 for keyword in NEGATIVE_KEYWORDS if keyword in normalized_text)

            if positive_score > negative_score:
                sentiment = "positive"
            elif negative_score > positive_score:
                sentiment = "negative"
            else:
                sentiment = "neutral"

            total_hits = positive_score + negative_score
            if total_hits == 0:
                scaled_positive = 0
                scaled_negative = 0
            else:
                scaled_positive = int(round((positive_score / total_hits) * 100))
                scaled_negative = int(round((negative_score / total_hits) * 100))

            predictions.append(
                {
                    "positive_score": scaled_positive,
                    "negative_score": scaled_negative,
                    "sentiment": sentiment,
                }
            )
        return predictions


class TransformerSentimentPredictor:
    def __init__(self, model_name: str, batch_size: int, max_length: int) -> None:
        from transformers import pipeline

        logger.info("Loading transformer sentiment model: %s", model_name)
        self.model_name = model_name
        self.batch_size = batch_size
        self.max_length = max_length
        self.pipeline = pipeline(
            "text-classification",
            model=model_name,
            tokenizer=model_name,
            framework="pt",
            device=-1,
            top_k=None,
        )
        logger.info("Transformer sentiment model loaded successfully")

    def predict(self, texts: list[str]) -> list[dict[str, Union[int, str]]]:
        predictions = []

        for index in range(0, len(texts), self.batch_size):
            batch_texts = texts[index : index + self.batch_size]
            outputs = self.pipeline(
                batch_texts,
                truncation=True,
                max_length=self.max_length,
            )

            for output in outputs:
                scores = {"positive": 0.0, "neutral": 0.0, "negative": 0.0}
                for item in output:
                    normalized_label = normalize_label(item["label"])
                    scores[normalized_label] = float(item["score"])

                sentiment = max(scores, key=scores.get)
                predictions.append(
                    {
                        "positive_score": int(round(scores["positive"] * 100)),
                        "negative_score": int(round(scores["negative"] * 100)),
                        "sentiment": sentiment,
                    }
                )

        return predictions


def get_sentiment_predictor():
    global _SENTIMENT_PREDICTOR

    if _SENTIMENT_PREDICTOR is not None:
        return _SENTIMENT_PREDICTOR

    if SENTIMENT_MODE == "keyword":
        logger.info("SENTIMENT_MODE=keyword, using keyword baseline")
        _SENTIMENT_PREDICTOR = KeywordSentimentPredictor()
        return _SENTIMENT_PREDICTOR

    try:
        _SENTIMENT_PREDICTOR = TransformerSentimentPredictor(
            model_name=SENTIMENT_MODEL_NAME,
            batch_size=SENTIMENT_BATCH_SIZE,
            max_length=SENTIMENT_MAX_LENGTH,
        )
        return _SENTIMENT_PREDICTOR
    except Exception as exc:
        if not SENTIMENT_FALLBACK_TO_KEYWORD:
            raise
        logger.warning(
            "Failed to initialize transformer model %s. Falling back to keyword baseline. Error: %s",
            SENTIMENT_MODEL_NAME,
            exc,
        )
        _SENTIMENT_PREDICTOR = KeywordSentimentPredictor()
        return _SENTIMENT_PREDICTOR


def build_clean_stream(bronze_stream: DataFrame) -> DataFrame:
    cleaned = (
        bronze_stream.withColumn("comment_id", normalize_blank_string(col("comment_id")))
        .withColumn("video_id", normalize_blank_string(col("video_id")))
        .withColumn("author", normalize_blank_string(col("author"), "unknown"))
        .withColumn("text", normalize_blank_string(col("text")))
        .withColumn("is_reply", when(col("is_reply").isNull(), lit(False)).otherwise(col("is_reply")))
        .withColumn("parent_comment_id", normalize_blank_string(col("parent_comment_id")))
        .withColumn("lang", lower(normalize_blank_string(col("lang"), "unknown")))
        .withColumn("source", lower(normalize_blank_string(col("source"), "unknown")))
        .withColumn("like_count", sanitize_non_negative_int(col("like_count")))
        .withColumn("reply_count", sanitize_non_negative_int(col("reply_count")))
        .withColumn("collected_at", when(col("collected_at").isNull(), col("event_time")).otherwise(col("collected_at")))
        .withColumn("collected_at", greatest(col("collected_at"), col("event_time")))
        .withColumn(
            "parent_comment_id",
            when(col("is_reply") == lit(False), lit(None)).otherwise(col("parent_comment_id")),
        )
        .withColumn("text_clean", normalize_text(col("text")))
        .withColumn("text_length", length(col("text_clean")))
        .withColumn(
            "collected_delay_seconds",
            unix_timestamp(col("collected_at")) - unix_timestamp(col("event_time")),
        )
        .filter(col("event_time").isNotNull())
        .filter(col("collected_at").isNotNull())
        .filter(col("comment_id").isNotNull())
        .filter(col("video_id").isNotNull())
        .filter(col("text").isNotNull())
        .filter(length(col("text_clean")) > 0)
        .filter((col("is_reply") == lit(False)) | col("parent_comment_id").isNotNull())
        .withColumn("silver_processed_at", current_timestamp())
    )

    return cleaned.withWatermark("collected_at", "2 days").dropDuplicates(["video_id", "comment_id"])


def score_batch(batch_df: DataFrame, epoch_id: int, silver_path: str, prediction_schema: StructType) -> None:
    batch_rows = batch_df.select("video_id", "comment_id", "text_clean").collect()
    if not batch_rows:
        logger.info("Epoch %s has no records after deduplication", epoch_id)
        return

    predictor = get_sentiment_predictor()
    slang_lexicon = get_slang_lexicon()
    texts = [apply_slang_lexicon(row["text_clean"], slang_lexicon) for row in batch_rows]
    predictions = predictor.predict(texts)

    prediction_rows = []
    for row, prediction in zip(batch_rows, predictions):
        prediction_rows.append(
            (
                row["video_id"],
                row["comment_id"],
                int(prediction["positive_score"]),
                int(prediction["negative_score"]),
                str(prediction["sentiment"]),
            )
        )

    prediction_df = batch_df.sparkSession.createDataFrame(prediction_rows, schema=prediction_schema)
    scored_df = batch_df.join(prediction_df, on=["video_id", "comment_id"], how="inner")

    logger.info(
        "Writing epoch %s to Silver with %s rows using sentiment mode %s",
        epoch_id,
        len(prediction_rows),
        SENTIMENT_MODE,
    )
    scored_df.write.format("delta").mode("append").save(silver_path)


def main() -> None:
    spark = create_spark()
    bronze_schema = build_schema()
    prediction_schema = build_prediction_schema()
    silver_schema = build_silver_output_schema()

    bronze_path = "hdfs://namenode:8020/lake_delta/bronze/youtube_comments"
    silver_path = "hdfs://namenode:8020/lake_delta/silver/youtube_comments"
    checkpoint_path = "hdfs://namenode:8020/checkpoints_delta/silver_youtube_comments"

    ensure_delta_table(spark, bronze_path, bronze_schema)
    ensure_delta_table(spark, silver_path, silver_schema)
    bronze_stream = spark.readStream.format("delta").load(bronze_path)
    cleaned_stream = build_clean_stream(bronze_stream)

    (
        cleaned_stream.writeStream.foreachBatch(
            lambda batch_df, epoch_id: score_batch(
                batch_df=batch_df,
                epoch_id=epoch_id,
                silver_path=silver_path,
                prediction_schema=prediction_schema,
            )
        )
        .outputMode("append")
        .option("checkpointLocation", checkpoint_path)
        .start()
        .awaitTermination()
    )


if __name__ == "__main__":
    main()
