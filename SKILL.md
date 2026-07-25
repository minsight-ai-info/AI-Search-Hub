---
name: ai-search-hub
description: >
  Run verified domestic AI search platforms through camofox sessions: Qwen, Doubao,
  Kimi, MiniMax Agent, and LongCat. Supports one-site execution and coordinated
  multi-site polling with final-answer extraction.
---

# AI Search Hub（国内 / camofox）

Use this project for Chinese web research or Chinese AI-platform searches through the verified domestic sites only:

- `qwen` — Chinese public web and Alibaba-related queries
- `doubao` — ByteDance ecosystem and Chinese trends
- `kimi` — long-form research and document synthesis
- `minimaxi` — MiniMax Agent / general Chinese tasks
- `longcat` — LongCat, local-life context, and Chinese web retrieval

## Scope policy

- Do **not** attempt, route to, or batch foreign platforms.
- Do **not** route to Yuanbao by default: its reusable login and long-answer path are not verified.
- Never treat a model-generated answer as proof; distinguish official sources, independent testing, and media/community claims.

## Prerequisites

- `camofox-browser` is running on `localhost:9377`.
- A saved session exists for the target platform. Verify with:

```bash
camofox-browser session list --format json
```

Supported session names: `qwen`, `doubao`, `kimi`, `minimaxi`, `longcat`.

Never ask for, receive, or type passwords, OTPs, cookies, or other secrets. For login, open the page and let the user scan QR / enter credentials themselves; save the session after success.

## Single platform

```bash
cd ~/ai-search-hub
python3 scripts/run_camofox_chat.py \
  --site qwen \
  --prompt "请检索并区分官方资料、独立测试和媒体传闻。" \
  --timeout 250 \
  --min-answer-chars 300 \
  --output ~/artifacts/documents/answer.txt
```

## Batch platform execution

Use this only when cross-platform comparison is useful:

```bash
python3 scripts/run_camofox_batch.py \
  --sites qwen doubao kimi minimaxi longcat \
  --prompt "你的研究问题" \
  --timeout 250 \
  --min-answer-chars 300 \
  --stable-rounds 3 \
  --output-dir ~/artifacts/documents/ai-search-hub-run
```

The runner serializes navigation/submission, then polls platform tabs concurrently. A transient camofox RPC timeout is retried without closing the tab. Inspect `batch-summary.json` before reporting any multi-platform conclusion.

## Platform extraction notes

- Qwen: requires `Thinking completed` and `Regenerate` before accepting the answer.
- Doubao: checks final assistant `data-streaming=false`; surfaces hidden SSE rate-limit errors.
- Kimi: discards exposed `thinking-container` content and keeps the final Markdown block.
- MiniMax: writes to the ProseMirror editor through `data-testid=message-textarea`, then extracts `assistant-segment-active`.
- LongCat: extracts the final `.mt-markdown-body`, excluding search-state UI such as `Found N results`.

## Verification

```bash
python3 -m unittest tests/test_phase1_reliability.py -q
python3 -m py_compile scripts/camofox_runner.py scripts/run_camofox_chat.py scripts/run_camofox_batch.py
```

Put generated results and screenshots under `~/artifacts/`; do not add them to git.
