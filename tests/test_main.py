import src.main as main
from src.hn_client import HNStory
from src.openai_summary_provider import DEFAULT_OPENAI_MODEL
from src.summarizer import build_rule_based_summary


def test_build_summary_provider_defaults_to_rule_based(monkeypatch) -> None:
    monkeypatch.delenv("SUMMARY_PROVIDER", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "unused-secret")

    provider, include_comments = main.build_summary_provider()

    assert provider is build_rule_based_summary
    assert include_comments is False


def test_build_summary_provider_uses_openai_when_enabled(monkeypatch) -> None:
    created = {}

    class FakeOpenAISummaryProvider:
        def __init__(self, api_key: str, model: str, timeout_seconds: int) -> None:
            created["api_key"] = api_key
            created["model"] = model
            created["timeout_seconds"] = timeout_seconds

        def __call__(self, story: HNStory) -> str:
            return "fake summary"

    monkeypatch.setattr(main, "OpenAISummaryProvider", FakeOpenAISummaryProvider)
    monkeypatch.setenv("SUMMARY_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "secret-key")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_TIMEOUT_SECONDS", raising=False)

    provider, include_comments = main.build_summary_provider()

    assert provider(HNStory(1, "Story", None, 1, 1)) == "fake summary"
    assert include_comments is True
    assert created == {
        "api_key": "secret-key",
        "model": DEFAULT_OPENAI_MODEL,
        "timeout_seconds": 20,
    }


def test_build_summary_provider_falls_back_when_openai_key_missing(monkeypatch, capsys) -> None:
    monkeypatch.setenv("SUMMARY_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    provider, include_comments = main.build_summary_provider()
    captured = capsys.readouterr()

    assert provider is build_rule_based_summary
    assert include_comments is False
    assert "OPENAI_API_KEY is missing" in captured.err
