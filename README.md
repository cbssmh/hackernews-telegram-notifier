# HN Daily Top 3 Telegram Notifier

Fetches the top Hacker News stories, builds a deterministic reading-decision message, and sends the result to Telegram.

## Setup

1. Create a Telegram bot with BotFather and copy the bot token.
2. Get the target chat ID for the Telegram chat that should receive notifications.
3. In GitHub, open the repository settings and add these Actions secrets:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. The workflow runs every day at 09:00 KST, which is 00:00 UTC.
5. To run it manually, open the Actions tab, select `Daily HN Telegram Notification`, and choose `Run workflow`.

## Local Development

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run tests:

```bash
python -m pytest
```

Run the notifier locally:

```bash
TELEGRAM_BOT_TOKEN="your-bot-token" TELEGRAM_CHAT_ID="your-chat-id" python -m src.main
```

## Notes

- No database is used.
- No Docker setup is required.
- Messages are deterministic and evidence-based by default.
- Article preview extraction falls back gracefully when unavailable.

## Optional OpenAI Summaries

To enable OpenAI summaries in GitHub Actions, add:

- Actions secret: `OPENAI_API_KEY`
- Actions variable: `SUMMARY_PROVIDER=openai`

Optional Actions variables:

- `OPENAI_MODEL` defaults to `gpt-5-nano`
- `OPENAI_MAX_COMMENTS` defaults to `3`
- `OPENAI_TIMEOUT_SECONDS` defaults to `20`

OpenAI summaries use only Hacker News metadata and top HN comments. Article bodies are not scraped. If OpenAI fails, the notifier falls back to rule-based summaries for that story.

## Optional NVIDIA Reading Decisions

To enable NVIDIA Build/NIM reading decisions, add:

Secret:

- `NVIDIA_API_KEY`

Variables:

- `SUMMARY_PROVIDER=nvidia`
- `NVIDIA_MODEL=minimaxai/minimax-m3`
- `NVIDIA_TIMEOUT_SECONDS=60`

NVIDIA reading decisions use extracted article text, Hacker News metadata, and top HN comments to generate the Preview, HN Insight, and optional Why Trending sections. If NVIDIA is unavailable or returns incomplete fields, the notifier automatically falls back to the existing non-LLM Preview and HN Insight.
