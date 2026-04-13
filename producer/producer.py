import json
import os
import time
from datetime import datetime, timezone
from html import unescape
from typing import Iterable
from urllib.parse import parse_qs, urlparse

import requests
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable


YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
REQUIRED_FIELDS = (
    "event_time",
    "collected_at",
    "comment_id",
    "video_id",
    "author",
    "text",
    "like_count",
    "reply_count",
    "is_reply",
    "source",
)


def getenv(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value else default


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
        key_serializer=lambda key: key.encode("utf-8"),
        value_serializer=lambda value: json.dumps(value, ensure_ascii=True).encode("utf-8"),
        acks="all",
        linger_ms=50,
    )


def wait_for_kafka(retry_delay_seconds: int) -> KafkaProducer:
    while True:
        try:
            producer = create_producer()
            producer.bootstrap_connected()
            print("Kafka is ready. Producer connected.", flush=True)
            return producer
        except NoBrokersAvailable:
            print(
                f"Kafka is not ready yet. Retrying in {retry_delay_seconds} seconds...",
                flush=True,
            )
            time.sleep(retry_delay_seconds)


def str_to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return str_to_bool(value)
    return bool(value)


def normalize_record(payload: dict, default_source: str) -> dict:
    normalized = dict(payload)
    normalized["collected_at"] = normalized.get("collected_at") or normalized.get("event_time")
    normalized["source"] = normalized.get("source") or default_source
    normalized["parent_comment_id"] = normalized.get("parent_comment_id")
    normalized["lang"] = normalized.get("lang") or "unknown"
    normalized["like_count"] = int(normalized.get("like_count") or 0)
    normalized["reply_count"] = int(normalized.get("reply_count") or 0)
    normalized["is_reply"] = to_bool(normalized.get("is_reply"))
    normalized["text"] = str(normalized.get("text", "")).strip()
    return normalized


def validate_record(payload: dict, expected_video_id: str | None) -> None:
    missing_fields = [field for field in REQUIRED_FIELDS if payload.get(field) in (None, "")]
    if missing_fields:
        raise ValueError(f"Ban ghi thieu truong bat buoc: {', '.join(missing_fields)}")

    if payload["collected_at"] < payload["event_time"]:
        raise ValueError(
            f"Ban ghi {payload['comment_id']} co collected_at nho hon event_time, khong hop le"
        )

    if not payload["is_reply"] and payload.get("parent_comment_id") not in (None, ""):
        raise ValueError(
            f"Ban ghi {payload['comment_id']} khong phai reply nhung lai co parent_comment_id"
        )

    if payload["is_reply"] and not payload.get("parent_comment_id"):
        raise ValueError(f"Ban ghi {payload['comment_id']} la reply nhung thieu parent_comment_id")

    if expected_video_id and payload["video_id"] != expected_video_id:
        raise ValueError(
            f"Ban ghi {payload['comment_id']} co video_id={payload['video_id']} khong khop YOUTUBE_VIDEO_ID={expected_video_id}"
        )


def send_records(
    producer: KafkaProducer,
    topic: str,
    records: Iterable[dict],
    expected_video_id: str | None,
    replay_delay_ms: int,
    skip_invalid_records: bool = False,
) -> int:
    sent_count = 0
    skipped_count = 0

    for raw_payload in records:
        payload = normalize_record(raw_payload, default_source=raw_payload.get("source", "unknown"))
        try:
            validate_record(payload, expected_video_id)
        except ValueError as exc:
            if not skip_invalid_records:
                raise

            skipped_count += 1
            print(
                f"Skipping invalid record {payload.get('comment_id', 'unknown')}: {exc}",
                flush=True,
            )
            continue
        key = payload.get("comment_id", "no-key")
        producer.send(topic, key=key, value=payload)
        producer.flush()
        sent_count += 1

        if replay_delay_ms > 0:
            time.sleep(replay_delay_ms / 1000.0)

    if skipped_count > 0:
        print(f"Skipped {skipped_count} invalid record(s) during ingestion.", flush=True)

    return sent_count


def stream_file_once(producer: KafkaProducer, topic: str, data_path: str, replay_delay_ms: int) -> int:
    expected_video_id = normalize_video_id_input(getenv("YOUTUBE_VIDEO_ID", "").strip()) or None
    records = []

    with open(data_path, "r", encoding="utf-8") as source:
        for line in source:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))

    return send_records(producer, topic, records, expected_video_id, replay_delay_ms)


def run_sample_mode(producer: KafkaProducer, topic: str, data_path: str, replay_delay_ms: int) -> None:
    sample_loop = str_to_bool(getenv("SAMPLE_LOOP", "false"))

    while True:
        sent_count = stream_file_once(producer, topic, data_path, replay_delay_ms)
        print(f"Sample mode sent {sent_count} records from {data_path}.", flush=True)

        if not sample_loop:
            print(
                "Sample mode is configured to run once. Producer will stop here to avoid duplicate data.",
                flush=True,
            )
            return

        print("Sample loop is enabled. Replaying the sample file again.", flush=True)


def require_env(name: str) -> str:
    value = getenv(name, "").strip()
    if not value:
        raise ValueError(f"Can thiet lap bien moi truong {name} de dung youtube_api mode")
    return value


def normalize_video_id_input(raw_value: str) -> str:
    value = raw_value.strip()
    if not value:
        return value

    if "youtube.com" in value or "youtu.be" in value:
        parsed = urlparse(value)
        if "youtu.be" in parsed.netloc:
            return parsed.path.strip("/").split("/")[0]

        query_video_id = parse_qs(parsed.query).get("v", [""])[0]
        if query_video_id:
            return query_video_id

    for separator in ("&", "?"):
        if separator in value:
            value = value.split(separator, 1)[0]

    return value.strip()


def youtube_text(snippet: dict) -> str:
    return unescape((snippet.get("textOriginal") or snippet.get("textDisplay") or "").strip())


def build_top_level_record(thread_item: dict, collected_at: str, expected_video_id: str) -> dict:
    top_level = thread_item["snippet"]["topLevelComment"]
    snippet = top_level["snippet"]
    return {
        "event_time": snippet["publishedAt"],
        "collected_at": collected_at,
        "comment_id": top_level["id"],
        "video_id": snippet.get("videoId") or expected_video_id,
        "author": snippet.get("authorDisplayName", "unknown"),
        "text": youtube_text(snippet),
        "like_count": snippet.get("likeCount", 0),
        "reply_count": thread_item["snippet"].get("totalReplyCount", 0),
        "is_reply": False,
        "parent_comment_id": None,
        "lang": "unknown",
        "source": "youtube_api",
    }


def build_reply_record(reply_item: dict, collected_at: str, expected_video_id: str) -> dict:
    snippet = reply_item["snippet"]
    return {
        "event_time": snippet["publishedAt"],
        "collected_at": collected_at,
        "comment_id": reply_item["id"],
        "video_id": snippet.get("videoId") or expected_video_id,
        "author": snippet.get("authorDisplayName", "unknown"),
        "text": youtube_text(snippet),
        "like_count": snippet.get("likeCount", 0),
        "reply_count": 0,
        "is_reply": True,
        "parent_comment_id": snippet.get("parentId"),
        "lang": "unknown",
        "source": "youtube_api",
    }


def fetch_youtube_comment_pages(
    api_key: str,
    video_id: str,
    order: str,
    max_results: int,
    page_limit: int,
    retry_delay_seconds: int,
) -> Iterable[dict]:
    session = requests.Session()
    next_page_token = None
    pages_fetched = 0

    while pages_fetched < page_limit:
        params = {
            "part": "snippet,replies",
            "videoId": video_id,
            "maxResults": max_results,
            "order": order,
            "textFormat": "plainText",
            "key": api_key,
        }

        if next_page_token:
            params["pageToken"] = next_page_token

        for attempt in range(1, 4):
            response = session.get(YOUTUBE_API_URL, params=params, timeout=30)
            if response.status_code in {429, 500, 502, 503, 504} and attempt < 3:
                print(
                    f"YouTube API tam thoi loi {response.status_code}. Thu lai sau {retry_delay_seconds} giay.",
                    flush=True,
                )
                time.sleep(retry_delay_seconds)
                continue

            response.raise_for_status()
            page = response.json()
            yield page
            break

        pages_fetched += 1
        next_page_token = page.get("nextPageToken")
        if not next_page_token:
            return


def extract_youtube_records(pages: Iterable[dict], expected_video_id: str) -> list[dict]:
    collected_at = utc_now_iso()
    records = []

    for page in pages:
        for item in page.get("items", []):
            records.append(build_top_level_record(item, collected_at, expected_video_id))
            for reply in item.get("replies", {}).get("comments", []):
                records.append(build_reply_record(reply, collected_at, expected_video_id))

    return records


def run_youtube_api_mode(producer: KafkaProducer, topic: str) -> None:
    api_key = require_env("YOUTUBE_API_KEY")
    raw_video_id = require_env("YOUTUBE_VIDEO_ID")
    video_id = normalize_video_id_input(raw_video_id)
    order = getenv("YOUTUBE_ORDER", "time").strip().lower()
    max_results = int(getenv("YOUTUBE_MAX_RESULTS", "100"))
    page_limit = int(getenv("YOUTUBE_PAGE_LIMIT", "5"))
    retry_delay_seconds = int(getenv("YOUTUBE_RETRY_DELAY_SECONDS", "5"))
    publish_delay_ms = int(getenv("YOUTUBE_PUBLISH_DELAY_MS", "0"))

    if not video_id:
        raise ValueError("Khong the chuan hoa YOUTUBE_VIDEO_ID thanh video id hop le")

    if max_results < 1 or max_results > 100:
        raise ValueError("YOUTUBE_MAX_RESULTS phai nam trong khoang 1..100")

    if page_limit < 1:
        raise ValueError("YOUTUBE_PAGE_LIMIT phai lon hon 0")

    pages = fetch_youtube_comment_pages(
        api_key=api_key,
        video_id=video_id,
        order=order,
        max_results=max_results,
        page_limit=page_limit,
        retry_delay_seconds=retry_delay_seconds,
    )
    records = extract_youtube_records(pages, expected_video_id=video_id)

    if not records:
        print("Khong lay duoc comment nao tu YouTube API.", flush=True)
        return

    sent_count = send_records(
        producer=producer,
        topic=topic,
        records=records,
        expected_video_id=video_id,
        replay_delay_ms=publish_delay_ms,
        skip_invalid_records=True,
    )
    print(
        f"YouTube API mode sent {sent_count} records for video_id={video_id}.",
        flush=True,
    )


def main() -> None:
    retry_delay_seconds = int(getenv("KAFKA_RETRY_DELAY_SECONDS", "5"))
    producer = wait_for_kafka(retry_delay_seconds)
    topic = getenv("KAFKA_TOPIC", "youtube-comments")
    data_path = getenv("SAMPLE_DATA_PATH", "/data/sample_comments.jsonl")
    replay_delay_ms = int(getenv("REPLAY_DELAY_MS", "300"))
    ingestion_mode = getenv("INGESTION_MODE", "sample").strip().lower()

    if ingestion_mode == "sample":
        run_sample_mode(producer, topic, data_path, replay_delay_ms)
        return

    if ingestion_mode == "youtube_api":
        run_youtube_api_mode(producer, topic)
        return

    raise ValueError(
        f"INGESTION_MODE khong hop le: {ingestion_mode}. Gia tri hop le hien tai: sample, youtube_api"
    )


if __name__ == "__main__":
    main()
