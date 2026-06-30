from __future__ import annotations

import argparse
import math
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass

from experiments.article_extraction_poc import extract_article


WORDS_PER_MINUTE = 220
SUMMARY_SENTENCE_COUNT = 3
LEXRANK_THRESHOLD = 0.1
STOPWORDS = {
    "a",
    "about",
    "after",
    "all",
    "also",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "because",
    "been",
    "but",
    "by",
    "can",
    "could",
    "for",
    "from",
    "had",
    "has",
    "have",
    "how",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "more",
    "not",
    "of",
    "on",
    "or",
    "our",
    "out",
    "so",
    "than",
    "that",
    "the",
    "their",
    "then",
    "there",
    "these",
    "they",
    "this",
    "to",
    "was",
    "we",
    "were",
    "what",
    "when",
    "which",
    "who",
    "will",
    "with",
    "would",
    "you",
    "your",
}


@dataclass(frozen=True)
class MethodOutput:
    method: str
    result: str
    processing_time_seconds: float
    failure: str = ""

    @property
    def word_count(self) -> int:
        return count_words(self.result)

    @property
    def reading_time(self) -> str:
        return estimate_reading_time(self.word_count)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare free article representations for reading decisions."
    )
    parser.add_argument("url", help="Article URL to compare")
    args = parser.parse_args()

    started_at = time.perf_counter()
    extraction = extract_article(args.url)
    extraction_time = time.perf_counter() - started_at

    outputs = build_outputs(extraction)
    print_outputs(args.url, extraction, extraction_time, outputs)

    return 0 if extraction["success"] else 1


def build_outputs(extraction: dict) -> list[MethodOutput]:
    title = extraction.get("title") or "(title not available)"
    description = extraction.get("meta_description") or ""
    text = extraction.get("text") or ""

    method_builders = [
        ("Output A: Title only", lambda: title),
        (
            "Output B: Title + meta description",
            lambda: join_parts(title, description or "(meta description not available)"),
        ),
        (
            "Output C: Title + first meaningful paragraph",
            lambda: join_parts(title, first_meaningful_paragraph(text)),
        ),
        (
            "Output D: Title + LSA extractive summary",
            lambda: join_parts(title, lsa_summary(text, SUMMARY_SENTENCE_COUNT)),
        ),
        (
            "Output E: Title + LexRank summary",
            lambda: join_parts(title, lexrank_summary(text, SUMMARY_SENTENCE_COUNT)),
        ),
        (
            "Output F: Title + TextRank summary",
            lambda: join_parts(title, textrank_summary(text, SUMMARY_SENTENCE_COUNT)),
        ),
    ]

    outputs: list[MethodOutput] = []
    for method, builder in method_builders:
        started_at = time.perf_counter()
        failure = ""
        try:
            result = builder()
        except Exception as exc:
            result = title
            failure = f"{type(exc).__name__}: {exc}"

        outputs.append(
            MethodOutput(
                method=method,
                result=result,
                processing_time_seconds=round(time.perf_counter() - started_at, 3),
                failure=failure,
            )
        )

    return outputs


def print_outputs(
    url: str,
    extraction: dict,
    extraction_time: float,
    outputs: list[MethodOutput],
) -> None:
    print("Reading Decision PoC")
    print("====================")
    print(f"URL: {url}")
    print()

    for output in outputs:
        print("=========================")
        print(output.method)
        print("=========================")
        print(f"Reading time estimate: {output.reading_time}")
        print(f"Word count: {output.word_count}")
        print()
        print("Result")
        print(output.result or "(not available)")
        if output.failure:
            print()
            print(f"Failure: {output.failure}")
        print()

    print("Objective Statistics")
    print("====================")
    print(f"Extraction succeeded: {extraction['success']}")
    print(f"Extraction time seconds: {round(extraction_time, 3)}")
    print(f"Extracted text length: {extraction['text_length']}")
    print(f"Extracted word count: {count_words(extraction.get('text') or '')}")
    if extraction.get("error"):
        print(f"Extraction failure: {extraction['error']}")

    for output in outputs:
        print(
            f"{output.method}: "
            f"summary_chars={len(output.result)} "
            f"summary_words={output.word_count} "
            f"processing_time_seconds={output.processing_time_seconds} "
            f"failure={output.failure or 'none'}"
        )


def first_meaningful_paragraph(text: str) -> str:
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n+", text)]
    paragraphs = [paragraph for paragraph in paragraphs if paragraph]
    if not paragraphs:
        return "(plain text not available)"

    for paragraph in paragraphs:
        if count_words(paragraph) >= 25:
            return paragraph

    return paragraphs[0]


def lsa_summary(text: str, sentence_count: int) -> str:
    sentences = split_sentences(text)
    if len(sentences) <= sentence_count:
        return join_sentences(sentences)

    vectors = build_tfidf_vectors(sentences)
    if not vectors:
        return join_sentences(sentences[:sentence_count])

    covariance = sentence_covariance(vectors)
    principal = power_iteration(covariance)
    ranked = sorted(
        range(len(sentences)),
        key=lambda index: abs(principal[index]),
        reverse=True,
    )

    return join_ranked_sentences(sentences, ranked, sentence_count)


def lexrank_summary(text: str, sentence_count: int) -> str:
    sentences = split_sentences(text)
    if len(sentences) <= sentence_count:
        return join_sentences(sentences)

    vectors = build_tfidf_vectors(sentences)
    if not vectors:
        return join_sentences(sentences[:sentence_count])

    graph = similarity_graph(vectors, threshold=LEXRANK_THRESHOLD)
    scores = pagerank(graph)
    ranked = sorted(range(len(sentences)), key=lambda index: scores[index], reverse=True)

    return join_ranked_sentences(sentences, ranked, sentence_count)


def textrank_summary(text: str, sentence_count: int) -> str:
    sentences = split_sentences(text)
    if len(sentences) <= sentence_count:
        return join_sentences(sentences)

    vectors = build_tfidf_vectors(sentences)
    if not vectors:
        return join_sentences(sentences[:sentence_count])

    graph = similarity_graph(vectors, threshold=0.0)
    scores = pagerank(graph)
    ranked = sorted(range(len(sentences)), key=lambda index: scores[index], reverse=True)

    return join_ranked_sentences(sentences, ranked, sentence_count)


def split_sentences(text: str) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []

    raw_sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])|(?<=。)\s*", normalized)
    sentences = [sentence.strip() for sentence in raw_sentences if sentence.strip()]
    return [sentence for sentence in sentences if count_words(sentence) >= 5]


def build_tfidf_vectors(sentences: list[str]) -> list[dict[str, float]]:
    tokenized = [tokenize(sentence) for sentence in sentences]
    document_frequency: Counter[str] = Counter()
    for tokens in tokenized:
        document_frequency.update(set(tokens))

    vectors: list[dict[str, float]] = []
    sentence_total = len(sentences)
    for tokens in tokenized:
        counts = Counter(tokens)
        if not counts:
            vectors.append({})
            continue

        token_total = sum(counts.values())
        vector: dict[str, float] = {}
        for token, count in counts.items():
            tf = count / token_total
            idf = math.log((1 + sentence_total) / (1 + document_frequency[token])) + 1
            vector[token] = tf * idf
        vectors.append(vector)

    return vectors


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]*", text.lower())
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


def sentence_covariance(vectors: list[dict[str, float]]) -> list[list[float]]:
    size = len(vectors)
    matrix = [[0.0 for _ in range(size)] for _ in range(size)]
    for row in range(size):
        for column in range(row, size):
            value = dot(vectors[row], vectors[column])
            matrix[row][column] = value
            matrix[column][row] = value
    return matrix


def similarity_graph(
    vectors: list[dict[str, float]],
    threshold: float,
) -> list[list[float]]:
    size = len(vectors)
    graph = [[0.0 for _ in range(size)] for _ in range(size)]
    for row in range(size):
        for column in range(size):
            if row == column:
                continue

            similarity = cosine(vectors[row], vectors[column])
            if similarity > threshold:
                graph[row][column] = similarity
    return graph


def power_iteration(matrix: list[list[float]], iterations: int = 50) -> list[float]:
    size = len(matrix)
    if size == 0:
        return []

    vector = [1.0 / size for _ in range(size)]
    for _ in range(iterations):
        next_vector = [
            sum(matrix[row][column] * vector[column] for column in range(size))
            for row in range(size)
        ]
        norm = math.sqrt(sum(value * value for value in next_vector))
        if norm == 0:
            return vector
        vector = [value / norm for value in next_vector]

    return vector


def pagerank(
    graph: list[list[float]],
    damping: float = 0.85,
    iterations: int = 40,
) -> list[float]:
    size = len(graph)
    if size == 0:
        return []

    scores = [1.0 / size for _ in range(size)]
    for _ in range(iterations):
        next_scores = [(1.0 - damping) / size for _ in range(size)]
        for source, edges in enumerate(graph):
            edge_total = sum(edges)
            if edge_total == 0:
                share = damping * scores[source] / size
                for target in range(size):
                    next_scores[target] += share
                continue

            for target, weight in enumerate(edges):
                if weight:
                    next_scores[target] += damping * scores[source] * (weight / edge_total)

        scores = next_scores

    return scores


def join_ranked_sentences(
    sentences: list[str],
    ranked_indexes: list[int],
    sentence_count: int,
) -> str:
    selected = sorted(ranked_indexes[:sentence_count])
    return join_sentences([sentences[index] for index in selected])


def join_sentences(sentences: list[str]) -> str:
    return " ".join(sentences) if sentences else "(plain text not available)"


def join_parts(*parts: str) -> str:
    return "\n\n".join(part for part in parts if part)


def dot(left: dict[str, float], right: dict[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left

    return sum(value * right.get(token, 0.0) for token, value in left.items())


def cosine(left: dict[str, float], right: dict[str, float]) -> float:
    denominator = vector_norm(left) * vector_norm(right)
    if denominator == 0:
        return 0.0

    return dot(left, right) / denominator


def vector_norm(vector: dict[str, float]) -> float:
    return math.sqrt(sum(value * value for value in vector.values()))


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def estimate_reading_time(word_count: int) -> str:
    if word_count == 0:
        return "0 min"

    minutes = max(1, math.ceil(word_count / WORDS_PER_MINUTE))
    return f"{minutes} min"


if __name__ == "__main__":
    sys.exit(main())
