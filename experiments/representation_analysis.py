from __future__ import annotations

import re
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from experiments.article_extraction_poc import extract_article
from experiments.reading_decision_poc import (
    SUMMARY_SENTENCE_COUNT,
    count_words,
    first_meaningful_paragraph,
    lexrank_summary,
    lsa_summary,
    split_sentences,
    textrank_summary,
)


REPORT_PATH = Path("experiments/representation_analysis.md")
BENCHMARK_URLS = [
    (
        "Personal engineering blog",
        "https://www.joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i/",
    ),
    (
        "Company engineering blog",
        "https://github.blog/engineering/architecture-optimization/how-we-improved-push-processing-on-github/",
    ),
    (
        "Hacker News article",
        "https://europeancorrespondent.com/en/r/the-us-ambassador-had-belgian-police-stop-our-reporting",
    ),
    (
        "GitHub Pages article",
        "https://karpathy.github.io/2015/05/21/rnn-effectiveness/",
    ),
]


@dataclass(frozen=True)
class Representation:
    name: str
    text: str
    metrics: dict[str, object]
    observations: list[str]


def main() -> int:
    report = build_report()
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")
    return 0


def build_report() -> str:
    lines = [
        "# Representation Analysis",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "This isolated experiment reports structural metrics only. It does not rank methods, recommend a winner, or propose production changes.",
        "",
    ]

    for article_label, url in BENCHMARK_URLS:
        started_at = time.perf_counter()
        extraction = extract_article(url)
        extraction_time = round(time.perf_counter() - started_at, 3)
        title = extraction.get("title") or "(title not available)"
        text = extraction.get("text") or ""

        lines.extend(
            [
                f"## {article_label}",
                "",
                f"Article URL: {url}",
                "",
                f"Extraction succeeded: {extraction['success']}",
                f"Extraction time seconds: {extraction_time}",
                f"Extracted title: {title}",
                f"Extracted words: {count_words(text)}",
                f"Extracted characters: {len(text)}",
                "",
            ]
        )

        if extraction.get("error"):
            lines.extend([f"Extraction failure: {extraction['error']}", ""])

        for representation in build_representations(title, text, extraction_time):
            lines.extend(format_representation(representation))

    return "\n".join(lines)


def build_representations(
    title: str,
    article_text: str,
    extraction_time: float,
) -> list[Representation]:
    raw_representations = [
        ("A. Title", title),
        (
            "B. Title + first meaningful paragraph",
            join_parts(title, first_meaningful_paragraph(article_text)),
        ),
        (
            "C. Title + LSA summary",
            join_parts(title, lsa_summary(article_text, SUMMARY_SENTENCE_COUNT)),
        ),
        (
            "D. Title + LexRank summary",
            join_parts(title, lexrank_summary(article_text, SUMMARY_SENTENCE_COUNT)),
        ),
        (
            "E. Title + TextRank summary",
            join_parts(title, textrank_summary(article_text, SUMMARY_SENTENCE_COUNT)),
        ),
    ]

    representations: list[Representation] = []
    for name, output_text in raw_representations:
        metrics = compute_metrics(output_text, title, extraction_time)
        representations.append(
            Representation(
                name=name,
                text=output_text,
                metrics=metrics,
                observations=build_observations(metrics),
            )
        )

    return representations


def compute_metrics(
    output_text: str,
    title: str,
    extraction_time: float,
) -> dict[str, object]:
    sentences = split_sentences(output_text)
    duplicated_sentences = find_duplicated_sentences(sentences)

    return {
        "total_words": count_words(output_text),
        "total_characters": len(output_text),
        "sentence_count": len(sentences),
        "extraction_time_seconds": extraction_time,
        "duplicated_sentences": duplicated_sentences,
        "repeated_title_ratio": repeated_title_ratio(output_text, title),
        "code_blocks_dominate_output": code_blocks_dominate(output_text),
        "mathematical_expressions_dominate_output": math_expressions_dominate(output_text),
        "starts_with_article_context": starts_with_article_context(output_text, title),
    }


def format_representation(representation: Representation) -> list[str]:
    metrics = representation.metrics
    duplicated = metrics["duplicated_sentences"] or "none"
    if isinstance(duplicated, list):
        duplicated = "; ".join(duplicated)

    lines = [
        f"### {representation.name}",
        "",
        "Metrics:",
        "",
        f"- total words: {metrics['total_words']}",
        f"- total characters: {metrics['total_characters']}",
        f"- sentence count: {metrics['sentence_count']}",
        f"- extraction time seconds: {metrics['extraction_time_seconds']}",
        f"- duplicated sentences: {duplicated}",
        f"- repeated title ratio: {metrics['repeated_title_ratio']}",
        f"- code blocks dominate output: {metrics['code_blocks_dominate_output']}",
        f"- mathematical expressions dominate output: {metrics['mathematical_expressions_dominate_output']}",
        f"- starts with article context: {metrics['starts_with_article_context']}",
        "",
        "Actual text:",
        "",
        "```text",
        representation.text,
        "```",
        "",
        "Objective observations:",
        "",
    ]

    lines.extend(f"- {observation}" for observation in representation.observations)
    lines.append("")
    return lines


def build_observations(metrics: dict[str, object]) -> list[str]:
    observations: list[str] = []

    duplicated_sentences = metrics["duplicated_sentences"]
    if duplicated_sentences:
        observations.append("Contains duplicated sentences.")
    else:
        observations.append("No duplicated sentences detected.")

    if metrics["repeated_title_ratio"] == 0:
        observations.append("The exact title phrase was not repeated in the body portion.")
    elif metrics["repeated_title_ratio"] < 0.25:
        observations.append("The exact title phrase accounts for a minority of the output.")
    else:
        observations.append("The exact title phrase accounts for a substantial share of the output.")

    if metrics["code_blocks_dominate_output"]:
        observations.append("Code-like lines account for at least half of non-empty lines.")
    else:
        observations.append("Code-like lines do not dominate the output.")

    if metrics["mathematical_expressions_dominate_output"]:
        observations.append("Mathematical notation accounts for a large share of tokens.")
    else:
        observations.append("Mathematical notation does not dominate the output.")

    if metrics["starts_with_article_context"]:
        observations.append("After the title, the output begins with article context.")
    else:
        observations.append("After the title, article context is absent or not detected at the start.")

    return observations


def find_duplicated_sentences(sentences: list[str]) -> list[str]:
    normalized_to_original: dict[str, str] = {}
    counts: Counter[str] = Counter()

    for sentence in sentences:
        normalized = normalize_sentence(sentence)
        if not normalized:
            continue
        normalized_to_original.setdefault(normalized, sentence)
        counts[normalized] += 1

    return [
        normalized_to_original[normalized]
        for normalized, count in counts.items()
        if count > 1
    ]


def repeated_title_ratio(output_text: str, title: str) -> float:
    title_words = count_words(title)
    output_words = count_words(output_text)
    if title_words == 0 or output_words == 0:
        return 0.0

    occurrences = normalized_text(output_text).count(normalized_text(title))
    repeated_title_words = max(0, occurrences - 1) * title_words

    return round(repeated_title_words / output_words, 3)


def code_blocks_dominate(output_text: str) -> bool:
    lines = [line.strip() for line in output_text.splitlines() if line.strip()]
    if not lines:
        return False

    code_like_count = sum(1 for line in lines if is_code_like_line(line))
    return code_like_count / len(lines) >= 0.5


def math_expressions_dominate(output_text: str) -> bool:
    tokens = re.findall(r"\S+", output_text)
    if not tokens:
        return False

    math_tokens = [
        token
        for token in tokens
        if re.search(r"[∑√≈≤≥≠∞πλσµ]|[=+\-*/^<>]{1,}|\\[a-zA-Z]+", token)
    ]
    return len(math_tokens) / len(tokens) >= 0.25


def starts_with_article_context(output_text: str, title: str) -> bool:
    body = body_after_title(output_text, title)
    first_sentence = first_detected_sentence(body)

    return bool(first_sentence and count_words(first_sentence) >= 8)


def first_detected_sentence(text: str) -> str:
    sentences = split_sentences(text)
    if sentences:
        return sentences[0]

    return text.strip()


def body_after_title(output_text: str, title: str) -> str:
    stripped = output_text.strip()
    if not stripped:
        return ""

    if stripped.startswith(title):
        return stripped[len(title) :].strip()

    return stripped


def is_code_like_line(line: str) -> bool:
    if line.startswith(("def ", "class ", "import ", "from ", "const ", "let ", "var ")):
        return True

    if re.search(r"[{};]|=>|==|!=|:=|</?[A-Za-z][^>]*>", line):
        return True

    return line.startswith(("$ ", ">>> ", "... "))


def normalize_sentence(sentence: str) -> str:
    return normalized_text(sentence).strip(".!? ")


def normalized_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def join_parts(*parts: str) -> str:
    return "\n\n".join(part for part in parts if part)


if __name__ == "__main__":
    raise SystemExit(main())
