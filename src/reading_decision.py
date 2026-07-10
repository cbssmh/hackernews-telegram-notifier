from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import re
from urllib.parse import urlparse

from src.article_extractor import ArticleExtraction
from src.hn_client import HNStory


WORDS_PER_MINUTE = 220
EXCERPT_MIN_CHARS = 120
EXCERPT_MAX_CHARS = 180
MIN_COMMENT_CHARS = 40
NEWS_DOMAIN_HINTS = (
    "apnews",
    "bbc.",
    "bloomberg",
    "correspondent",
    "guardian",
    "nytimes",
    "reuters",
    "washingtonpost",
)


@dataclass(frozen=True)
class ReadingDecisionInput:
    story: HNStory
    article: ArticleExtraction


@dataclass(frozen=True)
class ReadingDecision:
    preview: str = ""
    hn_insight: str = ""
    why_trending: str = ""


ReadingDecisionProvider = Callable[[ReadingDecisionInput], ReadingDecision]


def build_article_excerpt(text: str, fallback: str) -> str:
    cleaned_text = _clean_whitespace(text)
    if not cleaned_text:
        return fallback

    paragraphs = [_clean_whitespace(part) for part in re.split(r"\n+", text)]
    meaningful = [part for part in paragraphs if _is_meaningful_article_text(part)]

    if meaningful:
        return truncate_text(meaningful[0], max_chars=EXCERPT_MAX_CHARS)

    sentences = _split_sentences(cleaned_text)
    excerpt = ""
    for sentence in sentences:
        candidate = f"{excerpt} {sentence}".strip()
        if len(candidate) > EXCERPT_MAX_CHARS:
            break
        excerpt = candidate
        if len(excerpt) >= EXCERPT_MIN_CHARS:
            break

    return truncate_text(excerpt or cleaned_text, max_chars=EXCERPT_MAX_CHARS)


def build_hn_insight(comments: tuple[str, ...]) -> str | None:
    for comment in comments:
        cleaned = clean_comment_text(comment)
        if len(cleaned) < MIN_COMMENT_CHARS:
            continue
        return truncate_text(cleaned, max_chars=EXCERPT_MAX_CHARS)

    return None


def clean_comment_text(comment: str) -> str:
    lines: list[str] = []
    for line in comment.splitlines():
        stripped = line.strip()
        stripped = stripped.removeprefix(">").strip()
        if not stripped or stripped in {"```", "~~~"}:
            continue
        lines.append(stripped)

    return _clean_whitespace(" ".join(lines))


def calculate_reading_time_minutes(word_count: int) -> int:
    if word_count <= 0:
        return 1

    return max(1, round(word_count / WORDS_PER_MINUTE))


def classify_source_type(url: str | None) -> str:
    if not url:
        return "Discussion"

    parsed = urlparse(url)
    domain = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path.lower()
    path_parts = [part for part in path.split("/") if part]

    if domain == "github.com" and len(path_parts) >= 2:
        return "Project / Repository"

    if domain == "github.blog" or "engineering" in domain or "/engineering/" in path:
        return "Engineering Blog"

    if domain == "arxiv.org":
        return "Research"

    if domain.startswith("docs.") or "/docs/" in path or path.startswith("/docs"):
        return "Documentation"

    if any(hint in domain for hint in NEWS_DOMAIN_HINTS):
        return "News"

    return "Article"


def truncate_text(text: str, max_chars: int = EXCERPT_MAX_CHARS) -> str:
    cleaned = _clean_whitespace(text)
    if len(cleaned) <= max_chars:
        return cleaned

    limit = max_chars - 3
    truncated = cleaned[:limit].rsplit(" ", 1)[0].rstrip(".,;: ")
    if not truncated:
        truncated = cleaned[:limit].rstrip(".,;: ")

    return f"{truncated}..."


def _is_meaningful_article_text(text: str) -> bool:
    lower_text = text.lower()
    if len(text) < 80:
        return False

    if any(
        fragment in lower_text
        for fragment in (
            "accept cookies",
            "cookie policy",
            "privacy policy",
            "subscribe to",
            "sign up",
            "enable javascript",
            "newsletter",
        )
    ):
        return False

    return len(_split_sentences(text)) >= 1


def _split_sentences(text: str) -> list[str]:
    cleaned = _clean_whitespace(text)
    if not cleaned:
        return []

    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", cleaned)
        if sentence.strip()
    ]


def _clean_whitespace(text: str) -> str:
    return " ".join(text.split())
