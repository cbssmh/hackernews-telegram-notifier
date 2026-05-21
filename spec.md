# HN Daily Top 3 Notifier

## Goal
매일 오전 9시, Hacker News 인기글 3개를 수집하고 핵심 요약을 Telegram 알림으로 전송한다.

## Target User
개인 사용자 1명.

## MVP Scope
- Hacker News Top Stories API에서 인기글 수집
- 상위 3개 글 선택
- 제목, 링크, 점수, 댓글 수 수집
- 규칙 기반 핵심 요약 생성
- Telegram Bot으로 메시지 전송
- GitHub Actions로 매일 자동 실행

## Out of Scope for MVP
- 웹 UI
- DB 저장
- 사용자 계정
- 다중 사용자 지원
- OpenAI 요약
- 복잡한 중복 알림 방지

## Architecture
GitHub Actions Scheduler
→ Python script
→ Hacker News API
→ Rule-based summarizer
→ Telegram Bot API

## Notification Time
- 매일 오전 9시
- 기준 시간대: Asia/Seoul

## API Sources
- Hacker News Firebase API
  - Top stories endpoint
  - Item detail endpoint

## Telegram Requirements
Required environment variables:
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID

## Message Format
각 글마다 다음 정보를 포함한다.

1. 순위
2. 제목
3. 핵심 요약
4. 점수
5. 댓글 수
6. 원문 링크
7. HN 토론 링크

## Rule-Based Summary Logic
MVP에서는 기사 본문을 직접 크롤링하지 않는다.

요약은 다음 정보를 기반으로 생성한다:
- 제목
- 점수
- 댓글 수
- 도메인
- HN 메타데이터

예시:
"AI 관련 개발 도구 발표로 보이며, HN에서 높은 관심을 받고 있습니다. 댓글 수가 많아 기술적 논쟁이나 실사용 경험 공유가 활발할 가능성이 있습니다."

## Error Handling
- HN API 실패 시 명확한 에러 로그 출력
- Telegram 전송 실패 시 실패 로그 출력
- 일부 글 수집 실패 시 가능한 글만 전송
- Top 3 미만이면 수집 가능한 개수만 전송

## Test Requirements
- HN item 파싱 테스트
- Top 3 선택 테스트
- Telegram 메시지 포맷 테스트
- 환경변수 누락 테스트
- API 실패 시 예외 처리 테스트

## Future Extension
- OpenAI 요약 옵션
- 중복 알림 방지
- 키워드 필터링
- 관심 분야별 점수화
- GitHub reading note 자동 생성