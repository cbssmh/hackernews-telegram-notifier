from __future__ import annotations

from collections.abc import Callable
from datetime import date

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
        build_article_excerpt(article.text, fallback=summary_provider(story))
        if article.success
        else summary_provider(story)
    )
    reading_time = calculate_reading_time_minutes(article.word_count)
    hn_insight = build_hn_insight(story.top_comments)

    lines = [
        f"📰 {title}",
        "",
        f"📂 {classify_source_type(story.url)}",
        f"{domain} · ⏱ {reading_time} min",
        f"⭐{story.score} · 💬{story.descendants}",
        "",
        "📖 Preview",
        preview,
        "",
    ]

    if hn_insight:
        lines.extend(
            [
                "💬 HN Insight",
                hn_insight,
                "",
            ]
        )

    lines.extend(
        [
            f"🔗 Read: {article_url}",
            f"💬 Discuss: {story.discussion_url}",
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
