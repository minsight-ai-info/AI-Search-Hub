# Web Chat Runner Interaction Isolation Design

**Date:** 2026-03-14

## Goal

Reduce accidental interference from the user while chat automation is running, especially when the user keeps using the computer during a run.

## Observed Problem

- The current automation can reuse an existing page in the connected browser context.
- Some input paths still rely on `page.keyboard`, which is more fragile when the automation window is focused or touched.
- When the user interacts with the automation browser window, focus and page state can drift away from what the script expects.

## Design

### Dedicated Automation Page

- Each automation run should create its own dedicated page instead of reusing the last live page in the context.
- Login checks and prompt sending should stay on that dedicated page for the whole run.
- Existing blank pages may remain, but the automation flow should not switch to whichever page happens to be active.

### DOM-First Input

- Input should prefer locator-level fill APIs and DOM-side value assignment.
- Keyboard events should become a last-resort fallback only.
- This reduces dependence on browser focus and user input state.

### Scope

- Update the generic driver used by `qwen`, `gemini`, and `grok`.
- Update wrapper login checks for legacy sites so they do not reuse an arbitrary page.
- Update legacy site scripts so they also prefer DOM-first input and dedicated pages when connected over CDP.

## Constraints

- If the user actively clicks inside the automation browser window, interference is still possible.
- The design reduces incidental interference; it does not make the browser immune to direct human interaction.

## Testing Strategy

- Add unit tests for input helper behavior to verify the code prefers non-keyboard fill paths.
- Add unit tests for wrapper/browser helper logic already touched in this repo.
- Re-run live tests on at least one working site (`qwen`) after the change.
