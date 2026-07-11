# Specification

## Goal

Send a daily Telegram digest of the top Hacker News stories that helps a Korean developer make fast Reading Decisions.

The digest should prioritize evidence over generic summaries.

## Target User

A single technical reader who wants a compact daily view of useful Hacker News stories.

## Scope

In scope:

- collect Hacker News Top Stories
- select up to three valid stories
- fetch selected top-level HN comments
- extract article text and metadata when possible
- display published date when available
- estimate reading time from extracted article text
- build Preview, HN Insight, and optional Why Trending
- send a Telegram message
- run locally or on GitHub Actions
- support rule-based, OpenAI Summary Provider, and NVIDIA Reading Decision Provider modes

Out of scope:

- web UI
- database persistence
- user accounts
- multi-chat routing
- duplicate notification prevention
- guaranteed article extraction for every site
- making AI provider output required

## Functional Requirements

The notifier must:

- fetch Hacker News top story IDs from the Firebase API
- skip deleted, dead, invalid, or non-story items
- continue when individual story or comment fetches fail
- include source and HN discussion links
- escape dynamic text before Telegram HTML rendering
- fall back when extraction or provider calls fail
- avoid exposing provider API keys in dry-run output

## Telegram Output

Each story can include:

- rank and title
- published date, when extracted
- source domain
- reading time, when article extraction succeeds
- score and comment count
- Preview
- HN Insight, when available
- Why Trending, when provided by the NVIDIA Reading Decision Provider
- source link
- HN discussion link

## Provider Modes

### Rule-Based

`SUMMARY_PROVIDER=rule_based`

This is the default. It uses deterministic summaries and fallback Reading Decision fields.

### OpenAI

`SUMMARY_PROVIDER=openai`

OpenAI receives HN metadata and selected comments only. It does not receive article bodies. If the request fails or returns empty output, the rule-based summary is used.

OpenAI is not a structured Reading Decision provider and does not produce Preview, HN Insight, or Why Trending fields.

### NVIDIA

`SUMMARY_PROVIDER=nvidia`

NVIDIA receives HN metadata, selected comments, and extracted article text. It returns structured Reading Decision fields:

- `preview`
- `hn_insight`
- `why_trending`

If NVIDIA configuration is incomplete or the request fails, the notifier uses non-LLM Reading Decision fields.

## Environment Variables

Required for Telegram delivery:

| Name | Required | Default | Notes |
| --- | --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | yes | none | Telegram bot token |
| `TELEGRAM_CHAT_ID` | yes | none | Target chat ID |

Provider selection:

| Name | Required | Default | Notes |
| --- | --- | --- | --- |
| `SUMMARY_PROVIDER` | no | `rule_based` | Supported values: `rule_based`, `openai`, `nvidia` |
| `HN_COMMENT_LIMIT` | no | `OPENAI_MAX_COMMENTS` or `3` | Number of selected comments to fetch |

OpenAI:

| Name | Required | Default | Notes |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | only for OpenAI mode | none | Missing key falls back to rule-based |
| `OPENAI_MODEL` | no | `gpt-5-nano` | OpenAI Responses API model |
| `OPENAI_MAX_COMMENTS` | no | `3` | Backward-compatible comment limit input |
| `OPENAI_TIMEOUT_SECONDS` | no | `20` | Request timeout |

NVIDIA:

| Name | Required | Default | Notes |
| --- | --- | --- | --- |
| `NVIDIA_API_KEY` | only for NVIDIA mode | none | Missing key disables NVIDIA Reading Decisions |
| `NVIDIA_MODEL` | only for NVIDIA mode | none | Example: `minimaxai/minimax-m3` |
| `NVIDIA_TIMEOUT_SECONDS` | no | `20` | Repository examples recommend `60` |

## GitHub Actions

Workflow: `.github/workflows/daily_hn.yml`

Schedule:

```yaml
schedule:
  - cron: "0 0 * * *"
```

This runs at `00:00 UTC`, which is `09:00 KST`.

The workflow also supports `workflow_dispatch`.

## Error Handling

Expected fallback behavior:

- missing Telegram values fail during Telegram delivery
- HN item failures are logged and skipped
- article fetch or extraction failures produce Preview fallback text
- access-blocked errors use a more specific Preview fallback
- missing OpenAI credentials fall back to rule-based summaries
- OpenAI request failures fall back to rule-based summaries
- missing NVIDIA credentials disable NVIDIA Reading Decisions
- NVIDIA request, parsing, or schema failures return empty Reading Decision fields

## Test Requirements

The test suite should cover:

- HN story parsing
- comment HTML parsing
- article extraction success and failure
- reading time and Preview fallback
- HN Insight construction
- Telegram message formatting
- provider selection
- OpenAI fallback
- NVIDIA JSON parsing and fallback
- dry-run script behavior
