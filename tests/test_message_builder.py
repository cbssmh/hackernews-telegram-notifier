from datetime import date

from src.hn_client import HNStory
from src.message_builder import build_daily_message


def test_build_daily_message_contains_story_information() -> None:
    story = HNStory(
        id=123,
        title="Example Story",
        url="https://example.com/post",
        score=100,
        descendants=20,
    )

    message = build_daily_message([story], target_date=date(2026, 5, 21))

    assert "HN Daily Top 3 — 2026-05-21" in message
    assert "Example Story" in message
    assert "점수: 100 | 댓글: 20" in message
    assert "https://example.com/post" in message
    assert "https://news.ycombinator.com/item?id=123" in message


def test_build_daily_message_without_stories() -> None:
    message = build_daily_message([], target_date=date(2026, 5, 21))

    assert "수집 가능한 Hacker News 인기글이 없습니다" in message