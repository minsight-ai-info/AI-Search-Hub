---
name: ai-search-hub
description: Run the AI Search Hub browser automation scripts for Yuanbao, LongCat, Doubao, Qwen, Gemini, and Grok. Use this skill when the user wants to ask one of those sites a prompt, auto-start or attach to a Chrome DevTools session on port 9222, seed an isolated debug browser profile from the user's local browser data, detect whether login is required, wait for the user to finish logging in if needed, and then continue automatically.
---

# AI Search Hub

Use this skill only for this repository's AI Search Hub browser automation scripts:

- `scripts/yuanbao_playwright.py`
- `scripts/longcat_playwright.py`
- `scripts/doubao_playwright.py`
- `scripts/qwen_playwright.py`
- `scripts/gemini_playwright.py`
- `scripts/grok_playwright.py`

## When To Use

Use this skill when the user asks to:

- run one of the supported chat sites from this repo
- normalize invocation across the three scripts
- auto-start a debug Chromium-family browser session
- detect whether `127.0.0.1:9222` is available
- prompt for login if the target site is not logged in, then continue automatically
- seed an isolated debug profile from the user's local browser data

## How To Run

Run the bundled wrapper script instead of calling the site script directly:

```bash
python3 scripts/run_web_chat.py --site doubao --prompt "Give me a short Hangzhou food guide."
```

Key arguments:

- `--site yuanbao|longcat|doubao|qwen|gemini|grok`
- `--prompt "..."` required
- `--repo-root <path>` if the current working directory is not the repo root
- `--cdp-http http://127.0.0.1:9222` to reuse an existing DevTools endpoint
- `--browser-path <path>` to force a specific Chromium-family browser binary
- `--debug-profile-dir <path>` to control the isolated debug profile location
- `--user-data-source <path>` to force a specific source browser user-data-dir
- `--output <path>` to control the destination file

## Workflow

The wrapper script is the low-freedom path and should be preferred over hand-rolling the sequence.

It does the following:

1. Finds the repo root and target site script.
2. Reuses `--cdp-http` if `9222` is already listening.
3. Otherwise seeds an isolated Chromium-family debug profile from the user's source browser data and starts the browser with a remote-debugging port, opening the requested site directly instead of leaving a separate `about:blank` startup tab behind.
4. For legacy sites (`yuanbao`, `longcat`, `doubao`), opens the target site and checks for login UI before dispatching the site-specific script.
5. For generic sites (`qwen`, `gemini`, `grok`), opens the target site, enters the prompt, and waits for a reply.
6. If the site requires login or produces no usable reply because login is required, prints a prompt and waits until login completes, then continues automatically.
7. Invokes the matching site script with standardized flags and the resolved `--cdp-url`.
8. Reuses the single startup page when possible so the browser does not keep an extra blank tab, and prefers DOM-side text entry over keyboard typing to reduce accidental interference from the user working elsewhere.

## Site Notes

- `doubao`: requires a logged-in session. The visitor page usually does not answer prompts.
- `yuanbao`: login may appear as a modal with QQ, WeChat, or last-login buttons even when the page shell is visible.
- `longcat`: the wrapper prefers a new chat before sending unless `--no-new-chat` is requested downstream.
- `qwen`, `gemini`, `grok`: each has its own Playwright entry script backed by a shared site-chat core. `gemini` first targets the visible composer and attempts the send once before falling back to the login-wait loop, because the landing page exposes a real textbox even when the account is not yet in a usable chat state.

## Constraints

- Prefer headed Chromium browsers for login-recovery flows. Headless mode only makes sense when the copied debug profile is already logged in.
- Do not kill the user's normal browser session unless the user explicitly asks for that.
- The wrapper copies browser data into an isolated debug profile and skips lock files, so the user's normal browser can stay open.
- The wrapper bypasses Python proxy settings for local DevTools requests because `http://127.0.0.1:9222/json/version` may otherwise return a false `502`.
