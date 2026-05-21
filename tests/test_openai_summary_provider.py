import requests

from src.hn_client import HNStory
from src.openai_summary_provider import OpenAISummaryProvider


def test_openai_summary_provider_uses_story_metadata_and_comments(monkeypatch) -> None:
    captured_request = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"output_text": "OpenAI summary"}

    def fake_post(*args, **kwargs) -> FakeResponse:
        captured_request["headers"] = kwargs["headers"]
        captured_request["json"] = kwargs["json"]
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)

    story = HNStory(
        id=123,
        title="Example Story",
        url="https://example.com/post",
        score=100,
        descendants=20,
        top_comments=("Great context", "Useful detail"),
    )
    provider = OpenAISummaryProvider(api_key="secret-key", model="test-model")

    assert provider(story) == "OpenAI summary"
    assert captured_request["headers"]["Authorization"] == "Bearer secret-key"
    assert captured_request["json"]["model"] == "test-model"
    assert "Example Story" in captured_request["json"]["input"]
    assert "example.com" in captured_request["json"]["input"]
    assert "Score: 100" in captured_request["json"]["input"]
    assert "Comment count: 20" in captured_request["json"]["input"]
    assert "Great context" in captured_request["json"]["input"]


def test_openai_summary_provider_falls_back_without_leaking_secret(monkeypatch, capsys) -> None:
    api_key = "secret-key"

    class FakeResponse:
        status_code = 429

    def fake_post(*args, **kwargs):
        raise requests.HTTPError(
            f"429 Client Error for url with {api_key}",
            response=FakeResponse(),
        )

    monkeypatch.setattr(requests, "post", fake_post)

    story = HNStory(
        id=123,
        title="Example Story",
        url="https://example.com/post",
        score=100,
        descendants=20,
    )
    provider = OpenAISummaryProvider(api_key=api_key)

    summary = provider(story)
    captured = capsys.readouterr()

    assert "example.com 출처" in summary
    assert "OpenAI summary failed" in captured.err
    assert api_key not in captured.err
