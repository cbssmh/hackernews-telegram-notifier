# Implementation Plan

This document tracks the implemented shape of the project and the remaining maintenance work. The original MVP has been promoted from a simple HN Telegram notifier into a Reading Decision engine.

## Current Status

Implemented:

- Hacker News Top Stories collection
- Top story filtering and comment collection
- Article Extraction
- Published Date extraction
- Reading Time estimation
- Rule-based fallback summaries
- Deterministic Preview fallback
- HN Insight from selected comments
- Optional OpenAI Summary Provider
- Optional NVIDIA Reading Decision Provider
- Optional Why Trending field
- Telegram HTML rendering
- GitHub Actions scheduled delivery
- NVIDIA dry-run benchmark script
- Unit tests for core modules and provider fallback behavior

## Current Pipeline

```text
GitHub Actions or local shell
  -> src.main
  -> HNClient
  -> Article Extraction
  -> Summary Provider
  -> Reading Decision Provider
  -> Message Builder
  -> Telegram Client
```

## Provider Milestones

### Rule-Based Path

Status: implemented.

The default path uses no AI provider. It builds summaries, Preview, and HN Insight from story metadata, article extraction, and selected comments.

### OpenAI Summary Provider

Status: implemented.

OpenAI is used only as a `SummaryProvider`. It receives the HN title, source domain, score, comment count, and selected comments. It does not receive extracted article text.

It is not a structured Reading Decision provider and should not be documented as producing Preview, HN Insight, or Why Trending.

### NVIDIA Reading Decision Provider

Status: implemented.

NVIDIA is used as a structured `ReadingDecisionProvider`. It receives story metadata, extracted article text, published date, and selected comments. It returns:

- `preview`
- `hn_insight`
- `why_trending`

The recommended example model is `minimaxai/minimax-m3`.

## Operational Milestones

Completed:

- Daily GitHub Actions workflow at `00:00 UTC`
- Manual workflow dispatch
- Test execution before Telegram delivery
- Environment-driven provider selection
- Local NVIDIA dry-run script
- Model evaluation notes in `docs/model-evaluation.md`

## Current Maintenance Plan

Near-term documentation work:

- Keep README focused on portfolio-level overview.
- Keep provider details in `docs/architecture.md` and `docs/model-evaluation.md`.
- Keep experiments isolated under `experiments/`.

Near-term engineering work:

- Observe real GitHub Actions runs for extraction failures and provider fallback frequency.
- Add broader model evaluation only when the prompt or NVIDIA model availability changes.
- Consider message-length safeguards if story count or field length grows.

## Non-Goals

Current non-goals:

- web UI
- database storage
- multi-user accounts
- duplicate suppression
- browser automation
- replacing Telegram delivery
- making AI providers mandatory
