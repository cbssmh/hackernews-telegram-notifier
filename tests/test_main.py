import src.main as main
from src.hn_client import HNStory
from src.openai_summary_provider import DEFAULT_OPENAI_MODEL
from src.summarizer import build_rule_based_summary


def test_build_summary_provider_defaults_to_rule_based(monkeypatch) -> None:
    monkeypatch.delenv("SUMMARY_PROVIDER", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "unused-secret")

    provider, include_comments = main.build_summary_provider()

    assert provider is build_rule_based_summary
    assert include_comments is True


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
    assert include_comments is True
    assert "OPENAI_API_KEY is missing" in captured.err


def test_build_reading_decision_provider_defaults_to_none(monkeypatch) -> None:
    monkeypatch.delenv("SUMMARY_PROVIDER", raising=False)

    assert main.build_reading_decision_provider() is None


def test_build_reading_decision_provider_uses_nvidia_when_enabled(monkeypatch) -> None:
    created = {}

    class FakeNVIDIAReadingDecisionProvider:
        def __init__(self, api_key: str, model: str, timeout_seconds: int) -> None:
            created["api_key"] = api_key
            created["model"] = model
            created["timeout_seconds"] = timeout_seconds

    monkeypatch.setattr(main, "NVIDIAReadingDecisionProvider", FakeNVIDIAReadingDecisionProvider)
    monkeypatch.setenv("SUMMARY_PROVIDER", "nvidia")
    monkeypatch.setenv("NVIDIA_API_KEY", "secret-key")
    monkeypatch.setenv("NVIDIA_MODEL", "nvidia/model")
    monkeypatch.delenv("NVIDIA_TIMEOUT_SECONDS", raising=False)

    provider = main.build_reading_decision_provider()

    assert isinstance(provider, FakeNVIDIAReadingDecisionProvider)
    assert created == {
        "api_key": "secret-key",
        "model": "nvidia/model",
        "timeout_seconds": 20,
    }


def test_build_reading_decision_provider_uses_timeout_override(monkeypatch) -> None:
    created = {}

    class FakeNVIDIAReadingDecisionProvider:
        def __init__(self, api_key: str, model: str, timeout_seconds: int) -> None:
            created["timeout_seconds"] = timeout_seconds

    monkeypatch.setattr(main, "NVIDIAReadingDecisionProvider", FakeNVIDIAReadingDecisionProvider)
    monkeypatch.setenv("SUMMARY_PROVIDER", "nvidia")
    monkeypatch.setenv("NVIDIA_API_KEY", "secret-key")
    monkeypatch.setenv("NVIDIA_MODEL", "nvidia/model")
    monkeypatch.setenv("NVIDIA_TIMEOUT_SECONDS", "9")

    main.build_reading_decision_provider()

    assert created["timeout_seconds"] == 9


def test_build_reading_decision_provider_uses_default_timeout_for_empty_value(monkeypatch) -> None:
    created = {}

    class FakeNVIDIAReadingDecisionProvider:
        def __init__(self, api_key: str, model: str, timeout_seconds: int) -> None:
            created["timeout_seconds"] = timeout_seconds

    monkeypatch.setattr(main, "NVIDIAReadingDecisionProvider", FakeNVIDIAReadingDecisionProvider)
    monkeypatch.setenv("SUMMARY_PROVIDER", "nvidia")
    monkeypatch.setenv("NVIDIA_API_KEY", "secret-key")
    monkeypatch.setenv("NVIDIA_MODEL", "nvidia/model")
    monkeypatch.setenv("NVIDIA_TIMEOUT_SECONDS", "")

    main.build_reading_decision_provider()

    assert created["timeout_seconds"] == 20


def test_build_reading_decision_provider_falls_back_when_nvidia_key_missing(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv("SUMMARY_PROVIDER", "nvidia")
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.setenv("NVIDIA_MODEL", "nvidia/model")

    provider = main.build_reading_decision_provider()
    captured = capsys.readouterr()

    assert provider is None
    assert "NVIDIA_API_KEY" in captured.err


def test_build_reading_decision_provider_falls_back_when_nvidia_key_is_blank(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv("SUMMARY_PROVIDER", "nvidia")
    monkeypatch.setenv("NVIDIA_API_KEY", "   ")
    monkeypatch.setenv("NVIDIA_MODEL", "nvidia/model")

    provider = main.build_reading_decision_provider()
    captured = capsys.readouterr()

    assert provider is None
    assert "NVIDIA_API_KEY" in captured.err
    assert "nvidia/model" not in captured.err


def test_build_reading_decision_provider_falls_back_when_nvidia_model_missing(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv("SUMMARY_PROVIDER", "nvidia")
    monkeypatch.setenv("NVIDIA_API_KEY", "secret-key")
    monkeypatch.delenv("NVIDIA_MODEL", raising=False)

    provider = main.build_reading_decision_provider()
    captured = capsys.readouterr()

    assert provider is None
    assert "NVIDIA_MODEL" in captured.err
    assert "secret-key" not in captured.err


def test_build_reading_decision_provider_falls_back_when_nvidia_model_is_blank(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv("SUMMARY_PROVIDER", "nvidia")
    monkeypatch.setenv("NVIDIA_API_KEY", "secret-key")
    monkeypatch.setenv("NVIDIA_MODEL", "   ")

    provider = main.build_reading_decision_provider()
    captured = capsys.readouterr()

    assert provider is None
    assert "NVIDIA_MODEL" in captured.err
    assert "secret-key" not in captured.err


def test_build_summary_provider_keeps_comments_for_nvidia(monkeypatch) -> None:
    monkeypatch.setenv("SUMMARY_PROVIDER", "nvidia")

    provider, include_comments = main.build_summary_provider()

    assert provider is build_rule_based_summary
    assert include_comments is True


def test_main_passes_nvidia_reading_decision_provider_to_message_builder(monkeypatch) -> None:
    captured = {}

    class FakeHNClient:
        def fetch_top_stories(self, **kwargs):
            captured["fetch_top_stories_kwargs"] = kwargs
            return [HNStory(1, "Story", "https://example.com/post", 100, 20)]

    class FakeTelegramClient:
        def __init__(self, bot_token: str, chat_id: str) -> None:
            captured["bot_token"] = bot_token
            captured["chat_id"] = chat_id

        def send_message(self, message: str) -> None:
            captured["sent_message"] = message

    class FakeNVIDIAReadingDecisionProvider:
        def __init__(self, api_key: str, model: str, timeout_seconds: int) -> None:
            captured["nvidia_api_key"] = api_key
            captured["nvidia_model"] = model
            captured["nvidia_timeout_seconds"] = timeout_seconds

    def fake_build_daily_message(stories, summary_provider, reading_decision_provider):
        captured["stories"] = stories
        captured["summary_provider"] = summary_provider
        captured["reading_decision_provider"] = reading_decision_provider
        return "message"

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "telegram-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat-id")
    monkeypatch.setenv("SUMMARY_PROVIDER", "nvidia")
    monkeypatch.setenv("NVIDIA_API_KEY", "secret-key")
    monkeypatch.setenv("NVIDIA_MODEL", "minimaxai/minimax-m3")
    monkeypatch.setenv("NVIDIA_TIMEOUT_SECONDS", "60")
    monkeypatch.setattr(main, "HNClient", FakeHNClient)
    monkeypatch.setattr(main, "TelegramClient", FakeTelegramClient)
    monkeypatch.setattr(main, "NVIDIAReadingDecisionProvider", FakeNVIDIAReadingDecisionProvider)
    monkeypatch.setattr(main, "build_daily_message", fake_build_daily_message)

    main.main()

    assert captured["fetch_top_stories_kwargs"]["include_comments"] is True
    assert captured["nvidia_model"] == "minimaxai/minimax-m3"
    assert captured["nvidia_timeout_seconds"] == 60
    assert isinstance(captured["reading_decision_provider"], FakeNVIDIAReadingDecisionProvider)
    assert captured["summary_provider"] is build_rule_based_summary
    assert captured["sent_message"] == "message"
