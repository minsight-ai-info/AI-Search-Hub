# Web Chat Runner Browser Expansion Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the wrapper and skill docs to support `qwen`, `gemini`, and `grok` using the user's real Chromium browser profile, with login-wait and no-reply handling.

**Architecture:** Keep `scripts/run_web_chat.py` as the public entrypoint, add a generic Playwright driver for the new sites, and preserve the existing legacy site scripts. Browser startup changes from copied profiles to the real user-data directory plus explicit lock/error handling.

**Tech Stack:** Python 3.9, Playwright sync API, `unittest`

---

## File Structure

- `SKILL.md`
  - Update skill description, supported sites, and profile behavior.
- `scripts/run_web_chat.py`
  - Expand site registry.
  - Route between legacy scripts and the new generic script.
  - Replace profile-copy startup with real-profile startup and lock detection.
- `scripts/generic_web_chat_playwright.py`
  - Implement shared driver logic for `qwen`, `gemini`, and `grok`.
- `tests/test_run_web_chat.py`
  - Cover wrapper configuration and browser/profile helper logic.
- `tests/test_generic_web_chat_playwright.py`
  - Cover normalization and reply/login interpretation logic.

## Chunk 1: Add Failing Tests For Wrapper Changes

### Task 1: Wrapper site registry and command routing

**Files:**
- Create: `tests/test_run_web_chat.py`
- Modify: `scripts/run_web_chat.py`

- [ ] **Step 1: Write the failing test**

```python
def test_build_site_command_routes_qwen_to_generic_driver():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_run_web_chat -v`
Expected: FAIL because the new site and generic script routing do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Update `SITE_CONFIG` and command construction in `scripts/run_web_chat.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_run_web_chat -v`
Expected: PASS for routing tests.

### Task 2: Wrapper browser profile lock detection

**Files:**
- Create: `tests/test_run_web_chat.py`
- Modify: `scripts/run_web_chat.py`

- [ ] **Step 1: Write the failing test**

```python
def test_profile_appears_locked_when_singleton_lock_exists():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_run_web_chat -v`
Expected: FAIL because profile-lock detection is not implemented.

- [ ] **Step 3: Write minimal implementation**

Add helper logic for lock-file detection and browser launch selection.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_run_web_chat -v`
Expected: PASS for helper tests.

## Chunk 2: Add Failing Tests For Generic Driver Logic

### Task 3: Generic text normalization and answer diffing

**Files:**
- Create: `tests/test_generic_web_chat_playwright.py`
- Create: `scripts/generic_web_chat_playwright.py`

- [ ] **Step 1: Write the failing test**

```python
def test_latest_new_text_prefers_new_items_over_existing_baseline():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_generic_web_chat_playwright -v`
Expected: FAIL because the module does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create shared helper functions and the generic driver module skeleton.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_generic_web_chat_playwright -v`
Expected: PASS for the text helper tests.

### Task 4: Generic login/no-reply interpretation

**Files:**
- Create: `tests/test_generic_web_chat_playwright.py`
- Modify: `scripts/generic_web_chat_playwright.py`

- [ ] **Step 1: Write the failing test**

```python
def test_interpret_missing_reply_requests_login_when_login_phrase_present():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_generic_web_chat_playwright -v`
Expected: FAIL because interpretation helpers are incomplete.

- [ ] **Step 3: Write minimal implementation**

Add shared phrase matching and missing-reply interpretation helpers.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_generic_web_chat_playwright -v`
Expected: PASS for login/no-reply logic.

## Chunk 3: Integrate Runtime Behavior

### Task 5: Implement runtime wrapper startup changes

**Files:**
- Modify: `scripts/run_web_chat.py`
- Test: `tests/test_run_web_chat.py`

- [ ] **Step 1: Write or extend failing tests**

Cover the real-profile startup branch and explicit error messages where feasible through helper-level tests.

- [ ] **Step 2: Run tests to verify failure**

Run: `python3 -m unittest tests.test_run_web_chat -v`
Expected: FAIL for the new startup behavior.

- [ ] **Step 3: Write minimal implementation**

Remove copied-profile seeding from runtime flow and switch to direct user-data-dir usage.

- [ ] **Step 4: Run tests to verify pass**

Run: `python3 -m unittest tests.test_run_web_chat -v`
Expected: PASS.

### Task 6: Implement generic site runtime behavior

**Files:**
- Modify: `scripts/generic_web_chat_playwright.py`
- Test: `tests/test_generic_web_chat_playwright.py`

- [ ] **Step 1: Write or extend failing tests**

Add focused tests for retry-decision helpers and site config coverage.

- [ ] **Step 2: Run tests to verify failure**

Run: `python3 -m unittest tests.test_generic_web_chat_playwright -v`
Expected: FAIL before runtime helpers are complete.

- [ ] **Step 3: Write minimal implementation**

Implement ready/login/retry flow with one retry after login completion.

- [ ] **Step 4: Run tests to verify pass**

Run: `python3 -m unittest tests.test_generic_web_chat_playwright -v`
Expected: PASS.

## Chunk 4: Update Skill Documentation And Verify

### Task 7: Update skill documentation

**Files:**
- Modify: `SKILL.md`

- [ ] **Step 1: Update supported sites and startup behavior**

Document the new sites, generic behavior, and real-profile constraint.

- [ ] **Step 2: Verify the wording against implemented behavior**

Check that the examples and constraints match the code path.

### Task 8: Run final verification

**Files:**
- Verify: `scripts/run_web_chat.py`
- Verify: `scripts/generic_web_chat_playwright.py`
- Verify: `tests/test_run_web_chat.py`
- Verify: `tests/test_generic_web_chat_playwright.py`
- Verify: `SKILL.md`

- [ ] **Step 1: Run unit tests**

Run: `python3 -m unittest discover -s tests -v`
Expected: PASS.

- [ ] **Step 2: Run compilation checks**

Run: `python3 -m py_compile scripts/run_web_chat.py scripts/generic_web_chat_playwright.py tests/test_run_web_chat.py tests/test_generic_web_chat_playwright.py`
Expected: PASS.

- [ ] **Step 3: Inspect wrapper help output**

Run: `python3 scripts/run_web_chat.py --help`
Expected: includes `qwen`, `gemini`, and `grok`.

- [ ] **Step 4: Report any unverified runtime risks**

State clearly that real site interaction still depends on live DOMs and logged-in browser state.
