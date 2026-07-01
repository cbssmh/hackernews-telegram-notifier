import json

import requests
import trafilatura

from src.article_extractor import extract_article


def test_extract_article_includes_published_date(monkeypatch) -> None:
    class FakeResponse:
        text = "<html><body>article</body></html>"

        def raise_for_status(self) -> None:
            return None

    def fake_get(*args, **kwargs) -> FakeResponse:
        return FakeResponse()

    def fake_extract(*args, **kwargs) -> str:
        return json.dumps(
            {
                "title": "Extracted Title",
                "text": "This article text has enough words to count as extracted content.",
                "date": "2026-05-20T12:34:56Z",
            }
        )

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(trafilatura, "extract", fake_extract)

    article = extract_article("https://example.com/post")

    assert article.success is True
    assert article.published_date == "2026-05-20"
