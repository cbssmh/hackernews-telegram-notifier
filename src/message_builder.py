from __future__ import annotations

from collections.abc import Callable
from datetime import date
from html import escape
import re
from urllib.parse import urlparse

from src.article_extractor import ArticleExtraction, extract_article
from src.hn_client import HNStory
from src.reading_decision import (
    ReadingDecision,
    ReadingDecisionInput,
    ReadingDecisionProvider,
    build_article_excerpt,
    build_hn_insight,
    calculate_reading_time_minutes,
)
from src.summarizer import build_rule_based_summary


SummaryProvider = Callable[[HNStory], str]
ArticleExtractor = Callable[[str], ArticleExtraction]
ACCESS_BLOCKED_PREVIEW_UNAVAILABLE = (
    "본문 미리보기를 가져오지 못했습니다. 원문 사이트가 자동 접근을 차단했을 수 있습니다."
)
PREVIEW_UNAVAILABLE = "본문 미리보기를 가져오지 못했습니다."


def build_daily_message(
    stories: list[HNStory],
    target_date: date | None = None,
    summary_provider: SummaryProvider = build_rule_based_summary,
    article_extractor: ArticleExtractor = extract_article,
    reading_decision_provider: ReadingDecisionProvider | None = None,
) -> str:
    message_date = target_date or date.today()

    lines: list[str] = [
        f"📰 HN Daily Top 3 — {message_date.isoformat()}",
        "",
    ]

    if not stories:
        lines.append("오늘 수집 가능한 Hacker News 인기글이 없습니다.")
        return "\n".join(lines)

    for rank, story in enumerate(stories, start=1):
        lines.extend(
            build_story_lines(
                story,
                rank=rank,
                summary_provider=summary_provider,
                article_extractor=article_extractor,
                reading_decision_provider=reading_decision_provider,
            )
        )

    return "\n".join(lines).strip()


def build_story_lines(
    story: HNStory,
    rank: int = 1,
    summary_provider: SummaryProvider = build_rule_based_summary,
    article_extractor: ArticleExtractor = extract_article,
    reading_decision_provider: ReadingDecisionProvider | None = None,
) -> list[str]:
    article = _extract_article(story.url, article_extractor)
    title = article.title if article.success and article.title else story.title
    article_url = story.url or story.discussion_url
    domain = story.domain or "news.ycombinator.com"
    base_preview = (
        build_article_excerpt(article.text, fallback=PREVIEW_UNAVAILABLE)
        if article.success
        else _build_preview_unavailable_message(article)
    )
    base_hn_insight = build_hn_insight(story.top_comments)
    decision = _build_reading_decision(story, article, reading_decision_provider)
    preview = decision.preview if article.success and decision.preview else base_preview
    hn_insight = decision.hn_insight or base_hn_insight
    why_trending = decision.why_trending

    lines = [
        f"{rank}. {escape(title)}",
        "",
    ]

    if article.success and article.published_date:
        lines.append(f"Published: {escape(article.published_date)}")

    metadata_line = escape(domain)
    if article.success:
        metadata_line = f"{metadata_line} · {calculate_reading_time_minutes(article.word_count)} min"

    lines.extend(
        [
            metadata_line,
            f"{story.score} points · {story.descendants} comments",
            "",
            "Preview:",
            escape(preview),
            "",
        ]
    )

    if hn_insight:
        lines.extend(
            [
                "HN Insight:",
                escape(hn_insight),
                "",
            ]
        )

    if why_trending:
        lines.extend(
            [
                "Why Trending:",
                escape(why_trending),
                "",
            ]
        )

    lines.extend(
        [
            f"Source: {_build_html_link(article_url, _display_hostname(article_url))}",
            f"Discussion: {_build_html_link(story.discussion_url, 'HN Discussion')}",
            "",
            "---",
            "",
        ]
    )

    return lines


def _build_reading_decision(
    story: HNStory,
    article: ArticleExtraction,
    reading_decision_provider: ReadingDecisionProvider | None,
) -> ReadingDecision:
    if reading_decision_provider is None:
        return ReadingDecision()

    try:
        return reading_decision_provider(
            ReadingDecisionInput(
                story=story,
                article=article,
            )
        )
    except Exception:
        return ReadingDecision()


def _extract_article(
    url: str | None,
    article_extractor: ArticleExtractor,
) -> ArticleExtraction:
    if not url:
        return ArticleExtraction(success=False)

    try:
        return article_extractor(url)
    except Exception as exc:
        return ArticleExtraction(success=False, error=f"Article extraction failed: {exc}")


def _build_preview_unavailable_message(article: ArticleExtraction) -> str:
    if _is_access_blocked_error(article.error):
        return ACCESS_BLOCKED_PREVIEW_UNAVAILABLE

    return PREVIEW_UNAVAILABLE


def _is_access_blocked_error(error: str) -> bool:
    return bool(re.search(r"\b(?:401|403|429)\b", error))


def _display_hostname(url: str) -> str:
    try:
        hostname = urlparse(url).hostname
    except ValueError:
        return url

    if not hostname:
        return url

    return hostname.removeprefix("www.")


def _build_html_link(url: str, text: str) -> str:
    return f'<a href="{escape(url, quote=True)}">{escape(text)}</a>'
