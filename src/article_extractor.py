from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any

import requests
import trafilatura


@dataclass(frozen=True)
class ArticleExtraction:
    success: bool
    title: str = ""
    text: str = ""
    word_count: int = 0
    published_date: str = ""
    error: str = ""


def extract_article(url: str, timeout_seconds: int = 10) -> ArticleExtraction:
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "hackernews-telegram-notifier/1.0"},
            timeout=timeout_seconds,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return ArticleExtraction(success=False, error=f"Fetch failed: {exc}")

    try:
        extracted = trafilatura.extract(
            response.text,
            output_format="json",
            with_metadata=True,
            include_comments=False,
            include_tables=False,
        )
    except Exception as exc:
        return ArticleExtraction(success=False, error=f"Extraction failed: {exc}")

    if not extracted:
        return ArticleExtraction(success=False, error="Extraction returned no article content.")

    try:
        data = json.loads(extracted)
    except json.JSONDecodeError as exc:
        return ArticleExtraction(success=False, error=f"Extraction returned invalid JSON: {exc}")

    text = _string_value(data.get("text"))
    if not text:
        return ArticleExtraction(success=False, error="Extracted article text was empty.")

    return ArticleExtraction(
        success=True,
        title=_string_value(data.get("title")),
        text=text,
        word_count=_count_words(text),
        published_date=_date_value(data.get("date")),
    )


def _string_value(value: Any) -> str:
    if not isinstance(value, str):
        return ""

    return " ".join(value.split())


def _count_words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def _date_value(value: Any) -> str:
    text = _string_value(value)
    match = re.search(r"(?<!\d)(?:19|20)\d{2}-\d{1,2}-\d{1,2}(?=\D|$)", text)
    return match.group(0) if match else ""
