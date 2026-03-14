# AI Search Hub

[中文说明](README.zh-CN.md)

<div align="center">

### One Query. Multiple AI Providers.

[![GitHub stars](https://img.shields.io/github/stars/minsight-ai-info/AI-Search-Hub?style=flat-square)](https://github.com/minsight-ai-info/AI-Search-Hub/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/minsight-ai-info/AI-Search-Hub?style=flat-square)](https://github.com/minsight-ai-info/AI-Search-Hub/network/members)
[![GitHub issues](https://img.shields.io/github/issues/minsight-ai-info/AI-Search-Hub?style=flat-square)](https://github.com/minsight-ai-info/AI-Search-Hub/issues)
[![Type](https://img.shields.io/badge/type-open--source%20skill-black?style=flat-square)](https://github.com/minsight-ai-info/AI-Search-Hub)

</div>

AI Search Hub is an open-source browser-driven skill for sending the same query to multiple AI platforms and turning the results into a normalized workflow input.

Instead of building full crawlers for every site, this project focuses on:

- provider-native search and chat surfaces
- isolated browser sessions
- login recovery flows
- prompt dispatch
- reply extraction
- a future aggregation layer on top

## What This Repository Contains Today

The current repository is the execution layer behind the product idea.

It already includes:

- a unified runner: `scripts/run_web_chat.py`
- provider adapters for `qwen`, `doubao`, `yuanbao`, `longcat`, `gemini`, and `grok`
- isolated Chrome profile seeding from the user's active local profile
- login detection and wait-and-continue flows
- DOM-first text input to reduce interference from active desktop usage
- tests covering wrapper logic and site-driver behavior

The multi-provider aggregation entrypoint described by the project vision is the next implementation step.

## Why AI Search Hub

Many "search the whole web" systems eventually turn into:

- crawler maintenance
- fragile browser automation
- login and session handling
- anti-bot breakage
- per-site search tuning
- repetitive prompt and keyword iteration
- manual merging of fragmented results

AI Search Hub takes a narrower and more practical approach:

> reuse the search and retrieval interfaces that the platforms have already optimized.

The goal is not to out-build every provider's search stack.
The goal is to orchestrate them.

## Current Provider Status

| Provider | Status | Notes |
|---|---|---|
| Qwen | Working | Real query flow verified |
| Doubao | Working | Real query flow verified |
| Yuanbao | Working | Real query flow verified after login-flow fixes |
| LongCat | Working with caveat | Query flow works, but the site may rate-limit |
| Gemini | Experimental | Browser/profile startup and page-state handling still being refined |
| Grok | Experimental | Site verification and page-state handling still being refined |
| Wenxin | Planned | Not implemented yet |

## How It Works

1. Receive one prompt.
2. Open or attach to an isolated Chromium debug session.
3. Reuse the user's active local Chrome profile as the seed source.
4. Open the provider page and detect whether login is required.
5. Wait for login if needed, then continue automatically.
6. Enter the prompt, send it, and wait for a stable answer.
7. Write the answer to a standard output file for downstream workflows.

## Repository Layout

```text
scripts/
  run_web_chat.py
  generic_web_chat_playwright.py
  doubao_playwright.py
  yuanbao_playwright.py
  longcat_playwright.py

tests/
  test_run_web_chat.py
  test_generic_web_chat_playwright.py
  test_longcat_playwright.py

docs/
  superpowers/specs/
  superpowers/plans/
```

## Quick Start

Run a single provider through the unified wrapper:

```bash
python3 scripts/run_web_chat.py --site qwen --prompt "Latest AI news"
```

Supported `--site` values right now:

- `qwen`
- `doubao`
- `yuanbao`
- `longcat`
- `gemini`
- `grok`

## Verification

Run the current test suite:

```bash
python3 -m unittest tests.test_run_web_chat tests.test_generic_web_chat_playwright tests.test_longcat_playwright -v
```

Static syntax verification:

```bash
python3 -m py_compile scripts/run_web_chat.py scripts/generic_web_chat_playwright.py scripts/doubao_playwright.py scripts/longcat_playwright.py scripts/yuanbao_playwright.py
```

## Roadmap

- add a true hub entrypoint that returns normalized multi-provider JSON
- harden Gemini support
- harden Grok support
- add Wenxin support
- support aggregated result fusion on top of provider-native outputs

## Project Direction

AI Search Hub is meant to be a thin orchestration layer, not a giant crawler framework.

The long-term value is:

- one query
- multiple provider-native result channels
- one normalized output contract
- better downstream agent workflows
