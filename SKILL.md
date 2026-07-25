---
name: ai-search-hub
description: >
  Multi-platform AI search aggregation via camofox browser automation.
  Use this skill when the user wants to search the web, social media, or Chinese content ecosystems
  through Gemini, Grok, Qwen, Doubao, Yuanbao, LongCat, MiniMax, or Kimi.
  Routes questions to the best platform, drives the camofox browser on port 9377,
  and returns the structured answer to Hermes.
---

# AI Search Hub (camofox edition)

A Hermes-compatible skill that reuses the AI-Search-Hub routing strategy and platform coverage,
but drives the **camofox browser** (`localhost:9377`) instead of Playwright/Chromium.

## When To Use

Use this skill when the user asks to:

- search the web, social media, or Chinese content ecosystems through multiple AI platforms
- run one of the supported chat sites: `doubao`, `gemini`, `grok`, `kimi`, `longcat`, `minimaxi`, `qwen`, `yuanbao`
- route a question to the best platform based on its content ecosystem
- reuse the camofox browser session instead of launching a new Chromium instance

## Prerequisites

1. camofox-browser installed and running as a systemd user service on `localhost:9377`
2. Python 3.10+ with `camofox-browser` CLI available in `PATH`
3. For login-required sites, complete login once inside the camofox browser and save the session:
   ```bash
   camofox-browser session save <site-name>
   ```
   Future runs will reuse that session automatically.

## Routing Strategy

Do not send every question to every platform. Analyze the question first, then route to the platform(s)
whose underlying data world is most likely to contain the best answer.

See `ROUTING.md` for the full decision framework. Quick reference:

| Question Type | Recommended Site | Parent Company |
|---|---|---|
| Twitter / X / real-time social | `grok` | xAI |
| Google / global web | `gemini` | Google |
| 微信公众号 / WeChat content | `yuanbao` | 腾讯 |
| 抖音 / 头条 / ByteDance trends | `doubao` | 字节跳动 |
| 美团 / 大众点评 / 本地生活 | `longcat` | 美团 |
| 淘宝 / 阿里 / 通用中文 | `qwen` | 阿里巴巴 |
| 用户明确要求 MiniMax / MiniMax Agent | `minimaxi` | MiniMax |
| 长文档 / 研究资料 / Kimi 指定 | `kimi` | 月之暗面 |

## How To Run

Use the `terminal` tool to execute the wrapper script:

```bash
cd /path/to/AI-Search-Hub
python3 scripts/run_camofox_chat.py \
  --site qwen \
  --prompt "Give me a short Hangzhou food guide." \
  --timeout 60 \
  --stable-rounds 3 \
  --interval 2
```

Key arguments:

- `--site` — one of `doubao`, `gemini`, `grok`, `kimi`, `longcat`, `minimaxi`, `qwen`, `yuanbao`
- `--prompt` — the question to send (required)
- `--output` — optional file path to save the answer
- `--timeout` — max seconds to wait for the final answer (default: 180)
- `--stable-rounds` — how many unchanged polls mean the answer is complete (default: 4)
- `--interval` — polling interval in seconds (default: 2.0)
- `--login-timeout` — max seconds to wait for manual login (default: 600)
- `--repo-root` — repository root path if cwd is not the repo root

## Workflow

The wrapper script does the following:

1. Opens the target site URL in camofox via `camofox-browser open`.
2. Waits for login if the site shows a login UI (prints a notice and polls for up to `--login-timeout` seconds).
3. Finds the input textbox from the camofox accessibility snapshot.
4. Types the prompt and submits it.
5. Polls camofox snapshots until the assistant answer stabilizes.
6. Cleans noise text (AI-generated disclaimers, UI fragments) and returns the answer.
7. Optionally writes the answer to `--output`.

## Session Reuse

camofox supports saved sessions so you do not have to log in every time:

```bash
# After logging in once in the camofox browser:
camofox-browser session save qwen

# The wrapper will reuse this session on subsequent runs.
```

The wrapper also handles sessions automatically:

- First run: detects no saved session, opens fresh, waits for login, saves session after successful login.
- Subsequent runs: detects saved session, loads it, skips login wait.
- If login markers are still present after waiting, the wrapper warns you and continues; complete login in the camofox browser and rerun to capture the session.

To list saved sessions:

```bash
camofox-browser session list
```

To delete a stale session:

```bash
camofox-browser session delete qwen
```

## Site Notes

- `doubao`: requires a logged-in session for most prompts.
- `yuanbao`: login may appear as a modal with QQ, WeChat, or last-login buttons.
- `longcat`: prefers a new chat before sending.
- `qwen`, `gemini`, `grok`, `minimaxi`, `kimi`: open the site directly and send the prompt.
- If a site returns a daily usage limit or region block, the wrapper will surface that text as the answer.

## Constraints

- This skill depends on the camofox browser service running on `localhost:9377`.
- Do not kill the user's normal browser session; camofox uses an isolated Firefox profile.
- If the camofox tab pool is full, close unused tabs with `camofox-browser close <tabId>`.
