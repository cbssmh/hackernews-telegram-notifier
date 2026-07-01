from datetime import date

from src.article_extractor import ArticleExtraction
from src.hn_client import HNStory
from src.message_builder import build_daily_message


def test_build_daily_message_contains_reading_decision_sections() -> None:
    story = HNStory(
        id=123,
        title="HN Title",
        url="https://github.blog/engineering/example-post",
        score=100,
        descendants=20,
        top_comments=(
            "This adds useful engineering context about why the implementation matters.",
        ),
    )

    message = build_daily_message(
        [story],
        target_date=date(2026, 5, 21),
        article_extractor=lambda url: ArticleExtraction(
            success=True,
            title="Extracted Article Title",
            text=(
                "This is the first meaningful paragraph from the article. "
                "It gives enough evidence for a fast reading decision without adding new claims."
            ),
            word_count=440,
        ),
    )

    assert "HN Daily Top 3 — 2026-05-21" in message
    assert "📰 Extracted Article Title" in message
    assert "📂 Engineering Blog" in message
    assert "github.blog · ⏱ 2 min" in message
    assert "⭐100 · 💬20" in message
    assert "📖 Preview" in message
    assert "This is the first meaningful paragraph" in message
    assert "💬 HN Insight" in message
    assert "useful engineering context" in message
    assert (
        '🔗 원문: <a href="https://github.blog/engineering/example-post">github.blog</a>'
        in message
    )
    assert (
        '💬 토론: <a href="https://news.ycombinator.com/item?id=123">HN Discussion</a>'
        in message
    )


def test_build_daily_message_falls_back_when_article_extraction_fails() -> None:
    story = HNStory(
        id=123,
        title="Fallback Story",
        url="https://example.com/post",
        score=100,
        descendants=20,
    )

    message = build_daily_message(
        [story],
        target_date=date(2026, 5, 21),
        summary_provider=lambda story: "Fallback preview",
        article_extractor=lambda url: ArticleExtraction(success=False, error="blocked"),
    )

    assert "📖 Preview\nFallback preview" in message
    assert "⏱ 1 min" in message


def test_build_daily_message_falls_back_when_article_extractor_raises() -> None:
    story = HNStory(
        id=123,
        title="Fallback Story",
        url="https://example.com/post",
        score=100,
        descendants=20,
    )

    def raising_extractor(url: str) -> ArticleExtraction:
        raise RuntimeError("network blocked")

    message = build_daily_message(
        [story],
        target_date=date(2026, 5, 21),
        summary_provider=lambda story: "Fallback preview",
        article_extractor=raising_extractor,
    )

    assert "📖 Preview\nFallback preview" in message


def test_build_daily_message_omits_hn_insight_when_comments_are_missing() -> None:
    story = HNStory(
        id=123,
        title="Example Story",
        url="https://example.com/post",
        score=100,
        descendants=20,
    )

    message = build_daily_message(
        [story],
        target_date=date(2026, 5, 21),
        article_extractor=lambda url: ArticleExtraction(
            success=True,
            text="A meaningful article paragraph that can be used as preview text.",
            word_count=220,
        ),
    )

    assert "💬 HN Insight" not in message


def test_build_daily_message_without_stories() -> None:
    message = build_daily_message([], target_date=date(2026, 5, 21))

    assert "수집 가능한 Hacker News 인기글이 없습니다" in message


def test_build_daily_message_removes_www_from_article_link_text() -> None:
    story = HNStory(
        id=123,
        title="Example Story",
        url="https://www.example.com/post",
        score=100,
        descendants=20,
    )

    message = build_daily_message(
        [story],
        target_date=date(2026, 5, 21),
        article_extractor=lambda url: ArticleExtraction(success=False),
        summary_provider=lambda story: "Fallback preview",
    )

    assert '🔗 원문: <a href="https://www.example.com/post">example.com</a>' in message


def test_build_daily_message_uses_full_url_as_link_text_when_hostname_is_missing() -> None:
    story = HNStory(
        id=123,
        title="Example Story",
        url="not-a-url",
        score=100,
        descendants=20,
    )

    message = build_daily_message(
        [story],
        target_date=date(2026, 5, 21),
        article_extractor=lambda url: ArticleExtraction(success=False),
        summary_provider=lambda story: "Fallback preview",
    )

    assert '🔗 원문: <a href="not-a-url">not-a-url</a>' in message
