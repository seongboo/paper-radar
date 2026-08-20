# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current status: planning only — no code exists yet

As of the latest commit, this repository contains **only `README.md`**. There is no source code, no build system, no tests, no dependency manifest, and no CI. The project is at the concept/planning stage (기획 단계).

Practical consequences for working here:
- **Do not assume any code, module layout, or tooling exists.** There are no build/lint/test commands to run because there is nothing to build yet. Don't invent references to files that aren't present.
- The first substantive coding task will be **greenfield**: establish the project skeleton (language runtime, dependency manifest, entrypoint) before or alongside the first feature.
- `README.md` is the single source of truth for intent. It is written in **Korean**; keep new user-facing docs consistent with the existing language and terminology unless asked otherwise.

## What this project is

**paper-radar (논문 레이더 / "Paper Radar")** is a research-survey automation tool. The goal is to cut the time spent surveying new literature by automatically collecting, summarizing, and ranking new papers against the user's research interests, then delivering a daily digest.

## Intended architecture (the pipeline)

The README describes the system as a linear pipeline. When implementing, treat these as the natural stage boundaries:

1. **Collect** — Poll the arXiv API (by category — e.g. `cond-mat` — plus keyword and author filters) to gather newly published items. Journal sources are a later addition.
2. **Summarize** — Run each collected paper through an LLM to produce a short (~3-line) summary.
3. **Rank** — Score and sort papers by relevance to the user's interest profile (keywords/categories the user cares about).
4. **Deliver** — Emit a daily digest as Markdown and/or email. A planned extension is auto-saving results into the user's Obsidian vault.

The **interest profile** (keywords + categories used for both collection filtering and relevance scoring) is a central piece of configuration; defining it is listed as the first concrete next step.

## Intended tech stack (per README — not yet committed)

- **Python** as the implementation language.
- **arXiv API** for paper collection.
- **LLM** for summarization/ranking — the README names **Claude** and **Ollama** (local) as the candidate providers, implying the LLM layer should be pluggable across a hosted API and a local model.

Nothing above is pinned in code yet, so these are design intentions to honor, not existing constraints. Confirm specifics with the user before locking in dependencies or a provider.

## MVP scope and next steps (from README)

MVP, then expansion:
- arXiv polling (category/keyword/author) → collect new items
- LLM 3-line summary + relevance scoring/sorting against the interest profile
- Daily Markdown/email digest; (expansion) automatic Obsidian save

Open next steps still to be done:
- [ ] Define the interest keyword/category profile
- [ ] Produce one full day's digest end to end (collect → summarize → rank)

## Notes

- Project planning is tracked outside this repo in Obsidian (`0. Inbox/논문 레이더 (paper-radar).md`); the README is the mirror kept in git.
- Related sibling projects referenced in the README: `seongboo2`, `AARLA`, `inbox-triage`. They are not dependencies of this repo.
