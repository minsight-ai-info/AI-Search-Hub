# Web Chat Runner Interaction Isolation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make browser automation runs less sensitive to incidental user interaction by using dedicated pages and DOM-first input.

**Architecture:** Keep the existing wrapper and site scripts, but change page selection so each run uses a dedicated page and change input handling so keyboard events are only a fallback. Apply the same pattern to the generic driver and the legacy site scripts.

**Tech Stack:** Python 3.9, Playwright sync API, `unittest`

---

## File Structure

- `scripts/generic_web_chat_playwright.py`
  - Change page lifecycle to use a dedicated page for the run.
  - Change input handling to avoid keyboard-first behavior.
- `scripts/run_web_chat.py`
  - Change login pre-check flow to stick to one dedicated page.
- `scripts/yuanbao_playwright.py`
  - Use a dedicated page and DOM-first input.
- `scripts/longcat_playwright.py`
  - Use a dedicated page and DOM-first input.
- `scripts/doubao_playwright.py`
  - Use a dedicated page and DOM-first input.
- `tests/test_generic_web_chat_playwright.py`
  - Add failing tests for DOM-first input behavior.

## Chunk 1: Input Handling

### Task 1: Test DOM-first fill behavior

**Files:**
- Modify: `tests/test_generic_web_chat_playwright.py`
- Modify: `scripts/generic_web_chat_playwright.py`

- [ ] **Step 1: Write failing tests**
- [ ] **Step 2: Run `python3 -m unittest tests.test_generic_web_chat_playwright -v` and confirm failure**
- [ ] **Step 3: Implement locator fill / DOM fallback behavior**
- [ ] **Step 4: Re-run `python3 -m unittest tests.test_generic_web_chat_playwright -v` and confirm pass**

## Chunk 2: Dedicated Pages

### Task 2: Stop reusing arbitrary live pages

**Files:**
- Modify: `scripts/generic_web_chat_playwright.py`
- Modify: `scripts/run_web_chat.py`
- Modify: `scripts/yuanbao_playwright.py`
- Modify: `scripts/longcat_playwright.py`
- Modify: `scripts/doubao_playwright.py`

- [ ] **Step 1: Implement dedicated-page helpers and wire them into each flow**
- [ ] **Step 2: Re-run targeted unit tests**
- [ ] **Step 3: Run live smoke test on `qwen`**

## Chunk 3: Final Verification

### Task 3: Full verification

**Files:**
- Verify: `scripts/run_web_chat.py`
- Verify: `scripts/generic_web_chat_playwright.py`
- Verify: `scripts/yuanbao_playwright.py`
- Verify: `scripts/longcat_playwright.py`
- Verify: `scripts/doubao_playwright.py`
- Verify: `tests/test_generic_web_chat_playwright.py`

- [ ] **Step 1: Run `python3 -m unittest discover -s tests -v`**
- [ ] **Step 2: Run `python3 -m py_compile scripts/run_web_chat.py scripts/generic_web_chat_playwright.py scripts/yuanbao_playwright.py scripts/longcat_playwright.py scripts/doubao_playwright.py tests/test_run_web_chat.py tests/test_generic_web_chat_playwright.py`**
- [ ] **Step 3: Run a live `qwen` wrapper test and compare the result with the previous behavior**
