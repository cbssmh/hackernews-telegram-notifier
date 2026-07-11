# Architecture

This project is a small scheduled pipeline for producing Telegram Reading Decisions from Hacker News stories.

## Pipeline

```text
Hacker News Top Stories
  -> HN story filtering
  -> HN comment collection
  -> Article Extraction
  -> Summary Provider
  -> Reading Decision Provider
  -> Message Builder
  -> Telegram
```

## Components

`src/main.py`

Wires environment variables, providers, Hacker News collection, message building, and Telegram delivery.

`src/hn_client.py`

Fetches Hacker News top story IDs, story details, and selected top-level comments. Invalid stories, deleted stories, dead stories, and failed item fetches are skipped.

`src/article_extractor.py`

Fetches article URLs and extracts plain text, title, word count, and published date using `trafilatura`. Extraction failures return structured fallback state instead of raising into message generation.

`src/reading_decision.py`

Defines `ReadingDecisionInput`, `ReadingDecision`, and `ReadingDecisionProvider`. It also contains deterministic helpers for Preview, HN Insight, reading time, and text truncation.

`src/openai_summary_provider.py`

Implements an optional OpenAI-backed `SummaryProvider`. It receives HN metadata and selected comments only. It falls back to the rule-based summary when the request fails or output is empty.

The current Telegram Reading Decision sections are driven by Preview, HN Insight, and Why Trending fields. OpenAI is not a structured Reading Decision provider.

`src/nvidia_reading_decision_provider.py`

Implements an optional NVIDIA Build/NIM-backed `ReadingDecisionProvider`. It receives article text, metadata, and selected comments, then returns structured fields:

- `preview`
- `hn_insight`
- `why_trending`

`src/message_builder.py`

Builds the Telegram HTML message. It merges provider fields with deterministic fallback values and escapes dynamic text before rendering.

`src/telegram_client.py`

Sends the final message to Telegram.

## Provider Boundaries

The OpenAI provider and NVIDIA provider serve different roles.

OpenAI is a summary provider:

```text
HNStory -> summary string
```

NVIDIA is a Reading Decision provider:

```text
ReadingDecisionInput -> ReadingDecision(preview, hn_insight, why_trending)
```

This separation keeps the older summary interface stable while allowing structured Reading Decision fields to evolve independently.

## Fallback Merge

Message generation uses field-level fallback:

- provider `preview` is used only when article extraction succeeds
- provider `hn_insight` is used when non-empty
- provider `why_trending` is rendered only when non-empty
- deterministic Preview remains available when extraction succeeds
- unavailable Preview text is preserved when extraction fails
- deterministic HN Insight remains available from selected comments

Provider failure should not prevent Telegram message generation.

## Runtime Configuration

Provider selection uses `SUMMARY_PROVIDER`.

Supported values:

- `rule_based`
- `openai`
- `nvidia`

The default is `rule_based`.

## GitHub Actions

The scheduled workflow:

- checks out the repository
- sets up Python 3.11
- installs dependencies from `requirements.txt`
- runs `python -m pytest`
- sends the Telegram notification

Schedule:

```text
00:00 UTC / 09:00 KST
```

## Dry Run

The NVIDIA dry-run script is:

```text
scripts/test_nvidia_reading_decision.py
```

It exercises the NVIDIA Reading Decision Provider without sending Telegram messages and avoids printing secrets or full raw provider payloads.
