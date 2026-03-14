# Web Chat Runner Browser Expansion Design

**Date:** 2026-03-14

## Goal

Extend the existing `web-chat-runner` skill so it can drive `qwen`, `gemini`, and `grok` in the same wrapper flow as the current supported sites, while using the user's own Chromium browser installation and its default profile instead of a copied debug profile.

## Current Context

- The repository currently exposes one wrapper: `scripts/run_web_chat.py`.
- Existing supported sites are `yuanbao`, `longcat`, and `doubao`.
- The wrapper currently seeds a separate `chrome_debug_profile_skill` directory by copying a browser profile and then launches Chrome against that copy.
- Existing site scripts are site-specific Playwright programs that connect over CDP and wait for manual login when needed.

## Requirements

1. Add support for `qwen`, `gemini`, and `grok`.
2. For the new sites, first open the browser to the target URL, then enter the user's prompt.
3. If the page has no usable reply or clearly requires login, prompt the user to log in and keep waiting until login completes, then continue automatically.
4. Use the user's browser and the browser's default profile instead of a copied debug profile.
5. Do not kill or modify the user's normal browser session automatically.
6. Preserve existing wrapper behavior for `yuanbao`, `longcat`, and `doubao` as much as possible.

## Constraints

- The automation stack is Playwright over Chrome DevTools Protocol, so practical support is limited to Chromium-family browsers.
- Reusing the real default profile is only reliable when a debuggable Chromium session is already available or when the profile is not locked by a separately running browser instance.
- This workspace is not a git repository, so design/plan files can be written locally but cannot be committed from this directory.
- Real end-to-end validation depends on live websites and logged-in user state, so automated tests must focus on configuration and branching logic.

## Chosen Approach

Keep `scripts/run_web_chat.py` as the only public wrapper, expand its site registry, and add one new generic Playwright driver for `qwen`, `gemini`, and `grok`.

This keeps the legacy site scripts intact while centralizing the new behavior in one place:

- Wrapper handles browser discovery, CDP reuse, default-profile startup, login waiting, and downstream dispatch.
- Legacy sites continue to call their dedicated scripts.
- New sites call a shared generic script that is configured per site by selectors and detection phrases.

## Architecture

### Wrapper

`scripts/run_web_chat.py` will:

- add site metadata for `qwen`, `gemini`, and `grok`
- route each site to either a legacy site script or the new generic driver
- prefer an existing CDP endpoint if one is already reachable
- otherwise launch a Chromium browser using the user's real user-data directory and the `Default` profile
- fail clearly if the profile appears locked and no debuggable browser session is available

### Generic Driver

A new script will:

- open the target URL
- wait for a prompt input area to become usable
- detect obvious login states before sending
- capture baseline visible text
- send the question
- wait for a stable new answer
- if login becomes required after send or no answer arrives, re-check login status and wait for manual login when appropriate
- retry the original prompt after login completion

### Site Configuration

Each new site will declare:

- URL
- prompt input selectors
- send button selectors
- login-related selectors/text
- answer container selectors
- generation-running selectors
- generation-done selectors
- optional blocked or unsupported-state text

## Error Handling

### Login Required

- If login is detected before send, print a login prompt and poll until the page is usable.
- If login is detected after send or after a no-reply timeout, wait for login and then retry the same prompt once.

### No Reply

- If no new reply appears and no login signals are present, return a clear failure explaining that the page may have changed or the site did not produce an answer.

### Browser/Profile Issues

- If no Chromium browser installation can be found, fail with a direct instruction to pass `--browser-path`.
- If the default profile appears to be in use and no CDP endpoint is available, fail with a direct instruction to close the browser or manually start it with remote debugging.

## Testing Strategy

### Automated

- Add `unittest` coverage for wrapper decision logic:
  - site routing
  - output path selection
  - command construction
  - browser/profile lock detection
- Add `unittest` coverage for the generic driver's pure logic:
  - text normalization
  - answer diffing
  - login/no-reply interpretation from visible text

### Manual

- Run wrapper help output.
- Run the unit test suite.
- Run Python bytecode compilation for scripts and tests.
- If environment allows, do live smoke runs for the new sites and observe login/no-login branches.

## Files To Change

- Modify `SKILL.md`
- Modify `scripts/run_web_chat.py`
- Add `scripts/generic_web_chat_playwright.py`
- Add tests under `tests/`

## Non-Goals

- Full refactor of the legacy site-specific scripts
- Support for non-Chromium automation stacks
- Silent browser profile cloning
