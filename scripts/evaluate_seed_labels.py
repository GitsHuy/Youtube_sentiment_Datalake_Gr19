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


def load_slang_lexicon(path: str | None) -> list[dict]:
    if not path:
        return []

    lexicon_path = Path(path)
    if not lexicon_path.exists():
        raise FileNotFoundError(f"Slang lexicon file not found: {path}")

    raw_entries = json.loads(lexicon_path.read_text(encoding="utf-8"))
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
    return prepared_entries


def apply_slang_lexicon(text: str, lexicon_entries: list[dict]) -> str:
    if not lexicon_entries:
        return text

    updated_text = decode_unicode_escapes(text)
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


def normalize_text(text: str, lexicon_entries: list[dict] | None = None) -> str:
    text = text or ""
    text = decode_unicode_escapes(text)
    text = text.lower()
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = expand_elongated_latin_words(text)
    text = apply_slang_lexicon(text.strip(), lexicon_entries or [])
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


def load_rows(csv_path: Path, label_column: str, lexicon_entries: list[dict]) -> list[dict[str, str]]:
    rows = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if not row.get(label_column):
                raise ValueError(f"Missing label in column '{label_column}' for row idx={row.get('idx', 'unknown')}")
            row["text_clean"] = normalize_text(row["text"], lexicon_entries=lexicon_entries)
            row["actual_label"] = normalize_label(row[label_column])
            rows.append(row)
    return rows


def build_metrics(predictions: list[dict[str, str]]) -> dict:
    total = len(predictions)
    correct = sum(1 for item in predictions if item["actual_label"] == item["predicted_label"])

    by_review = defaultdict(lambda: {"total": 0, "correct": 0})
    confusion = defaultdict(Counter)
    actual_distribution = Counter()
    predicted_distribution = Counter()

    for item in predictions:
        actual_label = item["actual_label"]
        predicted = item["predicted_label"]
        review_needed = item["review_bucket"]

        actual_distribution[actual_label] += 1
        predicted_distribution[predicted] += 1
        confusion[actual_label][predicted] += 1
        by_review[review_needed]["total"] += 1
        if actual_label == predicted:
            by_review[review_needed]["correct"] += 1

    mismatches = [item for item in predictions if item["actual_label"] != item["predicted_label"]]
    mismatches.sort(key=lambda item: (item["review_bucket"] != "reviewed", float(item["predicted_confidence"])))

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
            "support": actual_distribution[label],
        }

    macro_f1 = sum(item["f1_score"] for item in label_metrics.values()) / len(label_metrics)

    return {
        "total_rows": total,
        "correct_rows": correct,
        "agreement_accuracy": (correct / total) if total else 0.0,
        "actual_distribution": dict(actual_distribution),
        "predicted_distribution": dict(predicted_distribution),
        "accuracy_by_review_bucket": accuracy_by_review,
        "label_metrics": label_metrics,
        "macro_f1": macro_f1,
        "confusion_matrix": {
            actual_label: {
                "positive": confusion[actual_label]["positive"],
                "neutral": confusion[actual_label]["neutral"],
                "negative": confusion[actual_label]["negative"],
            }
            for actual_label in ["positive", "neutral", "negative"]
        },
        "mismatch_count": len(mismatches),
        "top_mismatches": mismatches[:20],
    }


def keyword_predict(text: str) -> dict[str, float | str]:
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
        confidence = 0.0
    else:
        confidence = max(positive_score, negative_score) / total_hits

    return {
        "predicted_label": sentiment,
        "predicted_confidence": confidence,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate sentiment predictions against labeled CSV data.")
    parser.add_argument("--input", default="data/evaluation/assistant_seed_labels_100.csv")
    parser.add_argument("--output", default="data/evaluation/model_vs_seed_labels_100.csv")
    parser.add_argument("--summary", default="data/evaluation/model_vs_seed_labels_100_summary.json")
    parser.add_argument("--label-column", default="assistant_seed_label")
    parser.add_argument("--notes-column", default="notes")
    parser.add_argument("--review-column", default="review_needed")
    parser.add_argument("--mode", choices=["transformer", "keyword"], default="transformer")
    parser.add_argument("--slang-lexicon", default="")
    parser.add_argument(
        "--model",
        default="cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual",
    )
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=256)
    args = parser.parse_args()

    lexicon_entries = load_slang_lexicon(args.slang_lexicon)
    rows = load_rows(Path(args.input), label_column=args.label_column, lexicon_entries=lexicon_entries)
    print(f"Loaded rows: {len(rows)}")
    if lexicon_entries:
        print(f"Loaded slang lexicon entries: {len(lexicon_entries)} from {args.slang_lexicon}")

    classifier = None
    if args.mode == "transformer":
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
    else:
        print("Using keyword baseline for evaluation")

    predictions = []
    for start_index in range(0, len(rows), args.batch_size):
        batch_rows = rows[start_index : start_index + args.batch_size]

        if args.mode == "transformer":
            outputs = classifier(
                [row["text_clean"] for row in batch_rows],
                truncation=True,
                max_length=args.max_length,
            )
        else:
            outputs = [keyword_predict(row["text_clean"]) for row in batch_rows]

        for row, output in zip(batch_rows, outputs):
            if args.mode == "transformer":
                scores = {"positive": 0.0, "neutral": 0.0, "negative": 0.0}
                for item in output:
                    scores[normalize_label(item["label"])] = float(item["score"])
                predicted_label = max(scores, key=scores.get)
                predicted_confidence = scores[predicted_label]
            else:
                predicted_label = str(output["predicted_label"])
                predicted_confidence = float(output["predicted_confidence"])

            review_value = str(row.get(args.review_column, "") or "").strip()
            review_bucket = review_value if review_value else "unbucketed"
            notes_value = row.get(args.notes_column, "")

            predictions.append(
                {
                    "idx": row["idx"],
                    "comment_id": row["comment_id"],
                    "video_id": row["video_id"],
                    "text": row["text"],
                    "actual_label": row["actual_label"],
                    "review_bucket": review_bucket,
                    "notes": notes_value,
                    "predicted_label": predicted_label,
                    "predicted_confidence": f"{predicted_confidence:.6f}",
                    "is_match": "yes" if row["actual_label"] == predicted_label else "no",
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
                "actual_label",
                "review_bucket",
                "notes",
                "predicted_label",
                "predicted_confidence",
                "is_match",
            ],
        )
        writer.writeheader()
        writer.writerows(predictions)

    summary = build_metrics(predictions)
    summary["evaluation_mode"] = args.mode
    summary["input_file"] = args.input
    summary["label_column"] = args.label_column
    summary["slang_lexicon"] = args.slang_lexicon or None
    if args.mode == "transformer":
        summary["model_name"] = args.model
    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Saved detailed predictions to: {output_path}")
    print(f"Saved summary to: {summary_path}")


if __name__ == "__main__":
    main()
