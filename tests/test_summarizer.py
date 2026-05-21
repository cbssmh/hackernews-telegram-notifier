from src.hn_client import HNStory
from src.summarizer import build_rule_based_summary


def test_github_summary() -> None:
    story = HNStory(
        id=1,
        title="New Developer Tool",
        url="https://github.com/example/project",
        score=300,
        descendants=120,
    )

    summary = build_rule_based_summary(story)

    assert "오픈소스" in summary
    assert "의미 있는 관심" in summary


def test_hn_discussion_summary() -> None:
    story = HNStory(
        id=2,
        title="Ask HN: How do you manage notes?",
        url=None,
        score=100,
        descendants=50,
    )

    summary = build_rule_based_summary(story)

    assert "HN 토론 중심" in summary


def test_high_engagement_summary() -> None:
    story = HNStory(
        id=3,
        title="Major AI Release",
        url="https://example.com/ai",
        score=800,
        descendants=400,
    )

    summary = build_rule_based_summary(story)

    assert "매우 높은 관심" in summary