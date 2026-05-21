from __future__ import annotations

import os
import sys

from src.hn_client import HNClient
from src.message_builder import SummaryProvider, build_daily_message
from src.openai_summary_provider import DEFAULT_OPENAI_MODEL, OpenAISummaryProvider
from src.summarizer import build_rule_based_summary
from src.telegram_client import TelegramClient


def main() -> None:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    summary_provider, include_comments = build_summary_provider()

    hn_client = HNClient()
    telegram_client = TelegramClient(
        bot_token=bot_token,
        chat_id=chat_id,
    )

    stories = hn_client.fetch_top_stories(
        limit=3,
        include_comments=include_comments,
        comment_limit=_get_int_env("OPENAI_MAX_COMMENTS", 3),
    )
    message = build_daily_message(stories, summary_provider=summary_provider)

    telegram_client.send_message(message)

    print(f"Sent HN daily notification. story_count={len(stories)}")


def build_summary_provider() -> tuple[SummaryProvider, bool]:
    provider_name = os.getenv("SUMMARY_PROVIDER", "rule_based").strip().lower()
    if provider_name != "openai":
        return build_rule_based_summary, False

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        print(
            "SUMMARY_PROVIDER=openai but OPENAI_API_KEY is missing; using rule-based summaries.",
            file=sys.stderr,
        )
        return build_rule_based_summary, False

    model = os.getenv("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL
    timeout_seconds = _get_int_env("OPENAI_TIMEOUT_SECONDS", 20)

    return OpenAISummaryProvider(
        api_key=api_key,
        model=model,
        timeout_seconds=timeout_seconds,
    ), True


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


if __name__ == "__main__":
    main()
