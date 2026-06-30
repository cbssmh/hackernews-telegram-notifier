from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from src.hn_client import HNClient, HNStory, parse_comment_text, parse_story


REPORT_PATH = Path("experiments/hn_comment_analysis.md")
STORY_COUNT = 4
COMMENT_LIMIT = 3
CANDIDATE_COUNT = 12
TECHNICAL_TERMS = {
    "api",
    "architecture",
    "benchmark",
    "cache",
    "compiler",
    "database",
    "debug",
    "deploy",
    "distributed",
    "framework",
    "github",
    "implementation",
    "latency",
    "library",
    "linux",
    "memory",
    "model",
    "network",
    "performance",
    "postgres",
    "python",
    "runtime",
    "scale",
    "security",
    "server",
    "software",
    "sql",
    "system",
    "thread",
    "typescript",
}
HUMOR_MARKERS = {
    "haha",
    "lol",
    "lmao",
    "meme",
    "joke",
    "funny",
    "sarcasm",
    "xkcd",
}


@dataclass(frozen=True)
class CommentRecord:
    text: str
    raw_text: str
    score: int | None

    @property
    def length(self) -> int:
        return len(self.text)


@dataclass(frozen=True)
class StoryRecord:
    story: HNStory
    comments: tuple[CommentRecord, ...]


def main() -> int:
    records = fetch_story_records()
    REPORT_PATH.write_text(build_report(records), encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")
    return 0


def fetch_story_records() -> list[StoryRecord]:
    client = HNClient()
    story_ids = client.fetch_top_story_ids()
    records: list[StoryRecord] = []

    for item_id in story_ids[:CANDIDATE_COUNT]:
        try:
            item = client.fetch_item(item_id)
            story = parse_story(item)
        except (requests.RequestException, ValueError):
            continue

        if story is None:
            continue

        comments = fetch_top_level_comments(client, item, COMMENT_LIMIT)
        records.append(StoryRecord(story=story, comments=tuple(comments)))

        if len(records) >= STORY_COUNT:
            break

    return records


def fetch_top_level_comments(
    client: HNClient,
    story_item: dict[str, Any],
    limit: int,
) -> list[CommentRecord]:
    kids = story_item.get("kids")
    if not isinstance(kids, list):
        return []

    comments: list[CommentRecord] = []
    for comment_id in kids:
        if not isinstance(comment_id, int):
            continue

        try:
            comment_item = client.fetch_item(comment_id)
        except (requests.RequestException, ValueError):
            continue

        comment_text = parse_comment_text(comment_item)
        if not comment_text:
            continue

        raw_text = comment_item.get("text") if isinstance(comment_item.get("text"), str) else ""
        score = comment_item.get("score") if isinstance(comment_item.get("score"), int) else None
        comments.append(CommentRecord(text=comment_text, raw_text=raw_text, score=score))

        if len(comments) >= limit:
            break

    return comments


def build_report(records: list[StoryRecord]) -> str:
    lines = [
        "# Hacker News Top Comment Analysis",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "This isolated experiment inspects top-level Hacker News comments as reading-decision evidence. It does not rank comments, summarize comments, recommend production changes, or modify the Telegram pipeline.",
        "",
        f"Stories requested: {STORY_COUNT}",
        f"Top-level comments requested per story: {COMMENT_LIMIT}",
        "",
    ]

    for index, record in enumerate(records, start=1):
        lines.extend(format_story(index, record))

    return "\n".join(lines)


def format_story(index: int, record: StoryRecord) -> list[str]:
    story = record.story
    lines = [
        f"## Story #{index}",
        "",
        "------------------------------------------------",
        "",
        f"Title: {story.title}",
        "",
        f"HN URL: {story.discussion_url}",
        "",
        f"Article URL: {story.url or '(HN discussion only)'}",
        "",
        f"HN Score: {story.score}",
        "",
        f"Comment Count: {story.descendants}",
        "",
        "------------------------------------------------",
        "",
    ]

    if not record.comments:
        lines.extend(["No top-level comments were available.", ""])
    else:
        for comment_index, comment in enumerate(record.comments, start=1):
            lines.extend(format_comment(comment_index, comment))

    lines.extend(format_article_metrics(record.comments))
    return lines


def format_comment(index: int, comment: CommentRecord) -> list[str]:
    score = str(comment.score) if comment.score is not None else "not available"
    observations = objective_observations(comment)

    lines = [
        f"Top Comment #{index}",
        "",
        f"Comment score: {score}",
        "",
        f"Comment length: {comment.length} characters",
        "",
        "```text",
        comment.text,
        "```",
        "",
        "Objective observations:",
        "",
    ]
    lines.extend(f"- {observation}" for observation in observations)
    lines.extend(["", "------------------------------------------------", ""])
    return lines


def format_article_metrics(comments: tuple[CommentRecord, ...]) -> list[str]:
    lengths = [comment.length for comment in comments]
    lines = [
        "Article-level Metrics",
        "",
    ]

    if not comments:
        lines.extend(
            [
                "- average comment length: 0",
                "- longest comment: 0",
                "- shortest comment: 0",
                "- percentage of comments containing links: 0%",
                "- percentage containing code blocks: 0%",
                "- percentage containing technical terms: 0%",
                "- percentage containing obvious humor or memes: 0%",
                "",
            ]
        )
        return lines

    lines.extend(
        [
            f"- average comment length: {round(sum(lengths) / len(lengths), 1)} characters",
            f"- longest comment: {max(lengths)} characters",
            f"- shortest comment: {min(lengths)} characters",
            f"- percentage of comments containing links: {percentage(comments, contains_link)}",
            f"- percentage containing code blocks: {percentage(comments, contains_code_block)}",
            f"- percentage containing technical terms: {percentage(comments, contains_technical_terms)}",
            f"- percentage containing obvious humor or memes: {percentage(comments, contains_humor_marker)}",
            "",
        ]
    )
    return lines


def objective_observations(comment: CommentRecord) -> list[str]:
    observations: list[str] = []

    if explains_background(comment):
        observations.append("comment explains background")
    if compares_technologies(comment):
        observations.append("comment compares technologies")
    if corrects_article(comment):
        observations.append("comment appears to correct or qualify something")
    if mostly_opinion(comment):
        observations.append("comment contains opinion language")
    if contains_humor_marker(comment):
        observations.append("comment contains obvious humor or meme markers")
    if adds_implementation_detail(comment):
        observations.append("comment adds implementation detail")
    if contains_link(comment):
        observations.append("comment contains a link")
    if contains_code_block(comment):
        observations.append("comment contains code-like formatting")
    if contains_technical_terms(comment):
        observations.append("comment contains technical terms")

    if not observations:
        observations.append("no heuristic observation matched")

    return observations


def explains_background(comment: CommentRecord) -> bool:
    text = normalized(comment.text)
    return any(
        phrase in text
        for phrase in (
            "background",
            "context",
            "history",
            "historically",
            "the reason",
            "because",
            "for years",
            "used to",
        )
    )


def compares_technologies(comment: CommentRecord) -> bool:
    text = normalized(comment.text)
    return any(
        marker in text
        for marker in (
            " vs ",
            " versus ",
            "compared to",
            "better than",
            "worse than",
            "instead of",
            "alternative",
            "tradeoff",
            "trade-off",
        )
    )


def corrects_article(comment: CommentRecord) -> bool:
    text = normalized(comment.text)
    return any(
        marker in text
        for marker in (
            "actually",
            "incorrect",
            "not true",
            "isn't true",
            "doesn't mean",
            "correction",
            "to be precise",
            "technically",
        )
    )


def mostly_opinion(comment: CommentRecord) -> bool:
    text = normalized(comment.text)
    opinion_markers = (
        "i think",
        "i believe",
        "i feel",
        "in my opinion",
        "imo",
        "imho",
        "personally",
    )
    return any(marker in text for marker in opinion_markers)


def adds_implementation_detail(comment: CommentRecord) -> bool:
    text = normalized(comment.text)
    return any(
        marker in text
        for marker in (
            "implemented",
            "implementation",
            "code",
            "api",
            "database",
            "cache",
            "memory",
            "latency",
            "architecture",
            "runtime",
            "benchmark",
            "deploy",
            "thread",
        )
    )


def contains_link(comment: CommentRecord) -> bool:
    combined = f"{comment.text} {comment.raw_text}"
    return bool(re.search(r"https?://|www\.|href=", combined, flags=re.IGNORECASE))


def contains_code_block(comment: CommentRecord) -> bool:
    raw = comment.raw_text
    text = comment.text
    return bool(
        re.search(r"<pre|<code|```|(^|\n)\s{4,}\S", raw, flags=re.IGNORECASE)
        or re.search(r"\b(def|class|function|const|let|var|SELECT)\b|[{};]|\w+\(\)", text)
    )


def contains_technical_terms(comment: CommentRecord) -> bool:
    terms = set(re.findall(r"[a-zA-Z][a-zA-Z0-9_+-]*", comment.text.lower()))
    return bool(terms.intersection(TECHNICAL_TERMS))


def contains_humor_marker(comment: CommentRecord) -> bool:
    text = normalized(comment.text)
    terms = set(re.findall(r"[a-zA-Z][a-zA-Z0-9_+-]*", text))
    return bool(terms.intersection(HUMOR_MARKERS))


def percentage(
    comments: tuple[CommentRecord, ...],
    predicate,
) -> str:
    matches = sum(1 for comment in comments if predicate(comment))
    value = round((matches / len(comments)) * 100, 1)
    return f"{value}%"


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


if __name__ == "__main__":
    raise SystemExit(main())
