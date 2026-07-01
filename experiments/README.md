# Experiments

This directory is an engineering notebook for validating ideas before they are promoted to production. Each PoC captures a narrow question, the command used to inspect it, and any generated reports for later comparison.

This directory contains isolated Proofs of Concept used to evaluate reading-decision ideas before any production integration. These scripts are not the Telegram pipeline, do not send messages, and should not be treated as production entrypoints.

## Article Extraction PoC

File: `article_extraction_poc.py`

Purpose: evaluate whether useful article content can be extracted for free from a single URL using `trafilatura`.

Run:

```bash
python -m experiments.article_extraction_poc "https://example.com/article"
```

Output includes:

- extraction success or failure
- execution time
- extracted title, if available
- meta description, if available
- extracted plain text
- extracted text length

## Reading Decision PoC

File: `reading_decision_poc.py`

Purpose: compare multiple free article representations that may help a human decide whether to read an article.

Run:

```bash
python -m experiments.reading_decision_poc "https://example.com/article"
```

Compared outputs:

- title only
- title plus meta description
- title plus first meaningful paragraph
- title plus LSA extractive summary
- title plus LexRank summary
- title plus TextRank summary

Generated report:

- `reading_decision_report.md`

## Representation Analysis

File: `representation_analysis.py`

Purpose: inspect structural strengths and weaknesses of article representations using objective metrics only.

Run:

```bash
python -m experiments.representation_analysis
```

Metrics include:

- total words
- total characters
- sentence count
- extraction time
- duplicated sentences
- repeated title ratio
- whether code blocks dominate the output
- whether mathematical expressions dominate the output
- whether output starts with article context

Generated report:

- `representation_analysis.md`

## HN Comment Analysis

File: `hn_comment_analysis.py`

Purpose: inspect whether top-level Hacker News comments contain useful additional context for fast reading decisions.

Run:

```bash
python -m experiments.hn_comment_analysis
```

Output includes:

- story title
- HN score
- HN comment count
- top 3 top-level comments, when available
- comment score, when available
- comment length
- objective comment observations
- article-level comment metrics

Generated report:

- `hn_comment_analysis.md`

## Operational Readiness Benchmark

File: `operational_readiness_benchmark.py`

Purpose: measure whether the free deterministic reading-decision pipeline is operationally reliable across 100 live Hacker News stories with external URLs.

Run:

```bash
python -m experiments.operational_readiness_benchmark
```

Generated outputs:

- `operational_readiness_benchmark.csv`
- `operational_readiness_report.md`

## Notes

- Experiments may fetch live URLs and Hacker News data.
- Experiments do not call OpenAI or paid APIs.
- Experiments do not send Telegram messages.
- Experiments should remain decoupled from production modules unless a later production change explicitly promotes an idea.
