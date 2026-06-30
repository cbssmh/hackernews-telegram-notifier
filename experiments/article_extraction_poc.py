from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any

import trafilatura


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract article metadata and plain text from one URL with trafilatura."
    )
    parser.add_argument("url", help="Article URL to extract")
    args = parser.parse_args()

    started_at = time.perf_counter()
    result = extract_article(args.url)
    result["execution_time_seconds"] = round(time.perf_counter() - started_at, 3)

    print_report(result)

    return 0 if result["success"] else 1


def extract_article(url: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "url": url,
        "success": False,
        "title": "",
        "meta_description": "",
        "text": "",
        "text_length": 0,
        "error": "",
    }

    try:
        downloaded = trafilatura.fetch_url(url)
    except Exception as exc:
        result["error"] = f"Fetch failed: {exc}"
        return result

    if not downloaded:
        result["error"] = "Fetch returned no content."
        return result

    try:
        extracted = trafilatura.extract(
            downloaded,
            output_format="json",
            with_metadata=True,
            include_comments=False,
            include_tables=False,
        )
    except Exception as exc:
        result["error"] = f"Extraction failed: {exc}"
        return result

    if not extracted:
        result["error"] = "Extraction returned no article content."
        return result

    try:
        data = json.loads(extracted)
    except json.JSONDecodeError as exc:
        result["error"] = f"Extraction returned invalid JSON: {exc}"
        return result

    text = _string_value(data.get("text"))
    result.update(
        {
            "success": bool(text),
            "title": _string_value(data.get("title")),
            "meta_description": _string_value(data.get("description")),
            "text": text,
            "text_length": len(text),
        }
    )

    if not text:
        result["error"] = "Extraction metadata was present, but plain text was empty."

    return result


def print_report(result: dict[str, Any]) -> None:
    print("Article Extraction PoC")
    print("======================")
    print(f"URL: {result['url']}")
    print(f"Success: {result['success']}")
    print(f"Execution time seconds: {result['execution_time_seconds']}")
    print(f"Extracted text length: {result['text_length']}")
    print()
    print("Extracted title:")
    print(result["title"] or "(not available)")
    print()
    print("Meta description:")
    print(result["meta_description"] or "(not available)")
    print()
    print("Extracted plain text:")
    print(result["text"] or "(not available)")

    if result["error"]:
        print()
        print("Error:")
        print(result["error"])


def _string_value(value: Any) -> str:
    if not isinstance(value, str):
        return ""

    return value.strip()


if __name__ == "__main__":
    sys.exit(main())
