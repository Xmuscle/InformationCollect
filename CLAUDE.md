# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

An intelligence aggregation engine that scrapes tech/finance sources, enriches and summarizes them with LLM calls, and generates a structured Chinese daily briefing report. Python 3.11+ project managed with `uv`.

## Commands

```bash
# Install dependencies
uv sync

# Run the full daily report
uv run python cli.py

# Fast local smoke run (1 item per source)
uv run python cli.py --test

# Override source limit or output file
uv run python cli.py --limit 3
uv run python cli.py --output reports/daily_briefings/custom.md

# Run all tests
uv run pytest tests/ -v

# Run a single test file
uv run pytest tests/test_core.py -v

# Run a single test
uv run pytest tests/test_anti_hallucination.py -k grok_fallback_not_clickable -v

# Add dependencies
uv add <package>
uv add --group dev <package>
```

## Architecture

### End-to-end flow

`cli.py` is the only entrypoint used by local runs and the scheduled GitHub Actions job. It parses `--limit`, `--test`, and `--output`, calls `src.intel_collector.fetch_all_sources()`, passes the result into `src.report_generator.generate_report()`, then writes markdown into `reports/daily_briefings/`.

### Collection is split into two layers

- `src/external/fetch_news.py` is the older aggregator-style layer for sources that are still fetched as plain dictionaries from one shared module.
- `src/sensors/` contains source-specific fetchers for newer or more specialized integrations.

That split is intentional but transitional: the codebase still runs both paths in the same collection pass.

### Collector orchestration model

`src/intel_collector.py` is the runtime hub.

- Batch 1 runs independent sources concurrently with `ThreadPoolExecutor`.
- Batch 2 runs Grok-dependent work after Product Hunt results exist.
- The collector normalizes each source into category buckets like `tech_trends`, `capital_flow`, `product_gems`, `research`, `agent_research`, `social`, `community`, and `insights`.
- Research lists are deduplicated after collection by normalized title.

When changing fetch behavior, preserve the dependency ordering between Batch 1 and Grok follow-up work.

### Report generation responsibilities

`src/report_generator.py` is not just formatting. It also contains output-time enrichment rules:

- tech/research/insight sections call LLM summarization helpers
- insight articles may fetch full text through Jina before summarization
- Product Hunt items tagged with `grok-fallback` must stay non-clickable and instead render with a verification warning plus search link
- social output from Grok is treated as markdown and optionally post-validated

If you change output structure, keep the anti-hallucination behavior aligned with `tests/test_anti_hallucination.py`.

### Configuration model

`src/config.py` is the single source of truth for runtime configuration. It loads `.env` from the project root once, builds an immutable `IntelConfig`, and then exposes both `cfg` and backward-compatible module constants.

Resolution order is environment variables first, then defaults. Most modules import config values directly from `src.config`, so config changes propagate broadly.

### LLM and content-enrichment stack

Despite the filename, `src/utils/gemini_translator.py` currently implements the DeepSeek-backed translation and summarization helpers used during report generation.

Supporting utilities:

- `src/utils/jina_reader.py` fetches article body text through Jina and falls back to DuckDuckGo snippets for blocked/junk pages
- `src/utils/verifier.py` validates links so Grok-produced URLs can be flagged when unreachable

### Scheduled automation

`.github/workflows/daily-report.yml` is the production path. It installs Python via `uv`, runs `uv run python cli.py`, and commits the generated report back into this repo on a daily cron. The workflow has a 15-minute timeout, which matches the runtime budget reporting printed by the collector.

## Testing

Tests are lightweight and do not require live API keys.

- `tests/test_import_smoke.py` verifies the main modules import cleanly via `src.*`
- `tests/test_core.py` covers config, deduplication, report rendering, helper utilities, and Grok-report validation behavior
- `tests/test_graceful_degradation.py` ensures empty or partial intel payloads still render reports
- `tests/test_anti_hallucination.py` locks the Product Hunt Grok-fallback rule: guessed URLs must not render as clickable markdown links

## Environment

Secrets live in `.env` or CI environment variables. The code currently reads `GITHUB_TOKEN`, `XAI_API_KEY`, `PRODUCTHUNT_TOKEN`, and `DEEPSEEK_API_KEY` from `src/config.py`.

Standard `HTTP_PROXY` and `HTTPS_PROXY` environment variables are supported for networked fetches.
