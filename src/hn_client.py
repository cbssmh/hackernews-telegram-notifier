from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import requests


HN_BASE_URL = "https://hacker-news.firebaseio.com/v0"
HN_ITEM_URL = "https://news.ycombinator.com/item?id={item_id}"


@dataclass(frozen=True)
class HNStory:
    id: int
    title: str
    url: str | None
    score: int
    descendants: int

    @property
    def discussion_url(self) -> str:
        return HN_ITEM_URL.format(item_id=self.id)

    @property
    def domain(self) -> str | None:
        if not self.url:
            return None
        parsed = urlparse(self.url)
        return parsed.netloc.removeprefix("www.") or None


class HNClient:
    def __init__(self, timeout_seconds: int = 10) -> None:
        self.timeout_seconds = timeout_seconds

    def fetch_top_story_ids(self) -> list[int]:
        response = requests.get(
            f"{HN_BASE_URL}/topstories.json",
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list):
            raise ValueError("HN top stories response must be a list.")

        return [int(item_id) for item_id in data]

    def fetch_item(self, item_id: int) -> dict[str, Any]:
        response = requests.get(
            f"{HN_BASE_URL}/item/{item_id}.json",
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, dict):
            raise ValueError(f"HN item response must be an object. item_id={item_id}")

        return data

    def fetch_top_stories(self, limit: int = 3, candidate_count: int = 15) -> list[HNStory]:
        story_ids = self.fetch_top_story_ids()

        stories: list[HNStory] = []

        for item_id in story_ids[:candidate_count]:
            item = self.fetch_item(item_id)
            story = parse_story(item)

            if story is not None:
                stories.append(story)

            if len(stories) >= limit:
                break

        return stories


def parse_story(item: dict[str, Any]) -> HNStory | None:
    if item.get("type") != "story":
        return None

    if item.get("deleted") or item.get("dead"):
        return None

    item_id = item.get("id")
    title = item.get("title")

    if not isinstance(item_id, int):
        return None

    if not isinstance(title, str) or not title.strip():
        return None

    return HNStory(
        id=item_id,
        title=title.strip(),
        url=item.get("url") if isinstance(item.get("url"), str) else None,
        score=item.get("score") if isinstance(item.get("score"), int) else 0,
        descendants=item.get("descendants") if isinstance(item.get("descendants"), int) else 0,
    )