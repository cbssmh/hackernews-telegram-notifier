from src.hn_client import HNStory
from src.summarizer import build_rule_based_summary


BANNED_GENERIC_PHRASES = (
    "기술/스타트업 관련 글로 보입니다",
    "출처의 기술 글로 보입니다",
    "출처의 기술/스타트업 관련 글로 보입니다",
)


def test_self_title_explains_top_level_domain_or_self_hosting() -> None:
    story = HNStory(
        id=1,
        title="The .self top-level domain",
        url="https://example.com/self-tld",
        score=80,
        descendants=20,
    )

    summary = build_rule_based_summary(story)

    assert "새 최상위 도메인" in summary or "self-hosting" in summary
    assert_no_banned_generic_phrases(summary)


def test_qwen_local_development_title_explains_model_performance_balance() -> None:
    story = HNStory(
        id=2,
        title="Qwen for local development: balancing model size and performance",
        url="https://example.com/qwen-local-development",
        score=150,
        descendants=40,
    )

    summary = build_rule_based_summary(story)

    assert "로컬 개발" in summary
    assert "모델" in summary
    assert "성능의 균형" in summary
    assert_no_banned_generic_phrases(summary)


def test_free_the_icons_title_does_not_use_generic_domain_wording() -> None:
    story = HNStory(
        id=3,
        title="Free the Icons",
        url="https://example.com/free-the-icons",
        score=120,
        descendants=35,
    )

    summary = build_rule_based_summary(story)

    assert "아이콘" in summary
    assert "자유롭게" in summary
    assert_no_banned_generic_phrases(summary)


def test_github_url_hints_at_open_source_project_when_title_is_ambiguous() -> None:
    story = HNStory(
        id=4,
        title="New Developer Tool",
        url="https://github.com/example/project",
        score=90,
        descendants=15,
    )

    summary = build_rule_based_summary(story)

    assert "오픈소스" in summary
    assert "프로젝트" in summary
    assert_no_banned_generic_phrases(summary)


def test_default_no_comment_behavior_interprets_title_without_engagement_sentence() -> None:
    story = HNStory(
        id=5,
        title="How to manage notes across devices",
        url=None,
        score=100,
        descendants=50,
    )

    summary = build_rule_based_summary(story)

    assert "How to manage notes across devices" in summary
    assert "방법과 판단 기준" in summary
    assert summary.count(".") == 1
    assert_no_banned_generic_phrases(summary)


def test_high_engagement_adds_short_second_sentence() -> None:
    story = HNStory(
        id=6,
        title="Major AI Release",
        url="https://example.com/ai",
        score=800,
        descendants=400,
    )

    summary = build_rule_based_summary(story)

    assert "Major AI Release" in summary
    assert "HN에서 반응이 커서" in summary
    assert summary.count(".") == 2
    assert_no_banned_generic_phrases(summary)


def assert_no_banned_generic_phrases(summary: str) -> None:
    for phrase in BANNED_GENERIC_PHRASES:
        assert phrase not in summary
