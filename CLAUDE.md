# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

**paper-radar (논문 레이더)** is a research-survey automation tool: it polls arXiv for new papers in the user's categories, produces a 3-line LLM summary and a relevance score per paper against the user's interest profile, and renders a ranked daily Markdown digest. The MVP pipeline (milestones M0–M3 in `DESIGN.md`) plus the M4 delivery extensions (Obsidian copy, SMTP email, cron guide) are implemented and tested; remaining M4 items (Batches API migration, journal sources) are open.

User-facing docs (`README.md`, `DESIGN.md`) and CLI/log messages are in **Korean** — keep new user-facing text consistent with that. `DESIGN.md` is the design plan the code follows; update it when architecture-level decisions change.

## Commands

```bash
uv sync                      # install deps (Python 3.11+, uv-managed)
uv run pytest                # run all tests (fast, no network/API key needed)
uv run pytest tests/test_rank.py -k keyword_boost   # single file / single test
uv run paper-radar --help    # CLI: run | collect | digest [--date YYYY-MM-DD]
```

There is no linter/formatter configured yet.

**Sandbox caveat:** in the Claude Code remote environment, `export.arxiv.org` is blocked by the proxy and no `ANTHROPIC_API_KEY` is set, so `run`/`collect` cannot be exercised live here. Verify behavior through the test suite (stubs cover both), and leave live-run verification to the user's machine.

## Architecture

Linear pipeline; one module per stage, wired in `src/paper_radar/pipeline.py` with dependency injection (store, fetch iterator, LLM client are passed in — this is what makes the tests network-free):

| Stage | Module | Notes |
|---|---|---|
| Collect | `collect.py` | `arxiv` package (handles 3s rate limit/paging); recent-window query + dedupe against SQLite makes skipped days self-healing |
| Analyze | `llm.py` | **One LLM call per paper** returns `{summary(3 lines), score 0–10, reason}` via JSON-schema structured output — never split into separate summarize/score calls |
| Rank | `rank.py` | `final_score = llm_score + deterministic boosts` (author match +3, keyword weights capped at +4) |
| Digest | `digest.py` | Markdown to `digests/YYYY-MM-DD.md`, top-N detailed + rest as one-liners; optional Obsidian copy |
| Deliver | `mailer.py` | Optional SMTP email of the digest (config `digest.email`); password comes **only** from the `SMTP_PASSWORD` env var, never the profile. A send failure logs an error but never fails the run |
| State | `store.py` | Single SQLite file (`radar.db`): `papers` (dedupe by arxiv_id, `seen_date` groups a day's digest), `analyses` (cache), `runs` |

Models (pydantic) live in `models.py`; `profile.yaml` (schema in `models.Profile`, example in `profile.example.yaml`) is loaded by `config.py`.

### Invariants to preserve

- **Analysis cache key** is `(arxiv_id, profile.analysis_hash())`. The hash covers only fields that change LLM output (`interest`, `llm.model`, `llm.language`) — keywords/authors are deliberately excluded so editing boosts never invalidates the cache. If you add a field that alters the prompt, add it to `analysis_hash()`.
- `llm.ANALYSIS_SCHEMA` (JSON schema sent to providers) and `models.Analysis` (pydantic validation) must stay in sync.
- A failed analysis (`AnalysisError`) skips that paper only; the pipeline never aborts a whole digest for one paper.
- LLM providers are pluggable behind `llm.LLMClient` (protocol): `ClaudeClient` (default) and `OllamaClient`. Both must return the same `Analysis` via schema-forced JSON. Don't leak provider specifics outside `llm.py`.
- Tests never hit the network: arXiv is stubbed via `SimpleNamespace` results (`paper_from_result` is the seam), the LLM via `tests/conftest.py::FakeLLM`.

## Claude API specifics

The `anthropic` dependency is **1.x** (breaking changes vs 0.x). Current-shape calls used here: `output_config={"format": {"type": "json_schema", ...}, "effort": ...}` on `messages.create`, and server-side refusal fallback via `client.beta.messages.create(betas=["server-side-fallback-2026-07-01"], fallbacks="default", ...)` (config-gated by `llm.fallback`). Don't regress to 0.x patterns (`output_format={...}` dict, `temperature`, prefill). Default model is `claude-opus-5`; cost knobs are `llm.effort` and switching provider/model in the profile — that's the user's call, not code's.

## Gitignored local files

`profile.yaml` (personal settings — commit changes to `profile.example.yaml` instead), `radar.db`, `digests/`. If asked to change digest output or profile schema, update the example file and tests together.

## Related: paper reader on `gh-pages`

The `gh-pages` branch holds a separate static web app (논문 리더, served at https://seongboo.github.io/paper-radar/), not part of the Python package. It opens an arXiv paper from `?arxiv=<id>`; the digest's "리더로 열기" links (`digest.reader_url`, rendered in `digest._open_links`) depend on that query parameter, so keep the two in sync. `main` and `gh-pages` share no files — never merge one into the other.
