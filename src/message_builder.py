from __future__ import annotations

from collections.abc import Callable
from datetime import date

from src.hn_client import HNStory
from src.summarizer import build_rule_based_summary


SummaryProvider = Callable[[HNStory], str]


def build_daily_message(
    stories: list[HNStory],
    target_date: date | None = None,
    summary_provider: SummaryProvider = build_rule_based_summary,
) -> str:
    message_date = target_date or date.today()

    lines: list[str] = [
        f"📰 HN Daily Top 3 — {message_date.isoformat()}",
        "",
    ]

    if not stories:
        lines.append("오늘 수집 가능한 Hacker News 인기글이 없습니다.")
        return "\n".join(lines)

    for index, story in enumerate(stories, start=1):
        source_url = story.url or story.discussion_url

        lines.extend(
            [
                f"{index}. {story.title}",
                f"요약: {summary_provider(story)}",
                f"점수: {story.score} | 댓글: {story.descendants}",
                f"원문: {source_url}",
                f"토론: {story.discussion_url}",
                "",
                "---",
                "",
            ]
        )

    return "\n".join(lines).strip()
