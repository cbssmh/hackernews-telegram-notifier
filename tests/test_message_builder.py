from datetime import date

from src.article_extractor import ArticleExtraction
from src.hn_client import HNStory
from src.message_builder import (
    ACCESS_BLOCKED_PREVIEW_UNAVAILABLE,
    PREVIEW_UNAVAILABLE,
    build_daily_message,
)
from src.reading_decision import ReadingDecision


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
            published_date="2026-05-20",
        ),
    )

    assert "HN Daily Top 3 — 2026-05-21" in message
    assert "1. Extracted Article Title" in message
    assert "Published: 2026-05-20" in message
    assert "github.blog · 2 min" in message
    assert "100 points · 20 comments" in message
    assert "Preview:" in message
    assert "This is the first meaningful paragraph" in message
    assert "HN Insight:" in message
    assert "useful engineering context" in message
    assert (
        'Source: <a href="https://github.blog/engineering/example-post">github.blog</a>'
        in message
    )
    assert (
        'Discussion: <a href="https://news.ycombinator.com/item?id=123">HN Discussion</a>'
        in message
    )


def test_build_daily_message_is_unchanged_without_reading_decision_provider() -> None:
    story = HNStory(
        id=123,
        title="HN Title",
        url="https://example.com/post",
        score=100,
        descendants=20,
        top_comments=("This comment adds useful context about the story.",),
    )

    without_provider = build_daily_message(
        [story],
        target_date=date(2026, 5, 21),
        article_extractor=_successful_article_extractor,
    )
    explicit_none = build_daily_message(
        [story],
        target_date=date(2026, 5, 21),
        article_extractor=_successful_article_extractor,
        reading_decision_provider=None,
    )

    assert explicit_none == without_provider
    assert "Why Trending:" not in explicit_none


def test_build_daily_message_uses_reading_decision_preview() -> None:
    story = _story_with_comments()

    message = build_daily_message(
        [story],
        target_date=date(2026, 5, 21),
        article_extractor=_successful_article_extractor,
        reading_decision_provider=lambda decision_input: ReadingDecision(
            preview="NVIDIA가 작성한 자연스러운 미리보기입니다.",
        ),
    )

    assert "Preview:\nNVIDIA가 작성한 자연스러운 미리보기입니다." in message
    assert "This is the first meaningful paragraph" not in message


def test_build_daily_message_uses_reading_decision_hn_insight() -> None:
    story = _story_with_comments()

    message = build_daily_message(
        [story],
        target_date=date(2026, 5, 21),
        article_extractor=_successful_article_extractor,
        reading_decision_provider=lambda decision_input: ReadingDecision(
            hn_insight="댓글에서는 배포 방식과 실무 적용 가능성을 주로 비교합니다.",
        ),
    )

    assert "HN Insight:\n댓글에서는 배포 방식과 실무 적용 가능성을 주로 비교합니다." in message
    assert "useful engineering context" not in message


def test_build_daily_message_adds_why_trending_when_available() -> None:
    story = _story_with_comments()

    message = build_daily_message(
        [story],
        target_date=date(2026, 5, 21),
        article_extractor=_successful_article_extractor,
        reading_decision_provider=lambda decision_input: ReadingDecision(
            why_trending="점수와 댓글 수가 높고 실무 장단점 논의가 이어져 주목받고 있습니다.",
        ),
    )

    assert "Why Trending:" in message
    assert "점수와 댓글 수가 높고 실무 장단점 논의가 이어져 주목받고 있습니다." in message


def test_build_daily_message_falls_back_for_empty_reading_decision_fields() -> None:
    story = _story_with_comments()

    message = build_daily_message(
        [story],
        target_date=date(2026, 5, 21),
        article_extractor=_successful_article_extractor,
        reading_decision_provider=lambda decision_input: ReadingDecision(),
    )

    assert "Preview:\nThis is the first meaningful paragraph" in message
    assert "HN Insight:" in message
    assert "useful engineering context" in message
    assert "Why Trending:" not in message


def test_build_daily_message_survives_reading_decision_provider_error() -> None:
    story = _story_with_comments()

    def raising_provider(decision_input):
        raise RuntimeError("provider failed")

    message = build_daily_message(
        [story],
        target_date=date(2026, 5, 21),
        article_extractor=_successful_article_extractor,
        reading_decision_provider=raising_provider,
    )

    assert "Preview:\nThis is the first meaningful paragraph" in message
    assert "HN Insight:" in message
    assert "Why Trending:" not in message


def test_build_daily_message_calls_reading_decision_provider_once_per_story() -> None:
    story = _story_with_comments()
    calls = []

    def recording_provider(decision_input):
        calls.append(decision_input)
        return ReadingDecision(why_trending="한 번만 호출됩니다.")

    message = build_daily_message(
        [story],
        target_date=date(2026, 5, 21),
        article_extractor=_successful_article_extractor,
        reading_decision_provider=recording_provider,
    )

    assert len(calls) == 1
    assert calls[0].story is story
    assert calls[0].article.success is True
    assert "한 번만 호출됩니다." in message


def test_build_daily_message_escapes_reading_decision_fields() -> None:
    story = _story_with_comments()

    message = build_daily_message(
        [story],
        target_date=date(2026, 5, 21),
        article_extractor=_successful_article_extractor,
        reading_decision_provider=lambda decision_input: ReadingDecision(
            preview="<b>preview</b> & text",
            hn_insight="<i>comment</i> & text",
            why_trending="<script>alert(1)</script>",
        ),
    )

    assert "&lt;b&gt;preview&lt;/b&gt; &amp; text" in message
    assert "&lt;i&gt;comment&lt;/i&gt; &amp; text" in message
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in message
    assert "<b>preview</b>" not in message


def test_build_daily_message_preserves_unavailable_preview_when_article_extraction_fails() -> None:
    story = HNStory(
        id=123,
        title="Fallback Story",
        url="https://example.com/post",
        score=100,
        descendants=20,
        top_comments=(
            "This comment still has enough detail for an HN insight when extraction fails.",
        ),
    )

    message = build_daily_message(
        [story],
        target_date=date(2026, 5, 21),
        article_extractor=lambda url: ArticleExtraction(success=False, error="blocked"),
        reading_decision_provider=lambda decision_input: ReadingDecision(
            preview="Provider preview must not replace unavailable article preview.",
            hn_insight="Provider HN insight can still be used.",
            why_trending="Provider why trending can still be used.",
        ),
    )

    assert f"Preview:\n{PREVIEW_UNAVAILABLE}" in message
    assert "Provider preview must not replace unavailable article preview." not in message
    assert "HN Insight:\nProvider HN insight can still be used." in message
    assert "Why Trending:\nProvider why trending can still be used." in message


def test_build_daily_message_uses_access_blocked_preview_when_article_fetch_is_blocked() -> None:
    for status_code in (401, 403, 429):
        story = HNStory(
            id=status_code,
            title="Blocked Story",
            url="https://example.com/post",
            score=100,
            descendants=20,
        )

        message = build_daily_message(
            [story],
            target_date=date(2026, 5, 21),
            summary_provider=lambda story: "Fallback preview",
            article_extractor=lambda url: ArticleExtraction(
                success=False,
                error=f"Fetch failed: {status_code} Client Error",
            ),
        )

        assert f"Preview:\n{ACCESS_BLOCKED_PREVIEW_UNAVAILABLE}" in message
        assert "Fallback preview" not in message
        assert "example.com · " not in message
        assert "Published:" not in message


def test_build_daily_message_uses_generic_preview_when_article_extraction_fails() -> None:
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

    assert f"Preview:\n{PREVIEW_UNAVAILABLE}" in message
    assert "Fallback preview" not in message
    assert "example.com · " not in message
    assert "Published:" not in message


def test_build_daily_message_uses_generic_preview_when_article_extractor_raises() -> None:
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

    assert f"Preview:\n{PREVIEW_UNAVAILABLE}" in message
    assert "Fallback preview" not in message


def test_build_daily_message_keeps_hn_insight_when_preview_fallback_is_used() -> None:
    story = HNStory(
        id=123,
        title="Fallback Story",
        url="https://example.com/post",
        score=100,
        descendants=20,
        top_comments=(
            "This comment still adds useful context about the story despite extraction failure.",
        ),
    )

    message = build_daily_message(
        [story],
        target_date=date(2026, 5, 21),
        article_extractor=lambda url: ArticleExtraction(success=False, error="blocked"),
    )

    assert f"Preview:\n{PREVIEW_UNAVAILABLE}" in message
    assert "HN Insight:" in message
    assert "useful context" in message


def test_build_daily_message_does_not_use_old_rule_based_summary_as_preview_fallback() -> None:
    story = HNStory(
        id=123,
        title="Generic Story",
        url="https://example.com/post",
        score=100,
        descendants=20,
    )

    message = build_daily_message(
        [story],
        target_date=date(2026, 5, 21),
        summary_provider=lambda story: "Generic Story라는 주제를 다루며, 제목에서 제기한 문제를 설명하는 글입니다.",
        article_extractor=lambda url: ArticleExtraction(success=False, error="empty"),
    )

    assert f"Preview:\n{PREVIEW_UNAVAILABLE}" in message
    assert "라는 주제를 다루며" not in message


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

    assert "HN Insight:" not in message


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

    assert 'Source: <a href="https://www.example.com/post">example.com</a>' in message


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

    assert 'Source: <a href="not-a-url">not-a-url</a>' in message


def test_build_daily_message_omits_published_when_missing() -> None:
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

    assert "Published:" not in message
    assert "example.com · 1 min" in message


def test_build_daily_message_numbers_multiple_stories() -> None:
    stories = [
        HNStory(id=123, title="First Story", url="https://example.com/one", score=100, descendants=20),
        HNStory(id=456, title="Second Story", url="https://example.com/two", score=90, descendants=10),
    ]

    message = build_daily_message(
        stories,
        target_date=date(2026, 5, 21),
        article_extractor=lambda url: ArticleExtraction(success=False, error="blocked"),
    )

    assert "1. First Story" in message
    assert "2. Second Story" in message


def _story_with_comments() -> HNStory:
    return HNStory(
        id=123,
        title="HN Title",
        url="https://github.blog/engineering/example-post",
        score=100,
        descendants=20,
        top_comments=(
            "This adds useful engineering context about why the implementation matters.",
        ),
    )


def _successful_article_extractor(url: str) -> ArticleExtraction:
    return ArticleExtraction(
        success=True,
        title="Extracted Article Title",
        text=(
            "This is the first meaningful paragraph from the article. "
            "It gives enough evidence for a fast reading decision without adding new claims."
        ),
        word_count=440,
        published_date="2026-05-20",
    )
