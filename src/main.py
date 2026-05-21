from __future__ import annotations

import os

from src.hn_client import HNClient
from src.message_builder import build_daily_message
from src.telegram_client import TelegramClient


def main() -> None:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    hn_client = HNClient()
    telegram_client = TelegramClient(
        bot_token=bot_token,
        chat_id=chat_id,
    )

    stories = hn_client.fetch_top_stories(limit=3)
    message = build_daily_message(stories)

    telegram_client.send_message(message)

    print(f"Sent HN daily notification. story_count={len(stories)}")


if __name__ == "__main__":
    main()