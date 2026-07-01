# HN Daily Digest v1.0.0 — Reading Decision Assistant

HN Daily Digest v1.0.0 delivers a daily Telegram digest of the top Hacker News stories, shaped around fast reading decisions instead of generic summaries.

## Highlights

- Sends a daily top-3 Hacker News digest to Telegram.
- Uses a Reading Decision focused message format with source type, preview, reading time, score, comment count, and community context.
- Keeps source and Hacker News discussion URLs clickable while displaying cleaner labels: the source hostname and `HN Discussion`.
- Runs as a free deterministic pipeline by default, with no database, paid model dependency, or hosted service required.
- Extracts article text for previews when available and falls back gracefully when extraction fails.
- Includes Hacker News community context from top comments to help judge whether a story is worth opening.
- Supports GitHub Actions automation for scheduled daily delivery.
- Ships with 33 passing tests covering the HN client, message builder, Telegram client, reading-decision logic, summarizers, and provider selection.

## Release Status

- Version: v1.0.0
- Title: HN Daily Digest v1.0.0 — Reading Decision Assistant
- Tag: not created yet
- Push: not performed
