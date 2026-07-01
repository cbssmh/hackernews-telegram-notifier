from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from typing import Any
from urllib.parse import urlparse

import requests
import trafilatura

from src.hn_client import parse_comment_text
from src.reading_decision import (
    build_hn_insight,
    calculate_reading_time_minutes,
    classify_source_type,
    clean_comment_text,
    truncate_text,
)


TARGET_STORY_COUNT = 100
HN_TIMEOUT_SECONDS = 10
ARTICLE_TIMEOUT_SECONDS = 12
COMMENT_SCAN_LIMIT = 5
USER_AGENT = "hackernews-telegram-notifier/operational-readiness-benchmark"
HN_ENDPOINTS = ("topstories", "beststories", "newstories")

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "operational_readiness_benchmark.csv"
REPORT_PATH = BASE_DIR / "operational_readiness_report.md"

CSV_FIELDS = (
    "story_id",
    "title",
    "url",
    "domain",
    "hn_score",
    "hn_comment_count",
    "http_status",
    "fetch_success",
    "extraction_success",
    "extracted_text_length",
    "word_count",
    "reading_time_minutes",
    "preview_candidate_exists",
    "preview_candidate_length",
    "published_date_found",
    "meta_description_found",
    "source_type",
    "top_comment_available",
    "top_comment_length",
    "hn_insight_candidate_exists",
    "failure_reason",
    "elapsed_seconds",
)


@dataclass(frozen=True)
class StoryCandidate:
    endpoint: str
    story_id: int
    title: str
    url: str
    domain: str
    score: int
    descendants: int
    kids: tuple[int, ...]


@dataclass(frozen=True)
class ArticleResult:
    http_status: int | None
    fetch_success: bool
    extraction_success: bool
    text: str
    word_count: int
    published_date: str
    meta_description: str
    failure_reason: str
    error_message: str


@dataclass(frozen=True)
class CommentResult:
    available: bool
    text: str
    insight_exists: bool


def main() -> None:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    started_at = time.perf_counter()
    stories, skipped = collect_story_candidates(session, TARGET_STORY_COUNT)

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []

    with CSV_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
        writer.writeheader()

        for index, story in enumerate(stories, start=1):
            print(f"[{index}/{len(stories)}] {story.domain} {story.story_id}")
            row, detail = benchmark_story(session, story)
            rows.append(row)
            details.append(detail)
            writer.writerow(row)
            csv_file.flush()

    total_elapsed = time.perf_counter() - started_at
    report = build_report(
        rows=rows,
        details=details,
        skipped=skipped,
        source_endpoints=HN_ENDPOINTS,
        total_elapsed=total_elapsed,
    )
    REPORT_PATH.write_text(report, encoding="utf-8")

    print(f"Wrote {CSV_PATH}")
    print(f"Wrote {REPORT_PATH}")


def collect_story_candidates(
    session: requests.Session,
    target_count: int,
) -> tuple[list[StoryCandidate], Counter[str]]:
    stories: list[StoryCandidate] = []
    skipped: Counter[str] = Counter()
    seen_story_ids: set[int] = set()
    seen_urls: set[str] = set()

    for endpoint in HN_ENDPOINTS:
        item_ids = fetch_hn_json(session, f"https://hacker-news.firebaseio.com/v0/{endpoint}.json")
        if not isinstance(item_ids, list):
            skipped["endpoint_fetch_failed"] += 1
            continue

        for item_id in item_ids:
            if len(stories) >= target_count:
                return stories, skipped

            if not isinstance(item_id, int) or item_id in seen_story_ids:
                skipped["duplicate_or_invalid_story_id"] += 1
                continue

            seen_story_ids.add(item_id)
            item = fetch_hn_json(session, f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json")
            story = parse_story_candidate(endpoint, item)

            if story is None:
                skipped["missing_external_url_or_invalid_story"] += 1
                continue

            if story.url in seen_urls:
                skipped["duplicate_url"] += 1
                continue

            seen_urls.add(story.url)
            stories.append(story)

    return stories, skipped


def benchmark_story(
    session: requests.Session,
    story: StoryCandidate,
) -> tuple[dict[str, Any], dict[str, Any]]:
    started_at = time.perf_counter()
    article = fetch_and_extract_article(session, story.url)
    comment = fetch_top_comment(session, story.kids)
    elapsed = time.perf_counter() - started_at

    preview_text = build_preview_candidate(article.text) if article.extraction_success else ""
    preview_candidate_exists = bool(preview_text)
    source_type = classify_source_type(story.url)

    row = {
        "story_id": story.story_id,
        "title": story.title,
        "url": story.url,
        "domain": story.domain,
        "hn_score": story.score,
        "hn_comment_count": story.descendants,
        "http_status": article.http_status or "",
        "fetch_success": article.fetch_success,
        "extraction_success": article.extraction_success,
        "extracted_text_length": len(article.text),
        "word_count": article.word_count,
        "reading_time_minutes": calculate_reading_time_minutes(article.word_count),
        "preview_candidate_exists": preview_candidate_exists,
        "preview_candidate_length": len(preview_text),
        "published_date_found": bool(article.published_date),
        "meta_description_found": bool(article.meta_description),
        "source_type": source_type,
        "top_comment_available": comment.available,
        "top_comment_length": len(comment.text),
        "hn_insight_candidate_exists": comment.insight_exists,
        "failure_reason": article.failure_reason,
        "elapsed_seconds": f"{elapsed:.3f}",
    }

    detail = {
        "story": story,
        "article": article,
        "comment": comment,
        "preview_text": preview_text,
        "suspicious_preview_reasons": suspicious_preview_reasons(
            title=story.title,
            text=article.text,
            preview=preview_text,
        ),
        "elapsed_seconds": elapsed,
    }
    return row, detail


def fetch_and_extract_article(session: requests.Session, url: str) -> ArticleResult:
    response: requests.Response | None = None

    try:
        response = session.get(url, timeout=ARTICLE_TIMEOUT_SECONDS)
    except requests.Timeout as exc:
        return failed_article(None, "timeout", exc, url)
    except requests.RequestException as exc:
        return failed_article(None, "network_error", exc, url)

    status = response.status_code
    if status in {401, 403}:
        return failed_article(status, "access_blocked_401_403", None, url)

    if status == 429:
        return failed_article(status, "rate_limited_429", None, url)

    if status >= 400:
        return failed_article(status, "network_error", None, url)

    content_type = response.headers.get("content-type", "").lower()
    if not looks_like_extractable_content(url, content_type):
        return failed_article(status, "non_html_or_pdf", None, url)

    try:
        extracted = trafilatura.extract(
            response.text,
            output_format="json",
            with_metadata=True,
            include_comments=False,
            include_tables=False,
        )
    except Exception as exc:
        return failed_article(status, "unknown", exc, url)

    if not extracted:
        return failed_article(status, "empty_extraction", None, url)

    try:
        data = json.loads(extracted)
    except json.JSONDecodeError as exc:
        return failed_article(status, "unknown", exc, url)

    text = string_value(data.get("text"))
    word_count = count_words(text)
    if not text:
        return failed_article(status, "empty_extraction", None, url)

    if word_count < 80:
        return ArticleResult(
            http_status=status,
            fetch_success=True,
            extraction_success=False,
            text=text,
            word_count=word_count,
            published_date=find_published_date(response.text, data),
            meta_description=find_meta_description(response.text, data),
            failure_reason="too_short",
            error_message="Extracted text word count was below 80.",
        )

    return ArticleResult(
        http_status=status,
        fetch_success=True,
        extraction_success=True,
        text=text,
        word_count=word_count,
        published_date=find_published_date(response.text, data),
        meta_description=find_meta_description(response.text, data),
        failure_reason="",
        error_message="",
    )


def failed_article(
    status: int | None,
    reason: str,
    exc: Exception | None,
    url: str,
) -> ArticleResult:
    return ArticleResult(
        http_status=status,
        fetch_success=False,
        extraction_success=False,
        text="",
        word_count=0,
        published_date="",
        meta_description="",
        failure_reason=reason,
        error_message=sanitize_error(exc, url) if exc else reason,
    )


def fetch_top_comment(session: requests.Session, kids: tuple[int, ...]) -> CommentResult:
    for comment_id in kids[:COMMENT_SCAN_LIMIT]:
        item = fetch_hn_json(session, f"https://hacker-news.firebaseio.com/v0/item/{comment_id}.json")
        if not isinstance(item, dict):
            continue

        comment_text = parse_comment_text(item)
        if not comment_text:
            continue

        cleaned = clean_comment_text(comment_text)
        if not cleaned:
            continue

        return CommentResult(
            available=True,
            text=cleaned,
            insight_exists=build_hn_insight((cleaned,)) is not None,
        )

    return CommentResult(available=False, text="", insight_exists=False)


def parse_story_candidate(endpoint: str, item: Any) -> StoryCandidate | None:
    if not isinstance(item, dict):
        return None

    if item.get("type") != "story" or item.get("deleted") or item.get("dead"):
        return None

    story_id = item.get("id")
    title = item.get("title")
    url = item.get("url")

    if not isinstance(story_id, int):
        return None

    if not isinstance(title, str) or not title.strip():
        return None

    if not isinstance(url, str) or not url.strip():
        return None

    parsed = urlparse(url)
    domain = (parsed.hostname or "").removeprefix("www.")
    if not parsed.scheme.startswith("http") or not domain or domain == "news.ycombinator.com":
        return None

    kids = item.get("kids")
    return StoryCandidate(
        endpoint=endpoint,
        story_id=story_id,
        title=" ".join(title.split()),
        url=url,
        domain=domain,
        score=item.get("score") if isinstance(item.get("score"), int) else 0,
        descendants=item.get("descendants") if isinstance(item.get("descendants"), int) else 0,
        kids=tuple(kid for kid in kids if isinstance(kid, int)) if isinstance(kids, list) else (),
    )


def build_preview_candidate(text: str) -> str:
    paragraphs = [clean_whitespace(part) for part in re.split(r"\n+", text)]
    for paragraph in paragraphs:
        if is_meaningful_preview_text(paragraph):
            return truncate_text(paragraph)

    cleaned = clean_whitespace(text)
    if is_meaningful_preview_text(cleaned):
        return truncate_text(cleaned)

    return ""


def suspicious_preview_reasons(title: str, text: str, preview: str) -> list[str]:
    reasons: list[str] = []
    if not preview:
        reasons.append("missing")
        return reasons

    lower_preview = preview.lower()
    lower_title = clean_whitespace(title).lower()
    if lower_title and lower_preview.startswith(lower_title[: min(len(lower_title), 60)]):
        reasons.append("starts_with_title")

    if len(preview) < 80:
        reasons.append("too_short")

    if looks_like_boilerplate(preview):
        reasons.append("boilerplate_like")

    if boilerplate_ratio(text) >= 0.35:
        reasons.append("boilerplate_dominated")

    return reasons


def is_meaningful_preview_text(text: str) -> bool:
    cleaned = clean_whitespace(text)
    if len(cleaned) < 80:
        return False

    if looks_like_boilerplate(cleaned):
        return False

    return bool(split_sentences(cleaned))


def looks_like_boilerplate(text: str) -> bool:
    lower = text.lower()
    fragments = (
        "accept cookies",
        "cookie policy",
        "privacy policy",
        "subscribe to",
        "sign up",
        "enable javascript",
        "newsletter",
        "advertisement",
        "all rights reserved",
        "skip to content",
        "main navigation",
    )
    return any(fragment in lower for fragment in fragments)


def boilerplate_ratio(text: str) -> float:
    paragraphs = [clean_whitespace(part) for part in re.split(r"\n+", text) if clean_whitespace(part)]
    if not paragraphs:
        return 0.0

    boilerplate_count = sum(1 for paragraph in paragraphs if looks_like_boilerplate(paragraph))
    return boilerplate_count / len(paragraphs)


def looks_like_extractable_content(url: str, content_type: str) -> bool:
    path = urlparse(url).path.lower()
    if path.endswith(".pdf") or "application/pdf" in content_type:
        return False

    if not content_type:
        return True

    return "text/html" in content_type or "application/xhtml" in content_type


def find_published_date(html_text: str, data: dict[str, Any]) -> str:
    for key in ("date", "published", "date_published"):
        value = string_value(data.get(key))
        if looks_like_date(value):
            return value

    parser = MetadataParser()
    parser.feed(html_text)
    return parser.published_date


def find_meta_description(html_text: str, data: dict[str, Any]) -> str:
    description = string_value(data.get("description"))
    if description:
        return description

    parser = MetadataParser()
    parser.feed(html_text)
    return parser.description


class MetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.published_date = ""
        self.description = ""
        self._json_ld_parts: list[str] = []
        self._inside_json_ld = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name.lower(): value or "" for name, value in attrs}
        if tag.lower() == "meta":
            key = (attr_map.get("property") or attr_map.get("name") or "").lower()
            content = html.unescape(attr_map.get("content", "")).strip()

            if not self.description and key in {"description", "og:description", "twitter:description"}:
                self.description = clean_whitespace(content)

            if not self.published_date and key in {
                "article:published_time",
                "date",
                "datepublished",
                "pubdate",
                "publishdate",
                "dc.date",
                "dc.date.issued",
            }:
                if looks_like_date(content):
                    self.published_date = content

        if tag.lower() == "script" and attr_map.get("type", "").lower() == "application/ld+json":
            self._inside_json_ld = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._inside_json_ld:
            self._inside_json_ld = False
            self._consume_json_ld("".join(self._json_ld_parts))
            self._json_ld_parts = []

    def handle_data(self, data: str) -> None:
        if self._inside_json_ld:
            self._json_ld_parts.append(data)

    def _consume_json_ld(self, payload: str) -> None:
        if self.published_date:
            return

        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            return

        date_value = find_json_ld_date(parsed)
        if date_value:
            self.published_date = date_value


def find_json_ld_date(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("datePublished", "dateCreated", "uploadDate"):
            candidate = string_value(value.get(key))
            if looks_like_date(candidate):
                return candidate

        graph = value.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                candidate = find_json_ld_date(item)
                if candidate:
                    return candidate

    if isinstance(value, list):
        for item in value:
            candidate = find_json_ld_date(item)
            if candidate:
                return candidate

    return ""


def build_report(
    rows: list[dict[str, Any]],
    details: list[dict[str, Any]],
    skipped: Counter[str],
    source_endpoints: tuple[str, ...],
    total_elapsed: float,
) -> str:
    total = len(rows)
    extraction_successes = [row for row in rows if bool_value(row["extraction_success"])]
    preview_successes = [row for row in rows if bool_value(row["preview_candidate_exists"])]
    published_successes = [row for row in rows if bool_value(row["published_date_found"])]
    top_comment_successes = [row for row in rows if bool_value(row["top_comment_available"])]
    insight_successes = [row for row in rows if bool_value(row["hn_insight_candidate_exists"])]
    link_comments = [
        detail for detail in details if detail["comment"].available and contains_link(detail["comment"].text)
    ]
    code_comments = [
        detail for detail in details if detail["comment"].available and contains_code_like_formatting(detail["comment"].text)
    ]

    failure_breakdown = Counter(row["failure_reason"] or "success" for row in rows)
    source_type_counts = Counter(row["source_type"] for row in rows)
    actual_endpoints = sorted({detail["story"].endpoint for detail in details})

    lines = [
        "# Operational Readiness Benchmark",
        "",
        f"Generated: {datetime.utcnow().isoformat(timespec='seconds')}Z",
        "",
        "This isolated benchmark measures the current free, deterministic HN Daily Digest reading-decision pipeline against live Hacker News stories. It does not call OpenAI, send Telegram messages, modify production code, or change the production message format.",
        "",
        "## Dataset Summary",
        "",
        f"- Total tested: {total}",
        f"- Total skipped: {sum(skipped.values())}",
        f"- Source endpoints configured: {', '.join(source_endpoints)}",
        f"- Source endpoints represented: {', '.join(actual_endpoints)}",
        f"- Skipped breakdown: {format_counter(skipped)}",
        "",
        "## Article Extraction",
        "",
        f"- Success rate: {rate(len(extraction_successes), total)} ({len(extraction_successes)}/{total})",
        f"- Failure reason breakdown: {format_counter(failure_breakdown)}",
        f"- Top failing domains: {format_counter(top_failing_domains(rows), limit=10)}",
        f"- Average extracted word count: {average_number(row['word_count'] for row in extraction_successes):.1f}",
        f"- Average elapsed time: {average_number(float(row['elapsed_seconds']) for row in rows):.2f}s",
        f"- Total elapsed time: {total_elapsed:.2f}s",
        "",
        "## Published Date",
        "",
        f"- Extraction rate: {rate(len(published_successes), total)} ({len(published_successes)}/{total})",
        "- Examples where found:",
        *example_lines([detail for detail in details if detail["article"].published_date], "published_date"),
        "- Examples where missing:",
        *example_lines([detail for detail in details if not detail["article"].published_date], "missing_date"),
        "",
        "## Preview Quality",
        "",
        f"- Preview candidate success rate: {rate(len(preview_successes), total)} ({len(preview_successes)}/{total})",
        f"- Average preview length: {average_number(row['preview_candidate_length'] for row in preview_successes):.1f}",
        "- Suspicious preview examples:",
        *suspicious_preview_lines(details),
        "",
        "## Source Type Classification",
        "",
        f"- Distribution: {format_counter(source_type_counts)}",
        f"- Generic `Article` fallback count: {source_type_counts.get('Article', 0)}",
        "- Examples per type:",
        *source_type_example_lines(details),
        "",
        "## HN Insight",
        "",
        f"- Top comment availability rate: {rate(len(top_comment_successes), total)} ({len(top_comment_successes)}/{total})",
        f"- HN insight candidate rate: {rate(len(insight_successes), total)} ({len(insight_successes)}/{total})",
        f"- Average top comment length: {average_number(row['top_comment_length'] for row in top_comment_successes):.1f}",
        f"- Percentage containing links: {rate(len(link_comments), len(top_comment_successes))}",
        f"- Percentage containing code-like formatting: {rate(len(code_comments), len(top_comment_successes))}",
        "- Useful-looking comment examples:",
        *comment_example_lines(details, useful=True),
        "- Low-value comment examples:",
        *comment_example_lines(details, useful=False),
        "",
        "## Operational Readiness",
        "",
        "### What Appears Reliable",
        "",
        *readiness_reliable_lines(rows),
        "",
        "### What Appears Risky",
        "",
        *readiness_risky_lines(rows, details),
        "",
        "### What Should Remain Fallback-Only",
        "",
        "- Access-blocked, rate-limited, timed-out, non-HTML/PDF, empty, and too-short article extractions should remain fallback-only in this benchmark context.",
        "- Generic `Article` source-type classification should be treated as a coarse fallback label, not a strong content signal.",
        "- Low-value HN comments should remain optional context and should not override article-derived previews.",
        "",
        "No production implementation is proposed here; this file is measurement only.",
        "",
    ]
    return "\n".join(lines)


def example_lines(details: list[dict[str, Any]], kind: str, limit: int = 5) -> list[str]:
    if not details:
        return ["  - None observed."]

    lines: list[str] = []
    for detail in details[:limit]:
        story = detail["story"]
        article = detail["article"]
        if kind == "published_date":
            lines.append(f"  - {story.domain}: {story.title} ({article.published_date})")
        else:
            lines.append(f"  - {story.domain}: {story.title}")
    return lines


def suspicious_preview_lines(details: list[dict[str, Any]], limit: int = 8) -> list[str]:
    suspicious = [detail for detail in details if detail["suspicious_preview_reasons"]]
    if not suspicious:
        return ["  - None observed."]

    lines: list[str] = []
    for detail in suspicious[:limit]:
        story = detail["story"]
        reasons = ", ".join(detail["suspicious_preview_reasons"])
        preview = truncate_text(detail["preview_text"] or detail["article"].error_message, max_chars=130)
        lines.append(f"  - {story.domain}: {reasons}; {preview}")
    return lines


def source_type_example_lines(details: list[dict[str, Any]], limit_per_type: int = 3) -> list[str]:
    examples: dict[str, list[str]] = defaultdict(list)
    for detail in details:
        story = detail["story"]
        source_type = classify_source_type(story.url)
        if len(examples[source_type]) < limit_per_type:
            examples[source_type].append(f"{story.domain}: {story.title}")

    lines: list[str] = []
    for source_type in sorted(examples):
        joined = "; ".join(examples[source_type])
        lines.append(f"  - {source_type}: {joined}")
    return lines


def comment_example_lines(details: list[dict[str, Any]], useful: bool, limit: int = 5) -> list[str]:
    if useful:
        candidates = [
            detail for detail in details if detail["comment"].available and detail["comment"].insight_exists
        ]
    else:
        candidates = [
            detail
            for detail in details
            if detail["comment"].available and not detail["comment"].insight_exists
        ]

    if not candidates:
        return ["  - None observed."]

    lines: list[str] = []
    for detail in candidates[:limit]:
        story = detail["story"]
        comment = truncate_text(detail["comment"].text, max_chars=130)
        lines.append(f"  - {story.domain}: {comment}")
    return lines


def readiness_reliable_lines(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        f"- Article extraction produced usable text for {rate(sum(bool_value(row['extraction_success']) for row in rows), len(rows))} of tested stories.",
        f"- Preview candidates were available for {rate(sum(bool_value(row['preview_candidate_exists']) for row in rows), len(rows))} of tested stories.",
        f"- HN top-level comment context was available for {rate(sum(bool_value(row['top_comment_available']) for row in rows), len(rows))} of tested stories.",
    ]
    return lines


def readiness_risky_lines(rows: list[dict[str, Any]], details: list[dict[str, Any]]) -> list[str]:
    failures = Counter(row["failure_reason"] for row in rows if row["failure_reason"])
    suspicious_count = sum(1 for detail in details if detail["suspicious_preview_reasons"])
    lines = [
        f"- Extraction failures remain common enough to require fallback behavior: {format_counter(failures)}.",
        f"- Suspicious or missing preview candidates were observed for {suspicious_count} stories.",
        f"- Published-date coverage was {rate(sum(bool_value(row['published_date_found']) for row in rows), len(rows))}, so dates should be treated as opportunistic metadata.",
    ]
    return lines


def top_failing_domains(rows: list[dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        if row["failure_reason"]:
            counts[str(row["domain"])] += 1
    return counts


def fetch_hn_json(session: requests.Session, url: str) -> Any:
    try:
        response = session.get(url, timeout=HN_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, json.JSONDecodeError):
        return None


def split_sentences(text: str) -> list[str]:
    cleaned = clean_whitespace(text)
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", cleaned)
        if sentence.strip()
    ]


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def string_value(value: Any) -> str:
    if not isinstance(value, str):
        return ""

    return clean_whitespace(value)


def clean_whitespace(text: str) -> str:
    return " ".join(text.split())


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.lower() == "true"

    return bool(value)


def average_number(values: Any) -> float:
    numbers = [float(value) for value in values]
    if not numbers:
        return 0.0

    return sum(numbers) / len(numbers)


def rate(part: int, whole: int) -> str:
    if whole <= 0:
        return "0.0%"

    return f"{(part / whole) * 100:.1f}%"


def format_counter(counter: Counter[str], limit: int | None = None) -> str:
    if not counter:
        return "none"

    items = counter.most_common(limit)
    return ", ".join(f"{key}: {value}" for key, value in items)


def looks_like_date(value: str) -> bool:
    if not value:
        return False

    return bool(re.search(r"\b(19|20)\d{2}[-/]\d{1,2}[-/]\d{1,2}\b", value))


def contains_link(text: str) -> bool:
    return bool(re.search(r"https?://|www\.", text, flags=re.IGNORECASE))


def contains_code_like_formatting(text: str) -> bool:
    return bool(re.search(r"`|```|~~~|[{};]{2,}|[a-zA-Z_][a-zA-Z0-9_]*\(", text))


def sanitize_error(exc: Exception, url: str) -> str:
    hostname = urlparse(url).hostname or "unknown"
    message = clean_whitespace(str(exc))
    return message.replace(url, f"https://{hostname}/...")


if __name__ == "__main__":
    main()
