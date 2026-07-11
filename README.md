# AI-Powered Hacker News Reading Decision Engine

Fetches the top Hacker News stories, extracts article evidence, builds Reading Decision fields, and sends a compact Telegram digest.

The project is designed to answer a practical question: should this story be opened now, saved for later, or skipped?

## What It Does

- Collects the current Hacker News top stories.
- Extracts article text, title, published date, and reading time when available.
- Pulls selected Hacker News comments as community evidence.
- Builds a Telegram digest with Preview, HN Insight, and optional Why Trending.
- Uses rule-based fallback output by default.
- Includes an OpenAI Summary Provider implementation for the summary-provider interface.
- Optionally uses NVIDIA Build/NIM for structured Reading Decision fields.
- Runs locally or on a scheduled GitHub Actions workflow.

## Why This Project Exists

Most HN digests repeat metadata that is already visible on Hacker News: title, score, comment count, and link. This project focuses on reading decisions instead.

It combines article extraction, comment context, and conservative fallback behavior so the digest remains useful even when article extraction or an AI provider fails.

## Example Output

```text
📰 HN Daily Top 3 — 2026-07-11

1. Example technical article

Published: 2026-07-10
example.com · 4 min
512 points · 184 comments

Preview:
이 글은 배포 파이프라인에서 병목이 생기는 이유와 이를 줄이기 위한 구조적 변경을 설명합니다.

HN Insight:
댓글에서는 실제 운영 경험, 장애 복구 방식, 기존 도구와의 차이를 중심으로 논의가 이어집니다.

Why Trending:
개발자들이 매일 겪는 배포 안정성과 속도 문제를 구체적인 사례로 다루기 때문입니다.

Source: example.com
Discussion: HN Discussion
```

## Architecture

```text
Hacker News Top Stories
  -> Article Extraction
  -> Reading Decision Provider
  -> Preview
  -> HN Insight
  -> Why Trending
  -> Telegram
```

The production path is intentionally small:

- `src/hn_client.py` fetches top stories and selected comments.
- `src/article_extractor.py` extracts article text and metadata.
- `src/reading_decision.py` builds deterministic Preview and HN Insight fallbacks.
- `src/openai_summary_provider.py` implements the optional OpenAI Summary Provider path.
- `src/nvidia_reading_decision_provider.py` provides optional structured Reading Decision fields.
- `src/message_builder.py` merges provider output with fallback fields and escapes Telegram HTML.
- `src/main.py` wires providers, Hacker News, and Telegram delivery together.

See [docs/architecture.md](docs/architecture.md) for details.

## Reading Decision Fields

- `Preview`: a short article-derived preview when extraction succeeds.
- `HN Insight`: a short summary of useful signals from selected HN comments.
- `Why Trending`: an optional explanation of why the story appears to be drawing HN attention.

Provider output is treated as optional. Missing or invalid fields fall back independently.

## Evidence-First Fallback

The default path is rule-based and does not require a paid model. The notifier still sends a useful digest when:

- article extraction fails
- a page blocks automated access
- HN comments are unavailable
- OpenAI or NVIDIA credentials are missing
- a provider request fails
- provider output is malformed or incomplete

Fallback text is generated from the article extraction result, story metadata, and selected HN comments.

## Provider Support

| Provider mode | Environment value | Role |
| --- | --- | --- |
| Rule-based | `SUMMARY_PROVIDER=rule_based` | Default deterministic summary and Reading Decision fallback |
| OpenAI | `SUMMARY_PROVIDER=openai` | SummaryProvider implementation using HN metadata and selected comments |
| NVIDIA | `SUMMARY_PROVIDER=nvidia` | Structured Preview, HN Insight, and Why Trending |

OpenAI is not a structured Reading Decision provider. NVIDIA Reading Decisions use extracted article text, HN metadata, and selected comments.

## NVIDIA Configuration

Recommended example model:

```text
minimaxai/minimax-m3
```

Required for NVIDIA mode:

```bash
SUMMARY_PROVIDER=nvidia
NVIDIA_API_KEY=your_nvidia_api_key
NVIDIA_MODEL=minimaxai/minimax-m3
NVIDIA_TIMEOUT_SECONDS=60
```

`NVIDIA_TIMEOUT_SECONDS` falls back to `20` in code when unset or invalid. `60` is the recommended operational value used in repository examples.

## Local Development

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Run tests:

```bash
python3 -m pytest
```

Run locally with the rule-based path:

```bash
TELEGRAM_BOT_TOKEN="your-bot-token" TELEGRAM_CHAT_ID="your-chat-id" python3 -m src.main
```

Run a NVIDIA dry run without sending Telegram messages:

```bash
NVIDIA_API_KEY="..." NVIDIA_MODEL="minimaxai/minimax-m3" python3 scripts/test_nvidia_reading_decision.py
```

Use `HN_STORY_ID` to dry-run a fixed story:

```bash
HN_STORY_ID="123456" NVIDIA_API_KEY="..." NVIDIA_MODEL="minimaxai/minimax-m3" python3 scripts/test_nvidia_reading_decision.py
```

## GitHub Actions

The workflow in [.github/workflows/daily_hn.yml](.github/workflows/daily_hn.yml):

- runs daily at `00:00 UTC`, which is `09:00 KST`
- supports manual dispatch
- installs Python dependencies
- runs `python -m pytest`
- sends the Telegram notification only after tests pass

Required secrets:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Optional secrets and variables are documented in [docs/specification.md](docs/specification.md).

## Testing

The test suite covers:

- Hacker News item parsing and comment extraction
- article extraction behavior
- rule-based summaries
- OpenAI summary fallback
- NVIDIA Reading Decision parsing and fallback
- Telegram message formatting
- provider selection in `src/main.py`
- the NVIDIA dry-run script

Run:

```bash
python3 -m pytest
```

## Model Evaluation

The NVIDIA model choice and dry-run comparison are documented in [docs/model-evaluation.md](docs/model-evaluation.md).

The default NVIDIA example model is:

```text
minimaxai/minimax-m3
```

## Limitations

- Article extraction depends on remote pages and may fail on blocked, dynamic, or non-HTML content.
- Published dates are best-effort metadata from extracted article pages.
- HN Insight depends on available top-level comments and may be omitted.
- NVIDIA output is constrained and escaped, but still treated as optional provider output.
- The current model evaluation is a small dry-run comparison, not a statistically broad benchmark.
- The project does not use a database, duplicate suppression, user accounts, or a web UI.

## Documentation

- [Architecture](docs/architecture.md)
- [Specification](docs/specification.md)
- [Implementation Plan](docs/implementation-plan.md)
- [Model Evaluation](docs/model-evaluation.md)
- [Release Notes](docs/release-notes.md)
- [Experiments](experiments/README.md)
