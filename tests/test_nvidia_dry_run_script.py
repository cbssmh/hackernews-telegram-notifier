import scripts.test_nvidia_reading_decision as dry_run
from src.article_extractor import ArticleExtraction
from src.hn_client import HNStory
from src.reading_decision import ReadingDecision


def test_dry_run_timeout_helper_uses_default_for_missing_or_invalid_values(monkeypatch) -> None:
    for value in (None, "", "   ", "not-int", "0", "-1"):
        if value is None:
            monkeypatch.delenv("NVIDIA_TIMEOUT_SECONDS", raising=False)
        else:
            monkeypatch.setenv("NVIDIA_TIMEOUT_SECONDS", value)

        assert dry_run._timeout_seconds_from_env("NVIDIA_TIMEOUT_SECONDS") == 20


def test_dry_run_timeout_helper_accepts_positive_integer(monkeypatch) -> None:
    monkeypatch.setenv("NVIDIA_TIMEOUT_SECONDS", " 7 ")

    assert dry_run._timeout_seconds_from_env("NVIDIA_TIMEOUT_SECONDS") == 7


def test_dry_run_exits_before_network_when_api_key_is_missing(monkeypatch, capsys) -> None:
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.setenv("NVIDIA_MODEL", "nvidia/model")

    assert dry_run.main() == 1
    captured = capsys.readouterr()

    assert "NVIDIA_API_KEY is missing." in captured.err
    assert "nvidia/model" not in captured.err


def test_dry_run_exits_before_network_when_model_is_blank(monkeypatch, capsys) -> None:
    monkeypatch.setenv("NVIDIA_API_KEY", "secret-key")
    monkeypatch.setenv("NVIDIA_MODEL", "   ")

    assert dry_run.main() == 1
    captured = capsys.readouterr()

    assert "NVIDIA_MODEL is missing." in captured.err
    assert "secret-key" not in captured.err


def test_dry_run_exits_before_network_when_story_id_is_invalid(monkeypatch, capsys) -> None:
    monkeypatch.setenv("NVIDIA_API_KEY", "secret-key")
    monkeypatch.setenv("NVIDIA_MODEL", "nvidia/model")
    monkeypatch.setenv("HN_STORY_ID", "not-an-id")

    assert dry_run.main() == 1
    captured = capsys.readouterr()

    assert "HN_STORY_ID must be a positive integer." in captured.err
    assert "secret-key" not in captured.err


def test_dry_run_selects_first_story_with_successful_article(monkeypatch) -> None:
    monkeypatch.delenv("HN_STORY_ID", raising=False)
    stories = [
        HNStory(1, "No URL", None, 10, 1),
        HNStory(2, "Extraction Fails", "https://example.com/fail", 10, 1),
        HNStory(3, "Empty Article", "https://example.com/empty", 10, 1),
        HNStory(4, "Good Article", "https://example.com/good", 10, 1),
    ]

    def fake_extract_article(url: str) -> ArticleExtraction:
        if url.endswith("/fail"):
            return ArticleExtraction(success=False, error="blocked")
        if url.endswith("/empty"):
            return ArticleExtraction(success=True, text="")
        return ArticleExtraction(success=True, text="Useful article text.")

    monkeypatch.setattr(dry_run, "extract_article", fake_extract_article)

    selected = dry_run._select_story_with_article(stories)

    assert selected is not None
    story, article = selected
    assert story.title == "Good Article"
    assert article.text == "Useful article text."


def test_dry_run_returns_none_when_no_extractable_article(monkeypatch) -> None:
    monkeypatch.delenv("HN_STORY_ID", raising=False)
    stories = [
        HNStory(1, "No URL", None, 10, 1),
        HNStory(2, "Extraction Fails", "https://example.com/fail", 10, 1),
    ]

    monkeypatch.setattr(
        dry_run,
        "extract_article",
        lambda url: ArticleExtraction(success=False, error="blocked"),
    )

    assert dry_run._select_story_with_article(stories) is None


def test_dry_run_calls_provider_once_for_selected_article(monkeypatch, capsys) -> None:
    monkeypatch.delenv("HN_STORY_ID", raising=False)
    calls = []

    class FakeHNClient:
        def fetch_top_stories(self, **kwargs):
            return [
                HNStory(1, "No URL", None, 10, 1),
                HNStory(
                    2,
                    "Good Article",
                    "https://example.com/good",
                    100,
                    20,
                    top_comments=("Useful comment",),
                ),
            ]

    class FakeNVIDIAReadingDecisionProvider:
        def __init__(self, api_key: str, model: str, timeout_seconds: int) -> None:
            self.timeout_seconds = timeout_seconds

        def __call__(self, decision_input):
            calls.append(decision_input)
            return ReadingDecision(
                preview="Preview",
                hn_insight="Insight",
                why_trending="Trending",
            )

    monkeypatch.setenv("NVIDIA_API_KEY", "secret-key")
    monkeypatch.setenv("NVIDIA_MODEL", "nvidia/model")
    monkeypatch.setattr(dry_run, "HNClient", FakeHNClient)
    monkeypatch.setattr(
        dry_run,
        "extract_article",
        lambda url: ArticleExtraction(success=True, text="Useful article text."),
    )
    monkeypatch.setattr(
        dry_run,
        "NVIDIAReadingDecisionProvider",
        FakeNVIDIAReadingDecisionProvider,
    )

    assert dry_run.main() == 0
    captured = capsys.readouterr()

    assert len(calls) == 1
    assert calls[0].story.title == "Good Article"
    assert calls[0].article.text == "Useful article text."
    assert "Model: nvidia/model" in captured.out
    assert "Story title: Good Article" in captured.out
    assert "Preview: Preview" in captured.out
    assert "secret-key" not in captured.out
    assert "secret-key" not in captured.err


def test_dry_run_uses_fixed_story_id_and_supplies_comments(monkeypatch, capsys) -> None:
    calls = []
    fetch_top_called = False
    comment_limits = []

    class FakeHNClient:
        def fetch_top_stories(self, **kwargs):
            nonlocal fetch_top_called
            fetch_top_called = True
            return []

        def fetch_item(self, item_id: int):
            assert item_id == 123
            return {
                "id": 123,
                "type": "story",
                "title": "Fixed Story",
                "url": "https://example.com/fixed",
                "score": 200,
                "descendants": 50,
                "kids": [1, 2, 3, 4],
            }

        def fetch_top_comments(self, item, limit: int = 3):
            comment_limits.append(limit)
            return ("First comment", "Second comment", "Third comment")

    class FakeNVIDIAReadingDecisionProvider:
        def __init__(self, api_key: str, model: str, timeout_seconds: int) -> None:
            self.model = model

        def __call__(self, decision_input):
            calls.append(decision_input)
            return ReadingDecision(preview="Preview")

    monkeypatch.setenv("NVIDIA_API_KEY", "secret-key")
    monkeypatch.setenv("NVIDIA_MODEL", "nvidia/model-a")
    monkeypatch.setenv("HN_STORY_ID", "123")
    monkeypatch.setattr(dry_run, "HNClient", FakeHNClient)
    monkeypatch.setattr(
        dry_run,
        "extract_article",
        lambda url: ArticleExtraction(success=True, text="Fixed article text."),
    )
    monkeypatch.setattr(
        dry_run,
        "NVIDIAReadingDecisionProvider",
        FakeNVIDIAReadingDecisionProvider,
    )

    assert dry_run.main() == 0
    captured = capsys.readouterr()

    assert fetch_top_called is False
    assert comment_limits == [3]
    assert len(calls) == 1
    assert calls[0].story.id == 123
    assert calls[0].story.top_comments == ("First comment", "Second comment", "Third comment")
    assert calls[0].article.text == "Fixed article text."
    assert "Model: nvidia/model-a" in captured.out
    assert "Story title: Fixed Story" in captured.out
