from __future__ import annotations

import requests

from src.article_extractor import ArticleExtraction
from src.hn_client import HNStory
from src.nvidia_reading_decision_provider import (
    ARTICLE_TEXT_MAX_CHARS,
    COMMENT_MAX_CHARS,
    MAX_HN_INSIGHT_CHARS,
    MAX_PREVIEW_CHARS,
    MAX_WHY_TRENDING_CHARS,
    NVIDIA_CHAT_COMPLETIONS_URL,
    NVIDIAReadingDecisionProvider,
)
from src.reading_decision import ReadingDecisionInput


def test_nvidia_provider_calls_chat_completions_endpoint(monkeypatch, capsys) -> None:
    captured_request = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"preview":"요약",'
                                '"hn_insight":"댓글 쟁점",'
                                '"why_trending":"화제 이유"}'
                            )
                        }
                    }
                ]
            }

    def fake_post(*args, **kwargs) -> FakeResponse:
        captured_request["url"] = args[0]
        captured_request["headers"] = kwargs["headers"]
        captured_request["json"] = kwargs["json"]
        captured_request["timeout"] = kwargs["timeout"]
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)

    provider = NVIDIAReadingDecisionProvider(
        api_key="secret-key",
        model="nvidia/model",
        timeout_seconds=7,
    )
    decision = provider(_build_input())
    captured = capsys.readouterr()

    assert decision.preview == "요약"
    assert decision.hn_insight == "댓글 쟁점"
    assert decision.why_trending == "화제 이유"
    assert "NVIDIA response diagnostics" not in captured.err
    assert captured_request["url"] == NVIDIA_CHAT_COMPLETIONS_URL
    assert captured_request["headers"]["Authorization"] == "Bearer secret-key"
    assert captured_request["json"]["model"] == "nvidia/model"
    assert captured_request["json"]["max_tokens"] == 800
    assert captured_request["json"]["reasoning_effort"] == "none"
    assert captured_request["json"]["stream"] is False
    assert captured_request["timeout"] == 7

    system_content = captured_request["json"]["messages"][0]["content"]
    assert "If article extraction failed or article text is empty" in system_content
    assert "preview must be an empty string" in system_content
    assert "hn_insight and why_trending fields may be generated from comments and metadata" in system_content
    assert "Do not add evaluative claims" in system_content
    assert "cutting-edge" in system_content
    assert "world-first" in system_content

    user_content = captured_request["json"]["messages"][1]["content"]
    assert "Title: Example Story" in user_content
    assert "Source domain: example.com" in user_content
    assert "Score: 123" in user_content
    assert "Comment count: 45" in user_content
    assert "Article published date: 2026-05-20" in user_content
    assert "Article extraction success: True" in user_content
    assert "Article body with concrete details" in user_content
    assert "First useful comment" in user_content


def test_nvidia_provider_parses_json_code_fence(monkeypatch) -> None:
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: _fake_response(
            '```json\n{"preview":"요약","hn_insight":"댓글","why_trending":"이유"}\n```'
        ),
    )

    provider = NVIDIAReadingDecisionProvider(api_key="secret-key", model="nvidia/model")

    assert provider(_build_input()).why_trending == "이유"


def test_nvidia_provider_normalizes_missing_and_non_string_fields(monkeypatch) -> None:
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: _fake_response('{"preview":"요약","hn_insight":10}'),
    )

    provider = NVIDIAReadingDecisionProvider(api_key="secret-key", model="nvidia/model")
    decision = provider(_build_input())

    assert decision.preview == "요약"
    assert decision.hn_insight == ""
    assert decision.why_trending == ""


def test_nvidia_provider_limits_output_fields_independently(monkeypatch) -> None:
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: _fake_response(
            (
                '{"preview":"'
                + ("가" * 300)
                + '","hn_insight":"'
                + ("나" * 300)
                + '","why_trending":"'
                + ("다" * 300)
                + '"}'
            )
        ),
    )

    provider = NVIDIAReadingDecisionProvider(api_key="secret-key", model="nvidia/model")
    decision = provider(_build_input())

    assert len(decision.preview) == MAX_PREVIEW_CHARS
    assert len(decision.hn_insight) == MAX_HN_INSIGHT_CHARS
    assert len(decision.why_trending) == MAX_WHY_TRENDING_CHARS


def test_nvidia_provider_returns_empty_decision_for_malformed_json(monkeypatch) -> None:
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: _fake_response("not json"),
    )

    provider = NVIDIAReadingDecisionProvider(api_key="secret-key", model="nvidia/model")

    assert provider(_build_input()).preview == ""
    assert provider(_build_input()).hn_insight == ""
    assert provider(_build_input()).why_trending == ""


def test_nvidia_provider_returns_empty_decision_for_length_reasoning_without_json(monkeypatch) -> None:
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: _fake_response(
            "I need to reason about the article before producing the JSON.",
            finish_reason="length",
            reasoning_content="I need to reason about the article before producing the JSON.",
        ),
    )

    provider = NVIDIAReadingDecisionProvider(api_key="secret-key", model="nvidia/model")
    decision = provider(_build_input())

    assert decision.preview == ""
    assert decision.hn_insight == ""
    assert decision.why_trending == ""


def test_nvidia_provider_returns_empty_decision_for_http_error(monkeypatch, capsys) -> None:
    api_key = "secret-key"

    class FakeResponse:
        status_code = 429

        def raise_for_status(self) -> None:
            raise requests.HTTPError(
                f"429 Client Error for url with {api_key}",
                response=self,
            )

    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: FakeResponse())

    provider = NVIDIAReadingDecisionProvider(api_key=api_key, model="nvidia/model")
    decision = provider(_build_input())
    captured = capsys.readouterr()

    assert decision.preview == ""
    assert "NVIDIA reading decision failed" in captured.err
    assert "status_code=429" in captured.err
    assert api_key not in captured.err


def test_nvidia_provider_limits_long_article_and_comments(monkeypatch) -> None:
    captured_request = {}

    def fake_post(*args, **kwargs):
        captured_request["json"] = kwargs["json"]
        return _fake_response('{"preview":"","hn_insight":"","why_trending":""}')

    monkeypatch.setattr(requests, "post", fake_post)

    story = HNStory(
        id=123,
        title="Long Story",
        url="https://example.com/post",
        score=100,
        descendants=20,
        top_comments=("B" * COMMENT_MAX_CHARS + "COMMENTTAIL",),
    )
    article = ArticleExtraction(
        success=True,
        text="A" * ARTICLE_TEXT_MAX_CHARS + "ARTICLETAIL",
    )
    provider = NVIDIAReadingDecisionProvider(api_key="secret-key", model="nvidia/model")

    provider(ReadingDecisionInput(story=story, article=article))

    user_content = captured_request["json"]["messages"][1]["content"]
    assert "ARTICLETAIL" not in user_content
    assert "COMMENTTAIL" not in user_content


def _build_input() -> ReadingDecisionInput:
    story = HNStory(
        id=123,
        title="Example Story",
        url="https://example.com/post",
        score=123,
        descendants=45,
        top_comments=("First useful comment", "Second useful comment"),
    )
    article = ArticleExtraction(
        success=True,
        title="Extracted Title",
        text="Article body with concrete details for the model.",
        word_count=120,
        published_date="2026-05-20",
    )
    return ReadingDecisionInput(story=story, article=article)


def _fake_response(
    content: str,
    finish_reason: str | None = None,
    reasoning_content: str | None = None,
):
    class FakeResponse:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            message = {"content": content}
            if reasoning_content is not None:
                message["reasoning_content"] = reasoning_content

            choice = {"message": message}
            if finish_reason is not None:
                choice["finish_reason"] = finish_reason

            return {"choices": [choice]}

    return FakeResponse()
