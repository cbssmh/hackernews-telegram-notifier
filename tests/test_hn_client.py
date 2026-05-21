import requests

from src.hn_client import HNClient
from src.hn_client import HNStory, parse_story


def test_parse_valid_story() -> None:
    item = {
        "id": 123,
        "type": "story",
        "title": "Example Story",
        "url": "https://example.com/post",
        "score": 100,
        "descendants": 20,
    }

    story = parse_story(item)

    assert isinstance(story, HNStory)
    assert story.id == 123
    assert story.title == "Example Story"
    assert story.domain == "example.com"


def test_parse_deleted_story_returns_none() -> None:
    item = {
        "id": 123,
        "type": "story",
        "title": "Deleted Story",
        "deleted": True,
    }

    assert parse_story(item) is None


def test_parse_non_story_returns_none() -> None:
    item = {
        "id": 123,
        "type": "comment",
        "title": "Not a Story",
    }

    assert parse_story(item) is None


def test_parse_story_without_url_is_allowed() -> None:
    item = {
        "id": 123,
        "type": "story",
        "title": "Ask HN",
        "score": 50,
        "descendants": 30,
    }

    story = parse_story(item)

    assert story is not None
    assert story.url is None
    assert story.discussion_url == "https://news.ycombinator.com/item?id=123"


def test_fetch_top_stories_skips_failed_item_fetch() -> None:
    class StubHNClient(HNClient):
        def fetch_top_story_ids(self) -> list[int]:
            return [1, 2, 3]

        def fetch_item(self, item_id: int) -> dict:
            if item_id == 1:
                raise requests.RequestException("temporary item failure")

            return {
                "id": item_id,
                "type": "story",
                "title": f"Story {item_id}",
                "score": 100,
                "descendants": 10,
            }

    stories = StubHNClient().fetch_top_stories(limit=2, candidate_count=3)

    assert [story.id for story in stories] == [2, 3]
