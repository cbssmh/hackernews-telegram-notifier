from src.reading_decision import (
    build_article_excerpt,
    build_hn_insight,
    calculate_reading_time_minutes,
    classify_source_type,
)


def test_article_excerpt_uses_meaningful_text_and_truncates() -> None:
    text = (
        "Accept cookies to continue.\n"
        "This paragraph contains enough article evidence to help the reader decide "
        "whether to open the link, and it should be shortened before it becomes too "
        "long for a Telegram preview while still preserving only text that appeared "
        "directly in the extracted article body."
    )

    excerpt = build_article_excerpt(text, fallback="Fallback")

    assert excerpt.startswith("This paragraph contains enough article evidence")
    assert excerpt.endswith("...")
    assert len(excerpt) <= 180
    assert "Accept cookies" not in excerpt


def test_article_excerpt_falls_back_when_text_is_missing() -> None:
    assert build_article_excerpt("", fallback="Fallback summary") == "Fallback summary"


def test_reading_time_calculation() -> None:
    assert calculate_reading_time_minutes(0) == 1
    assert calculate_reading_time_minutes(110) == 1
    assert calculate_reading_time_minutes(440) == 2
    assert calculate_reading_time_minutes(1540) == 7


def test_source_type_classification() -> None:
    assert classify_source_type("https://github.com/example/project") == "Project / Repository"
    assert classify_source_type("https://github.blog/engineering/post") == "Engineering Blog"
    assert classify_source_type("https://arxiv.org/abs/1234.5678") == "Research"
    assert classify_source_type("https://docs.example.com/start") == "Documentation"
    assert classify_source_type("https://www.reuters.com/world/example") == "News"
    assert classify_source_type("https://example.com/post") == "Article"


def test_hn_insight_cleans_and_truncates_comment() -> None:
    insight = build_hn_insight(
        (
            "> ```\n"
            "> This comment provides community context about deployment tradeoffs "
            "and practical reliability concerns that are useful but far too long "
            "to include without truncation in the Telegram message.\n"
            "> ```",
        )
    )

    assert insight is not None
    assert insight.startswith("This comment provides community context")
    assert insight.endswith("...")
    assert len(insight) <= 180
    assert "```" not in insight
    assert ">" not in insight


def test_hn_insight_skips_short_comments() -> None:
    assert build_hn_insight(("Nice.", "")) is None
