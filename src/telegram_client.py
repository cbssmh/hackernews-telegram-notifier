from __future__ import annotations

import requests


class TelegramClient:
    def __init__(self, bot_token: str, chat_id: str, timeout_seconds: int = 10) -> None:
        if not bot_token:
            raise ValueError("Telegram bot token is required.")

        if not chat_id:
            raise ValueError("Telegram chat ID is required.")

        self.bot_token = bot_token
        self.chat_id = chat_id
        self.timeout_seconds = timeout_seconds

    def send_message(self, text: str) -> None:
        if not text.strip():
            raise ValueError("Telegram message text must not be empty.")

        response = requests.post(
            f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
            json={
                "chat_id": self.chat_id,
                "text": text,
                "disable_web_page_preview": True,
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()