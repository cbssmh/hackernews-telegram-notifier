from __future__ import annotations

from src.hn_client import HNStory


def build_rule_based_summary(story: HNStory) -> str:
    domain_hint = _build_domain_hint(story)
    engagement_hint = _build_engagement_hint(story)

    return f"{domain_hint} {engagement_hint}".strip()


def _build_domain_hint(story: HNStory) -> str:
    if story.domain is None:
        return "HN 토론 중심의 글로 보입니다."

    if "github.com" in story.domain:
        return "개발 도구나 오픈소스 프로젝트와 관련된 글로 보입니다."

    if "arxiv.org" in story.domain:
        return "논문이나 연구 결과와 관련된 글로 보입니다."

    if "youtube.com" in story.domain or "youtu.be" in story.domain:
        return "영상 콘텐츠를 중심으로 논의되는 글로 보입니다."

    return f"{story.domain} 출처의 기술/스타트업 관련 글로 보입니다."


def _build_engagement_hint(story: HNStory) -> str:
    if story.score >= 500 or story.descendants >= 300:
        return "HN에서 매우 높은 관심을 받고 있으며, 활발한 논쟁이나 경험 공유가 있을 가능성이 큽니다."

    if story.score >= 200 or story.descendants >= 100:
        return "HN에서 의미 있는 관심을 받고 있으며, 댓글에서 추가 맥락을 얻을 수 있습니다."

    return "아직 초기 반응 단계이지만 HN 상위권에 올라온 글입니다."