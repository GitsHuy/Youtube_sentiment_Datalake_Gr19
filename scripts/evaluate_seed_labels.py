import argparse
import csv
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path


os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from transformers import pipeline


def normalize_text(text: str) -> str:
    text = text or ""
    text = text.lower()
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


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


def load_rows(csv_path: Path) -> list[dict[str, str]]:
    rows = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row["text_clean"] = normalize_text(row["text"])
            rows.append(row)
    return rows


def build_metrics(predictions: list[dict[str, str]]) -> dict:
    total = len(predictions)
    correct = sum(1 for item in predictions if item["assistant_seed_label"] == item["predicted_label"])

    by_review = defaultdict(lambda: {"total": 0, "correct": 0})
    confusion = defaultdict(Counter)
    seed_distribution = Counter()
    predicted_distribution = Counter()

    for item in predictions:
        seed = item["assistant_seed_label"]
        predicted = item["predicted_label"]
        review_needed = item["review_needed"]

        seed_distribution[seed] += 1
        predicted_distribution[predicted] += 1
        confusion[seed][predicted] += 1
        by_review[review_needed]["total"] += 1
        if seed == predicted:
            by_review[review_needed]["correct"] += 1

    mismatches = [item for item in predictions if item["assistant_seed_label"] != item["predicted_label"]]
    mismatches.sort(key=lambda item: (item["review_needed"] != "no", float(item["predicted_confidence"])))

    accuracy_by_review = {}
    for key, value in by_review.items():
        accuracy_by_review[key] = {
            "total": value["total"],
            "correct": value["correct"],
            "accuracy": (value["correct"] / value["total"]) if value["total"] else 0.0,
        }

    label_metrics = {}
    labels = ["positive", "neutral", "negative"]
    for label in labels:
        true_positive = confusion[label][label]
        false_positive = sum(confusion[other][label] for other in labels if other != label)
        false_negative = sum(confusion[label][other] for other in labels if other != label)

        precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) else 0.0
        recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) else 0.0
        f1_score = (
            2 * precision * recall / (precision + recall)
            if (precision + recall)
            else 0.0
        )

        label_metrics[label] = {
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "support": seed_distribution[label],
        }

    macro_f1 = sum(item["f1_score"] for item in label_metrics.values()) / len(label_metrics)

    return {
        "total_rows": total,
        "correct_rows": correct,
        "agreement_accuracy": (correct / total) if total else 0.0,
        "seed_distribution": dict(seed_distribution),
        "predicted_distribution": dict(predicted_distribution),
        "accuracy_by_review_needed": accuracy_by_review,
        "label_metrics": label_metrics,
        "macro_f1": macro_f1,
        "confusion_matrix": {
            seed: {
                "positive": confusion[seed]["positive"],
                "neutral": confusion[seed]["neutral"],
                "negative": confusion[seed]["negative"],
            }
            for seed in ["positive", "neutral", "negative"]
        },
        "mismatch_count": len(mismatches),
        "top_mismatches": mismatches[:20],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate transformer sentiment model against assistant seed labels.")
    parser.add_argument("--input", default="data/evaluation/assistant_seed_labels_100.csv")
    parser.add_argument("--output", default="data/evaluation/model_vs_seed_labels_100.csv")
    parser.add_argument("--summary", default="data/evaluation/model_vs_seed_labels_100_summary.json")
    parser.add_argument(
        "--model",
        default="cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual",
    )
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=256)
    args = parser.parse_args()

    rows = load_rows(Path(args.input))
    print(f"Loaded rows: {len(rows)}")
    print(f"Loading model: {args.model}")

    classifier = pipeline(
        "text-classification",
        model=args.model,
        tokenizer=args.model,
        framework="pt",
        device=-1,
        top_k=None,
    )
    print("Model loaded successfully")

    predictions = []
    for start_index in range(0, len(rows), args.batch_size):
        batch_rows = rows[start_index : start_index + args.batch_size]
        outputs = classifier(
            [row["text_clean"] for row in batch_rows],
            truncation=True,
            max_length=args.max_length,
        )

        for row, output in zip(batch_rows, outputs):
            scores = {"positive": 0.0, "neutral": 0.0, "negative": 0.0}
            for item in output:
                scores[normalize_label(item["label"])] = float(item["score"])

            predicted_label = max(scores, key=scores.get)
            predictions.append(
                {
                    "idx": row["idx"],
                    "comment_id": row["comment_id"],
                    "video_id": row["video_id"],
                    "text": row["text"],
                    "assistant_seed_label": row["assistant_seed_label"],
                    "review_needed": row["review_needed"],
                    "notes": row["notes"],
                    "predicted_label": predicted_label,
                    "predicted_confidence": f"{scores[predicted_label]:.6f}",
                    "is_match": "yes" if row["assistant_seed_label"] == predicted_label else "no",
                }
            )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "idx",
                "comment_id",
                "video_id",
                "text",
                "assistant_seed_label",
                "review_needed",
                "notes",
                "predicted_label",
                "predicted_confidence",
                "is_match",
            ],
        )
        writer.writeheader()
        writer.writerows(predictions)

    summary = build_metrics(predictions)
    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Saved detailed predictions to: {output_path}")
    print(f"Saved summary to: {summary_path}")


if __name__ == "__main__":
    main()
