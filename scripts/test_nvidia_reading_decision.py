from __future__ import annotations

import os
import sys
from pathlib import Path

import requests

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.article_extractor import ArticleExtraction, extract_article
from src.hn_client import HNClient, HNStory, parse_story
from src.nvidia_reading_decision_provider import NVIDIAReadingDecisionProvider
from src.reading_decision import ReadingDecisionInput


DEFAULT_TIMEOUT_SECONDS = 20
MAX_STORIES_TO_SCAN = 10


def main() -> int:
    api_key = _stripped_env("NVIDIA_API_KEY")
    model = _stripped_env("NVIDIA_MODEL")
    timeout_seconds = _timeout_seconds_from_env("NVIDIA_TIMEOUT_SECONDS")
    story_id = _story_id_from_env("HN_STORY_ID")

    if not api_key:
        print("NVIDIA_API_KEY is missing.", file=sys.stderr)
        return 1

    if not model:
        print("NVIDIA_MODEL is missing.", file=sys.stderr)
        return 1

    if story_id == 0:
        print("HN_STORY_ID must be a positive integer.", file=sys.stderr)
        return 1

    hn_client = HNClient()
    if story_id is not None:
        selected = _select_fixed_story_with_article(hn_client, story_id)
        if selected is None:
            return 1
        story, article = selected
    else:
        selected = _select_top_story_with_article(hn_client)
        if selected is None:
            return 1
        story, article = selected

    provider = NVIDIAReadingDecisionProvider(
        api_key=api_key,
        model=model,
        timeout_seconds=timeout_seconds,
    )
    decision = provider(ReadingDecisionInput(story=story, article=article))

    print(f"Model: {model}")
    print(f"Story title: {story.title}")
    print(f"Article extraction success: {article.success}")
    print(f"Comment count supplied: {len(story.top_comments)}")
    print(f"Preview: {decision.preview}")
    print(f"HN Insight: {decision.hn_insight}")
    print(f"Why Trending: {decision.why_trending}")

    return 0


def _select_top_story_with_article(hn_client: HNClient) -> tuple[HNStory, ArticleExtraction] | None:
    try:
        stories = hn_client.fetch_top_stories(
            limit=MAX_STORIES_TO_SCAN,
            candidate_count=MAX_STORIES_TO_SCAN,
            include_comments=True,
            comment_limit=3,
        )
    except (requests.RequestException, ValueError) as exc:
        print(f"Failed to fetch Hacker News story. error_type={type(exc).__name__}", file=sys.stderr)
        return None

    if not stories:
        print("No Hacker News story was available.", file=sys.stderr)
        return None

    selected = _select_story_with_article(stories)
    if selected is None:
        print("No extractable article found in the first 10 Hacker News stories.", file=sys.stderr)
        return None

    return selected


def _select_fixed_story_with_article(
    hn_client: HNClient,
    story_id: int,
) -> tuple[HNStory, ArticleExtraction] | None:
    try:
        item = hn_client.fetch_item(story_id)
        story = parse_story(item)
    except (requests.RequestException, ValueError) as exc:
        print(f"Failed to fetch Hacker News story. error_type={type(exc).__name__}", file=sys.stderr)
        return None

    if story is None:
        print("HN_STORY_ID did not resolve to a valid story.", file=sys.stderr)
        return None

    story = HNStory(
        id=story.id,
        title=story.title,
        url=story.url,
        score=story.score,
        descendants=story.descendants,
        top_comments=hn_client.fetch_top_comments(item, limit=3),
    )

    try:
        article = extract_article(story.url) if story.url else ArticleExtraction(
            success=False,
            error="Story has no URL.",
        )
    except Exception as exc:
        print(f"Article extraction failed. error_type={type(exc).__name__}", file=sys.stderr)
        return None

    return story, article


def _stripped_env(name: str) -> str:
    return os.getenv(name, "").strip()


def _timeout_seconds_from_env(name: str) -> int:
    value = _stripped_env(name)
    if not value:
        return DEFAULT_TIMEOUT_SECONDS

    try:
        parsed = int(value)
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS

    if parsed <= 0:
        return DEFAULT_TIMEOUT_SECONDS

    return parsed


def _story_id_from_env(name: str) -> int | None:
    value = _stripped_env(name)
    if not value:
        return None

    try:
        story_id = int(value)
    except ValueError:
        return 0

    return story_id if story_id > 0 else 0


def _select_story_with_article(stories: list[HNStory]) -> tuple[HNStory, ArticleExtraction] | None:
    for story in stories:
        if not story.url:
            continue

        try:
            article = extract_article(story.url)
        except Exception:
            continue

        if article.success and article.text:
            return story, article

    return None


if __name__ == "__main__":
    raise SystemExit(main())
