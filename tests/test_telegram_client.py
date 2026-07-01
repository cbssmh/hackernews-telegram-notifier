import requests

from src.telegram_client import TelegramClient


def test_send_message_raises_sanitized_error(monkeypatch) -> None:
    bot_token = "secret-token"
    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    class FakeResponse:
        status_code = 401

        def raise_for_status(self) -> None:
            raise requests.HTTPError(
                f"401 Client Error: Unauthorized for url: {telegram_url}",
                response=self,
            )

    def fake_post(*args, **kwargs) -> FakeResponse:
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)

    client = TelegramClient(bot_token=bot_token, chat_id="123")

    try:
        client.send_message("hello")
    except RuntimeError as exc:
        error_message = str(exc)
    else:
        raise AssertionError("Expected RuntimeError")

    assert "Telegram sendMessage request failed" in error_message
    assert bot_token not in error_message
    assert telegram_url not in error_message


def test_send_message_uses_html_parse_mode(monkeypatch) -> None:
    captured = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

    def fake_post(*args, **kwargs) -> FakeResponse:
        captured["json"] = kwargs["json"]
        return FakeResponse()

    monkeypatch.setattr(requests, "post", fake_post)

    client = TelegramClient(bot_token="secret-token", chat_id="123")
    client.send_message('<a href="https://example.com/post">example.com</a>')

    assert captured["json"]["parse_mode"] == "HTML"
