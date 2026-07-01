from __future__ import annotations

from collections.abc import Callable
from datetime import date
from html import escape
import re
from urllib.parse import urlparse

from src.article_extractor import ArticleExtraction, extract_article
from src.hn_client import HNStory
from src.reading_decision import (
    build_article_excerpt,
    build_hn_insight,
    calculate_reading_time_minutes,
    classify_source_type,
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
) -> str:
    message_date = target_date or date.today()

    lines: list[str] = [
        f"📰 HN Daily Top 3 — {message_date.isoformat()}",
        "",
    ]

    if not stories:
        lines.append("오늘 수집 가능한 Hacker News 인기글이 없습니다.")
        return "\n".join(lines)

    for story in stories:
        lines.extend(
            build_story_lines(
                story,
                summary_provider=summary_provider,
                article_extractor=article_extractor,
            )
        )

    return "\n".join(lines).strip()


def build_story_lines(
    story: HNStory,
    summary_provider: SummaryProvider = build_rule_based_summary,
    article_extractor: ArticleExtractor = extract_article,
) -> list[str]:
    article = _extract_article(story.url, article_extractor)
    title = article.title if article.success and article.title else story.title
    article_url = story.url or story.discussion_url
    domain = story.domain or "news.ycombinator.com"
    preview = (
        build_article_excerpt(article.text, fallback=PREVIEW_UNAVAILABLE)
        if article.success
        else _build_preview_unavailable_message(article)
    )
    reading_time = calculate_reading_time_minutes(article.word_count)
    hn_insight = build_hn_insight(story.top_comments)

    lines = [
        f"📰 {escape(title)}",
        "",
        f"📂 {escape(classify_source_type(story.url))}",
        f"{escape(domain)} · ⏱ {reading_time} min",
        f"⭐{story.score} · 💬{story.descendants}",
        "",
        "📖 Preview",
        escape(preview),
        "",
    ]

    if hn_insight:
        lines.extend(
            [
                "💬 HN Insight",
                escape(hn_insight),
                "",
            ]
        )

    lines.extend(
        [
            f"🔗 원문: {_build_html_link(article_url, _display_hostname(article_url))}",
            f"💬 토론: {_build_html_link(story.discussion_url, 'HN Discussion')}",
            "",
            "---",
            "",
        ]
    )

    return lines


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
