# Operational Readiness Benchmark

Generated: 2026-07-01T04:11:49Z

This isolated benchmark measures the current free, deterministic HN Daily Digest reading-decision pipeline against live Hacker News stories. It does not call OpenAI, send Telegram messages, modify production code, or change the production message format.

## Dataset Summary

- Total tested: 100
- Total skipped: 3
- Source endpoints configured: topstories, beststories, newstories
- Source endpoints represented: topstories
- Skipped breakdown: missing_external_url_or_invalid_story: 2, duplicate_url: 1

## Article Extraction

- Success rate: 81.0% (81/100)
- Failure reason breakdown: success: 81, empty_extraction: 6, network_error: 4, too_short: 3, access_blocked_401_403: 3, timeout: 2, rate_limited_429: 1
- Top failing domains: twitter.com: 2, docs.mistral.ai: 1, hatari.frama.io: 1, hengefinder.com: 1, economist.com: 1, gutenberg.org: 1, nochan.net: 1, marcin.juszkiewicz.com.pl: 1, youtube.com: 1, washingtonpost.com: 1
- Average extracted word count: 1813.9
- Average elapsed time: 1.37s
- Total elapsed time: 158.55s

## Published Date

- Extraction rate: 82.0% (82/100)
- Examples where found:
  - anthropic.com: Claude Sonnet 5 (2026-06-30)
  - thereallo.dev: Claude Code is steganographically marking requests (2026-06-29)
  - github.com: Google copybara: moving code between repositories (2016-09-08)
  - forbes.com: Supersonic flight returning to US after half-century ban (2026-06-30)
  - en.wikipedia.org: Forestiere Underground Gardens (2005-02-21)
- Examples where missing:
  - twitter.com: Department of Commerce has lifted export controls on Claude Fable 5 and Mythos 5
  - hatari.frama.io: Hatari – Online Atari ST/STE/TT/Falcon Emulator
  - hengefinder.com: Hengefinder
  - economist.com: Americans see their country's past, present and future
  - gutenberg.org: Memoirs of Extraordinary Popular Delusions and the Madness of Crowds (1852)

## Preview Quality

- Preview candidate success rate: 77.0% (77/100)
- Average preview length: 175.0
- Suspicious preview examples:
  - en.wikipedia.org: starts_with_title; Forestiere Underground Gardens The Forestiere Underground Gardens in Fresno, California are a series of subterranean...
  - twitter.com: missing; empty_extraction
  - claude.com: starts_with_title; Claude Science beta Your research partner for rigorous science The Claude Science app runs analyses, searches databases, and...
  - docs.mistral.ai: missing; Extracted text word count was below 80.
  - hatari.frama.io: missing; Extracted text word count was below 80.
  - home.cern: starts_with_title; CERN bids farewell to the LHC and enters Long Shutdown 3 The Large Hadron Collider is embarking on its most ambitious upgrade...
  - verdagon.dev: missing; 
  - taonaw.com: starts_with_title; Have You Restarted Your Computer This Week? I like restarting my Mac on Saturday mornings. It’s a silly thing really. You...

## Source Type Classification

- Distribution: Article: 92, Project / Repository: 4, News: 3, Documentation: 1
- Generic `Article` fallback count: 92
- Examples per type:
  - Article: anthropic.com: Claude Sonnet 5; thereallo.dev: Claude Code is steganographically marking requests; forbes.com: Supersonic flight returning to US after half-century ban
  - Documentation: docs.mistral.ai: Leanstral 1.5
  - News: apnews.com: Supreme Court upholds broad conception of birthright citizenship; washingtonpost.com: Medicare starts covering GLP-1 drugs for weight loss; reuters.com: Crypto firms have spent $189M so far on 2026 US election, report says
  - Project / Repository: github.com: Google copybara: moving code between repositories; github.com: Show HN: C++, Java and C# light-weight-logger; github.com: Linux for the Sega MegaDrive

## HN Insight

- Top comment availability rate: 93.0% (93/100)
- HN insight candidate rate: 92.0% (92/100)
- Average top comment length: 591.2
- Percentage containing links: 23.7%
- Percentage containing code-like formatting: 5.4%
- Useful-looking comment examples:
  - anthropic.com: The cost per task chart is telling me that I should _never_ use Sonnet 5 above medium effort level - Opus always performs...
  - thereallo.dev: There are some commentors in this thread downplaying the severity of a service provider being less than transparent about...
  - github.com: To those who have used it: is it handy for situations where you have multiple repos that want to share a little code, but it's...
  - forbes.com: If you really want to make an impact on the noise floor, ban gasoline leaf blowers.
  - en.wikipedia.org: Related: “The underground world of hobby tunneling” https://news.ycombinator.com/item?id=39245893 272 points | Feb 3, 2024 |...
- Low-value comment examples:
  - anthropic.com: Nice! I go to the x20 again.

## Operational Readiness

### What Appears Reliable

- Article extraction produced usable text for 81.0% of tested stories.
- Preview candidates were available for 77.0% of tested stories.
- HN top-level comment context was available for 93.0% of tested stories.

### What Appears Risky

- Extraction failures remain common enough to require fallback behavior: empty_extraction: 6, network_error: 4, too_short: 3, access_blocked_401_403: 3, timeout: 2, rate_limited_429: 1.
- Suspicious or missing preview candidates were observed for 44 stories.
- Published-date coverage was 82.0%, so dates should be treated as opportunistic metadata.

### What Should Remain Fallback-Only

- Access-blocked, rate-limited, timed-out, non-HTML/PDF, empty, and too-short article extractions should remain fallback-only in this benchmark context.
- Generic `Article` source-type classification should be treated as a coarse fallback label, not a strong content signal.
- Low-value HN comments should remain optional context and should not override article-derived previews.

No production implementation is proposed here; this file is measurement only.
