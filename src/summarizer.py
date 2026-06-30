from __future__ import annotations

import re

from src.hn_client import HNStory


def build_rule_based_summary(story: HNStory) -> str:
    title_hint = _build_title_hint(story)
    engagement_hint = _build_engagement_hint(story)

    if engagement_hint is None:
        return title_hint

    return f"{title_hint} {engagement_hint}"


def _build_title_hint(story: HNStory) -> str:
    title = _clean_title(story.title)
    lower_title = title.lower()

    if ".self" in lower_title:
        return ".self를 새 최상위 도메인으로 제안하거나 self-hosting 정체성을 위한 주소 공간으로 소개하는 글입니다."

    if "qwen" in lower_title and "local" in lower_title:
        return "Qwen 모델을 로컬 개발 환경에서 활용하며 모델 크기와 성능의 균형을 어떻게 잡을지 설명하는 글입니다."

    if "free the icons" in lower_title:
        return "아이콘을 특정 플랫폼이나 라이선스의 제약에서 벗어나 더 자유롭게 쓰자는 문제의식이나 프로젝트를 소개하는 글입니다."

    ask_hn_topic = _strip_prefix(title, "Ask HN:")
    if ask_hn_topic is not None:
        return f"HN 사용자들에게 {_as_korean_topic(ask_hn_topic)}에 대한 경험과 조언을 묻는 토론입니다."

    show_hn_topic = _strip_prefix(title, "Show HN:")
    if show_hn_topic is not None:
        return _build_project_intro(show_hn_topic, story, "직접 만든")

    launch_hn_topic = _strip_prefix(title, "Launch HN:")
    if launch_hn_topic is not None:
        return _build_project_intro(launch_hn_topic, story, "새로 출시한")

    if title.lower().startswith("how "):
        return f"{_as_korean_topic(title)} 방법과 판단 기준을 설명하는 글입니다."

    if title.lower().startswith("why "):
        return f"{_as_korean_topic(title)} 이유와 배경을 풀어 설명하는 글입니다."

    if "open source" in lower_title or "open-source" in lower_title:
        return f"{_as_korean_topic(title)}를 오픈소스로 공개한 배경이나 활용 가능성을 설명하는 글입니다."

    if "github.com" in (story.domain or ""):
        return f"{_as_korean_topic(title)}라는 오픈소스 프로젝트나 개발 도구를 소개하는 글입니다."

    if "arxiv.org" in (story.domain or ""):
        return f"{_as_korean_topic(title)}라는 연구 아이디어나 실험 결과를 소개하는 글입니다."

    if "youtube.com" in (story.domain or "") or "youtu.be" in (story.domain or ""):
        return f"{_as_korean_topic(title)}를 영상으로 설명하거나 시연하는 콘텐츠입니다."

    return f"{_as_korean_topic(title)}라는 주제를 다루며, 제목에서 제기한 문제나 아이디어를 설명하는 글입니다."


def _build_project_intro(topic: str, story: HNStory, launch_word: str) -> str:
    topic = _remove_parenthetical_suffix(topic)
    if "github.com" in (story.domain or ""):
        return f"{launch_word} {_as_korean_topic(topic)} 오픈소스 프로젝트를 소개하는 글입니다."

    return f"{launch_word} {_as_korean_topic(topic)} 프로젝트나 서비스를 소개하는 글입니다."


def _build_engagement_hint(story: HNStory) -> str | None:
    if story.score >= 500 or story.descendants >= 300:
        return "HN에서 반응이 커서 실제 유용성이나 파급력을 두고 활발히 논의되는 주제입니다."

    if story.score >= 200 or story.descendants >= 100:
        return "HN에서 관심이 높아 실무적 장단점이나 배경 맥락을 확인해 볼 만합니다."

    return None


def _clean_title(title: str) -> str:
    return " ".join(title.strip().split())


def _strip_prefix(title: str, prefix: str) -> str | None:
    if not title.lower().startswith(prefix.lower()):
        return None

    topic = title[len(prefix) :].strip()
    return topic or None


def _remove_parenthetical_suffix(title: str) -> str:
    return re.sub(r"\s*\([^)]*\)\s*$", "", title).strip()


def _as_korean_topic(title: str) -> str:
    return _remove_parenthetical_suffix(title).strip(" .")
