# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

An AI-powered intelligence aggregation engine that scrapes 12+ tech/finance data sources, translates/summarizes via Gemini, and generates a structured Chinese daily briefing report. Python 3.11+, managed by uv.

## Commands

```bash
# Install dependencies
uv sync

# Run full daily report
uv run python cli.py

# Test mode (1 item per source, fast)
uv run python cli.py --test

# Run tests
uv run pytest tests/ -v

# Run a single test file
uv run pytest tests/test_core.py -v

# Add a dependency
uv add <package>

# Add a dev dependency
uv add --group dev <package>
```

## Architecture

### Two-tier data collection (historical, consolidation planned)

- **Tier 1 (Aggregator)**: `src/external/fetch_news.py` — HN, GitHub, 36Kr, V2EX, WallStreetCN via a single module
- **Tier 2 (Sensors)**: `src/sensors/` — independent per-source modules (Product Hunt, ArXiv, HF Papers, Grok/X, HN Blogs, TechCrunch, MIT-TR)

### Core pipeline (cli.py → collector → generator)

1. `cli.py` — CLI entry point, parses args, orchestrates fetch + report
2. `src/intel_collector.py` — concurrent fetch via ThreadPoolExecutor with batch ordering (Batch 1: independent sources in parallel; Batch 2: Grok calls that depend on Batch 1 results)
3. `src/report_generator.py` — renders collected intel into a markdown report with anti-hallucination logic

### Key modules

- `src/config.py` — `IntelConfig` singleton. Priority: env vars > `.env` > defaults
- `src/utils/gemini_translator.py` — Gemini-based Chinese translation and summarization
- `src/utils/jina_reader.py` — full-text web extraction with DDG fallback
- `src/utils/verifier.py` — link validity verification

### Design patterns

- **Graceful degradation**: missing API keys or empty responses skip the source rather than crash
- **Anti-hallucination**: Grok fallback URLs are marked as unverified and rendered without clickable links
- **Concurrent with ordering**: ThreadPoolExecutor for parallelism, but respects dependency ordering between batches

## Testing

Tests are fast (<1s) and require no API keys. Three categories:
- `test_import_smoke.py` — all 16 modules import cleanly
- `test_anti_hallucination.py` — Grok fallback URLs don't become clickable links
- `test_graceful_degradation.py` — missing keys/empty data don't crash
- `test_core.py` — core functionality

## Environment

API keys go in `.env` (see `.env.example`). Minimum requirement: `GITHUB_TOKEN`. Optional: `XAI_API_KEY`, `PRODUCTHUNT_TOKEN`, `GEMINI_API_KEY`.

Proxy config via standard `HTTP_PROXY`/`HTTPS_PROXY` env vars.
