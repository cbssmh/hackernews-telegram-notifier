# implementation_plan

## Goal
Greenfield Python 프로젝트로 HN 인기글 Top 3를 매일 오전 9시 Telegram으로 알림한다.

## Files to Create

### Core
- `src/main.py`
- `src/hn_client.py`
- `src/summarizer.py`
- `src/telegram_client.py`
- `src/message_builder.py`

### Config
- `requirements.txt`
- `.env.example`
- `.github/workflows/daily_hn.yml`

### Docs
- `README.md`
- `spec.md`
- `implementation_plan.md`

### Tests
- `tests/test_summarizer.py`
- `tests/test_message_builder.py`
- `tests/test_hn_client.py`

## Dependencies

```txt
requests
pytest
```

No OpenAI SDK in MVP.

## Data Flow

```text
GitHub Actions
  ↓
main.py
  ↓
hn_client.py
  ↓
summarizer.py
  ↓
message_builder.py
  ↓
telegram_client.py
```

## Execution Order

1. Load environment variables:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

2. Fetch HN top story IDs.

3. Fetch item details for top candidates.

4. Filter valid story items:
   - has title
   - has id
   - type is `story`
   - not deleted
   - not dead

5. Select top 3.

6. Generate rule-based summary.

7. Build Telegram message.

8. Send message.

9. Log success or failure.

## Rule-Based Summary Strategy

No article crawling in MVP.

Summary is generated from:

- title
- score
- comment count
- URL domain
- HN metadata

Example logic:

- high score + many comments → “HN에서 강한 관심과 논쟁이 발생한 글”
- GitHub domain → “개발 도구/오픈소스 프로젝트일 가능성”
- blog/company domain → “기술 블로그/제품 발표 가능성”
- no URL → “HN discussion 중심 글”

## Telegram Message Format

```text
📰 HN Daily Top 3 — YYYY-MM-DD

1. Title
요약: ...
점수: 123 | 댓글: 45
원문: https://...
토론: https://news.ycombinator.com/item?id=...

---
```

## GitHub Actions Schedule

KST 오전 9시는 UTC 00:00.

```yml
on:
  schedule:
    - cron: "0 0 * * *"
  workflow_dispatch:
```

## Testing Strategy

### Unit Tests
- summary generation
- message formatting
- invalid HN item filtering

### Integration-Light Tests
- HN client response parsing using mocked data
- Telegram payload construction without real sending

## Migration Impact
None. Greenfield.

## Rollback Risk
Low.

## Future Extension Points

### OpenAI Summary Option

Later add:

```text
SUMMARY_PROVIDER=rule_based | openai
OPENAI_API_KEY=...
```

Possible files:

- `src/summary_providers/rule_based.py`
- `src/summary_providers/openai.py`

### Duplicate Prevention

Later add:

- GitHub Actions cache
- JSON state file
- gist storage

## Implementation Milestones

### Milestone 1
Create core Python modules and tests.

### Milestone 2
Add GitHub Actions workflow.

### Milestone 3
Add README setup guide.

### Milestone 4
Optional OpenAI summarizer.