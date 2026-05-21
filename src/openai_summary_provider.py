from __future__ import annotations

import sys
from typing import Any

import requests

from src.hn_client import HNStory
from src.summarizer import build_rule_based_summary


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_OPENAI_MODEL = "gpt-5-nano"


class OpenAISummaryProvider:
    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_OPENAI_MODEL,
        timeout_seconds: int = 20,
    ) -> None:
        if not api_key:
            raise ValueError("OpenAI API key is required.")

        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    def __call__(self, story: HNStory) -> str:
        try:
            summary = self._build_openai_summary(story)
        except Exception as exc:
            self._log_fallback(exc)
            return build_rule_based_summary(story)

        if not summary:
            return build_rule_based_summary(story)

        return summary

    def _build_openai_summary(self, story: HNStory) -> str:
        response = requests.post(
            OPENAI_RESPONSES_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "instructions": (
                    "You summarize Hacker News stories for a Korean developer. "
                    "Use only the provided title, source domain, score, comment count, "
                    "and selected HN comments. Do not imply you read the article body. "
                    "Return one concise Korean sentence."
                ),
                "input": self._build_input(story),
                "max_output_tokens": 120,
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()

        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("OpenAI response must be an object.")

        return _extract_output_text(data).strip()

    def _build_input(self, story: HNStory) -> str:
        comments = "\n".join(f"- {comment}" for comment in story.top_comments)
        if not comments:
            comments = "- No top comments were available."

        return "\n".join(
            [
                f"Title: {story.title}",
                f"Domain: {story.domain or 'news.ycombinator.com'}",
                f"Score: {story.score}",
                f"Comment count: {story.descendants}",
                "Top HN comments:",
                comments,
            ]
        )

    def _log_fallback(self, exc: Exception) -> None:
        status_code = "unknown"
        if isinstance(exc, requests.RequestException) and exc.response is not None:
            status_code = str(exc.response.status_code)

        print(
            f"OpenAI summary failed. status_code={status_code}; using rule-based summary.",
            file=sys.stderr,
        )


def _extract_output_text(data: dict[str, Any]) -> str:
    output_text = data.get("output_text")
    if isinstance(output_text, str):
        return output_text

    output = data.get("output")
    if not isinstance(output, list):
        return ""

    parts: list[str] = []
    for item in output:
        if not isinstance(item, dict):
            continue

        content = item.get("content")
        if not isinstance(content, list):
            continue

        for content_item in content:
            if not isinstance(content_item, dict):
                continue

            text = content_item.get("text")
            if content_item.get("type") == "output_text" and isinstance(text, str):
                parts.append(text)

    return "\n".join(parts)
