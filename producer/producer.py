import json
import os
import time

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable


def getenv(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value else default


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


def stream_file_once(producer: KafkaProducer, topic: str, data_path: str, replay_delay_ms: int) -> int:
    sent_count = 0

    with open(data_path, "r", encoding="utf-8") as source:
        for line in source:
            line = line.strip()
            if not line:
                continue

            payload = json.loads(line)
            key = payload.get("comment_id", "no-key")
            producer.send(topic, key=key, value=payload)
            producer.flush()
            sent_count += 1
            time.sleep(replay_delay_ms / 1000.0)

    return sent_count


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


def run_youtube_api_mode() -> None:
    raise NotImplementedError(
        "INGESTION_MODE=youtube_api chua duoc hoan thien. Nguoi A se phat trien phan nay."
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
        run_youtube_api_mode()
        return

    raise ValueError(
        f"INGESTION_MODE khong hop le: {ingestion_mode}. Gia tri hop le hien tai: sample, youtube_api"
    )


if __name__ == "__main__":
    main()
