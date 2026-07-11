# Release Notes

## Current Repository State

The repository now implements a Hacker News Reading Decision pipeline rather than a simple top-story notifier.

Current capabilities:

- daily top-3 Hacker News digest
- Article Extraction
- Published Date
- Reading Time
- HN Comments
- rule-based fallback
- OpenAI Summary Provider
- NVIDIA Reading Decision Provider
- Preview
- HN Insight
- Why Trending
- GitHub Actions schedule
- NVIDIA dry-run benchmark script

The default NVIDIA example model is:

```text
minimaxai/minimax-m3
```

## v1.0.0 - Reading Decision Assistant

The v1.0.0 direction changed the project from a generic HN summary sender into a reading-decision assistant.

Highlights:

- Sends a daily top-3 Hacker News digest to Telegram.
- Uses a Reading Decision message format with Preview, reading time, score, comment count, and community context.
- Keeps source and Hacker News discussion URLs clickable while displaying concise labels.
- Runs as a deterministic pipeline by default, with no database, hosted service, or required paid model.
- Extracts article text for previews when available and falls back gracefully when extraction fails.
- Includes Hacker News community context from selected top comments.
- Supports GitHub Actions automation for scheduled daily delivery.
- Includes tests for the HN client, message builder, Telegram client, reading-decision logic, summarizers, providers, and dry-run script.

Release metadata:

- Tag: not created
- Push: not performed
