# NVIDIA Reading Decision Engine: Model Evaluation

## Context

This project originally followed a deterministic pipeline:

```text
Article -> Extraction -> Evidence -> Telegram
```

The first implementation intentionally avoided LLM-dependent features because the project was designed to work under free, non-LLM constraints. That meant the notifier did not attempt article-level semantic understanding, natural-language summary generation, preview rewriting, Hacker News comment synthesis, "why trending" explanations, reading-value judgment, or reader recommendation.

The NVIDIA Build/NIM work keeps the existing extraction layer and adds an optional reading-decision layer above it. The goal is not to replace article extraction or the existing Telegram rendering path. The goal is to let an LLM produce structured reading-decision fields when explicitly enabled, while preserving the deterministic fallback output.

## Previous constraints

Before this change, the project already had:

- Article extraction through `src.article_extractor.ArticleExtraction`
- deterministic preview text derived from extracted article text
- deterministic HN Insight text derived from selected top comments
- published date, reading time, source link, and discussion link rendering
- Telegram HTML escaping in `src/message_builder.py`
- an existing `SummaryProvider = Callable[[HNStory], str]`
- an existing OpenAI summary provider in `src/openai_summary_provider.py`

The existing OpenAI summary provider was deliberately left unchanged. NVIDIA support was added as a separate structured provider rather than as another string summary provider.

## Decision

Use NVIDIA Build's OpenAI-compatible Chat Completions API as an optional `ReadingDecisionProvider`.

The provider returns a structured object with three fields:

```json
{
  "preview": "string",
  "hn_insight": "string",
  "why_trending": "string"
}
```

The selected operating model example is:

```text
minimaxai/minimax-m3
```

The model is not hardcoded in the provider. Runtime configuration still comes from `NVIDIA_MODEL`.

This decision is ADR-like in intent:

- Status: accepted for the current v1 implementation
- Scope: optional NVIDIA reading decisions only
- Non-goal: replacing extraction, changing the OpenAI provider, or redesigning Telegram delivery
- Consequence: LLM output can improve Preview, HN Insight, and Why Trending when available, but the non-LLM path remains the safety baseline

## Architecture

The implementation separates the new layer from the existing summary-provider interface.

```text
HNStory + ArticleExtraction
        |
        v
ReadingDecisionInput
        |
        v
NVIDIAReadingDecisionProvider
        |
        v
ReadingDecision(preview, hn_insight, why_trending)
        |
        v
message_builder fallback merge
        |
        v
Telegram HTML
```

Relevant files:

- `src/reading_decision.py` defines `ReadingDecisionInput`, `ReadingDecision`, and `ReadingDecisionProvider`.
- `src/nvidia_reading_decision_provider.py` implements `NVIDIAReadingDecisionProvider`.
- `src/main.py` creates the provider when `SUMMARY_PROVIDER=nvidia`.
- `src/message_builder.py` merges provider output into the existing Telegram message.
- `scripts/test_nvidia_reading_decision.py` provides a local dry-run path without sending Telegram messages.

The NVIDIA request uses:

- endpoint: `https://integrate.api.nvidia.com/v1/chat/completions`
- `temperature=0.2`
- `top_p=0.9`
- `max_tokens=800`
- `reasoning_effort="none"`
- `stream=False`

The provider parses only `choices[0].message.content` as the final JSON response. It does not parse `reasoning_content`.

## Model candidates

Three NVIDIA Build models were compared during the current implementation pass:

- `nvidia/nemotron-3-ultra-550b-a55b`
- `minimaxai/minimax-m3`
- `mistralai/mistral-medium-3.5-128b`

The comparison used the same fixed HN story, same extracted article text, same selected top comments, same system prompt, and same JSON schema.

## Evaluation method

The evaluation was a dry-run comparison, not a broad benchmark.

Measured during the dry run:

- approximate response time for the same story
- whether the model returned valid JSON with the required fields
- whether `preview` was specific to the article text
- whether `hn_insight` represented comments without overstating consensus
- whether `why_trending` explained the technical reason for attention
- whether the model avoided unsupported claims when evidence was weak
- Korean naturalness

Inferred from those observations:

- operational suitability for a daily GitHub Actions workflow
- fit with the project's evidence-first philosophy
- relative risk of over-explaining sparse evidence

## Results

| Model | Approx. response time | JSON/schema behavior | Preview | HN Insight | Why Trending | Notes |
| --- | ---: | --- | --- | --- | --- | --- |
| `nvidia/nemotron-3-ultra-550b-a55b` | ~4.4s | Stable structured output after disabling reasoning output | Good | Good | Sometimes inferred more than the evidence supported | Fastest candidate, but more willing to explain weak signals |
| `minimaxai/minimax-m3` | ~6.3s | Stable JSON output | Most specific in the test case | Careful when comments were sparse | Most aligned with evidence limits | Selected for v1 operation |
| `mistralai/mistral-medium-3.5-128b` | ~15s | Returned concise output, but sometimes left fields empty | Acceptable | Mixed | Conservative, sometimes too sparse | Slower without a clear quality gain in the tested case |

These timings are single-run observations from the same fixed story test. They should not be treated as statistically reliable latency benchmarks.

## Why MiniMax M3

`minimaxai/minimax-m3` was selected because it gave the best balance for this project:

- specific article-based preview text
- careful comment synthesis
- better willingness to state when evidence was insufficient
- good JSON adherence in the tested path
- natural Korean phrasing
- response time that is acceptable for a scheduled daily GitHub Actions job

The most important reason is philosophical rather than cosmetic: the project is evidence-first. A model that produces a less flashy answer but avoids overstating weak evidence is a better fit than a faster model that fills gaps too aggressively.

## Prompt refinement

The first prompt version allowed `why_trending` to repeat metadata already visible in the Telegram message.

Example of the problem:

```text
1338 points and 930 comments show high interest...
```

This was not useful because the Telegram message already shows score, comment count, source, published date, and reading time.

The system prompt was refined so `why_trending` should:

- not repeat score, comment count, published date, reading time, or source domain unless necessary
- focus on why developers found the story interesting
- explain the technical discussion, controversy, novelty, or practical implication
- stay around 100 Korean characters
- avoid generic phrases equivalent to "many people were interested", "high score", or "many comments"

The prompt also explicitly tells the model not to add evaluative claims such as "cutting-edge", "innovative", "groundbreaking", or "world-first" unless those claims appear in the provided source text.

## Fallback behavior

Provider failure must not break Telegram message generation.

The implemented fallback behavior is:

- if the NVIDIA request fails, the provider returns an empty `ReadingDecision`
- if JSON parsing fails, the provider returns an empty `ReadingDecision`
- if a field is missing, `null`, a list, a number, or another non-string value, that field becomes an empty string
- `preview` from the provider is used only when article extraction succeeded
- if article extraction failed, the existing preview-unavailable text is preserved
- `hn_insight` may still use provider output when comments are available
- `why_trending` is rendered only when the provider returns a non-empty value
- all LLM text is escaped before entering Telegram HTML

This keeps the default non-LLM Preview and HN Insight as the compatibility baseline.

## Operational considerations

GitHub Actions configuration uses:

- secret: `NVIDIA_API_KEY`
- variable: `SUMMARY_PROVIDER=nvidia`
- variable: `NVIDIA_MODEL=minimaxai/minimax-m3`
- variable: `NVIDIA_TIMEOUT_SECONDS=60`

The workflow passes:

```yaml
NVIDIA_API_KEY: ${{ secrets.NVIDIA_API_KEY }}
NVIDIA_MODEL: ${{ vars.NVIDIA_MODEL }}
NVIDIA_TIMEOUT_SECONDS: ${{ vars.NVIDIA_TIMEOUT_SECONDS }}
```

The local dry-run command is:

```bash
export NVIDIA_API_KEY="..."
export NVIDIA_MODEL="minimaxai/minimax-m3"
export NVIDIA_TIMEOUT_SECONDS="60"

python3 scripts/test_nvidia_reading_decision.py
```

The dry-run script can also compare models on a fixed story:

```bash
HN_STORY_ID="..." python3 scripts/test_nvidia_reading_decision.py
```

The script does not send Telegram messages and does not print the API key, authorization header, full article text, full comments, request payload, or raw model response.

## Limitations

The current evaluation is intentionally small.

- It used a fixed story comparison rather than a broad corpus.
- The response times are approximate single-run observations.
- The quality judgments are based on observed output for the tested case.
- The provider does not implement retries.
- The provider does not add a new Telegram message-splitting strategy.
- Field length limits reduce message growth, but they do not prove the full Telegram message can never exceed 4096 characters.
- The implementation relies on the model returning a JSON object in `choices[0].message.content`.

The current implementation is appropriate for v1 because failures fall back to deterministic output, but the model choice should be revisited after observing more story types.

## Future evaluation plan

Future comparisons should use a wider story set:

- comment-heavy stories
- comment-sparse stories
- technical deep dives
- product announcements
- controversial discussions
- stories with failed extraction
- stories with boilerplate-heavy article pages

Useful metrics to track:

- response time distribution
- empty field rate
- malformed JSON rate
- unsupported claim rate
- Korean naturalness
- usefulness of `why_trending`
- fallback frequency
- final Telegram message length

The model should be re-evaluated when NVIDIA model availability, latency, or pricing changes, or when the prompt is changed substantially.
