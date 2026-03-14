<div align="center">

# AI Search Hub

### One Query. All Search.

[中文](README.md)

[![Repo](https://img.shields.io/badge/Repo-GitHub-181717?style=flat-square&logo=github)](https://github.com/minsight-ai-info/AI-Search-Hub)
[![Type](https://img.shields.io/badge/type-open--source%20skill-black?style=flat-square)](https://github.com/minsight-ai-info/AI-Search-Hub)
[![Status](https://img.shields.io/badge/status-active-success?style=flat-square)](https://github.com/minsight-ai-info/AI-Search-Hub)
[![Mode](https://img.shields.io/badge/mode-browser--driven-blue?style=flat-square)](https://github.com/minsight-ai-info/AI-Search-Hub)

**An open-source skill for aggregating platform-native AI search.**
**Send one query, search multiple AI platforms in parallel.**

</div>

---

## A Single Entry for Platform-Native AI Search

AI Search Hub is an open-source skill that turns fragmented AI search surfaces into one reusable search hub.

It is not trying to make you maintain:

- fragile crawler stacks
- separate browser automation flows for every provider
- endless login, captcha, rate-limit, and anti-bot recovery
- constant keyword and prompt tuning
- manual cleanup of scattered results

Its job is simple:

> **Aggregate the search capabilities major AI platforms have already optimized, and make them reusable for agents, workflows, and automation systems.**

---

## A Lighter Search Stack

Most "all-web search" systems eventually become the same heavy engineering story:

- custom crawlers
- browser automation
- login and session handling
- anti-bot recovery
- provider-specific maintenance
- endless keyword tuning
- manual result cleanup

AI Search Hub takes a different path:

> **Reuse the platform-native search power already optimized by AI vendors.**

Platforms already invested in search quality, ranking, access, and interaction design.
AI Search Hub does not rebuild that stack. It orchestrates it.

---

## Traditional Workflow vs AI Search Hub

| Traditional workflow | AI Search Hub |
|---|---|
| Build crawlers yourself | Reuse platform-native search |
| One automation flow per provider | One query, multi-provider dispatch |
| Constant anti-bot handling | Lean on existing platform entry points |
| Endless keyword tuning | Reuse provider-optimized search logic |
| Manual result stitching | Unified output for agents and workflows |

---

## How it works

### 1. Receive one query

The user or agent asks one question only once. No repeated rewriting per provider.

### 2. Dispatch across providers

The same query is sent to multiple providers so each one can search the ecosystem it knows best.

### 3. Reuse platform-native strengths

Gemini is strong at Google and web search.
Grok is strong at X / Twitter and real-time discovery.
Doubao, Yuanbao, Qwen, and Wenxin are better aligned with different layers of the Chinese internet.

### 4. Collect and normalize results

Outputs from multiple providers are pulled back into a single channel, ready for normalization, fusion, and workflow consumption.

### 5. Return to your workflow

The final output is meant for agents, research pipelines, monitoring systems, and automation workflows, not just browser tabs.

---

## Provider Matrix

| Provider | Search Strength | Typical Coverage | Role |
|---|---|---|---|
| Gemini | Google / web search | Google, public web, knowledge content | Core |
| Grok | X / Twitter real-time search | Live discussion, trending topics, real-time signals | Core |
| Doubao | Chinese content understanding | Douyin, Chinese content ecosystem, hot topics | Core |
| Yuanbao | Chinese source supplement | WeChat Official Accounts, Chinese web content | Core |
| Wenxin Yiyan | Chinese web expansion | Chinese search, public web pages | Extended |
| Qwen / Tongyi | Chinese web expansion | Chinese search, public web pages | Extended |
| More | Extensible | More social/search surfaces | Future |

---

## Search Worlds It Can Reach

By reusing platform-native search capabilities, AI Search Hub can indirectly cover many major sources, such as:

- Google
- Weibo
- Douyin
- X / Twitter
- Reddit
- WeChat Official Accounts
- public web pages
- overseas social media
- Chinese internet ecosystems

The point is not to crawl every platform yourself.
The point is:

> **Let platforms search the worlds they already know best.**

---

## Example Configuration

```yaml
hub:
  parallel: true
  timeout_ms: 30000
  normalize_output: true

providers:
  gemini:
    enabled: true
    role: "google-web-search"

  grok:
    enabled: true
    role: "x-twitter-search"

  doubao:
    enabled: true
    role: "douyin-chinese-content"

  yuanbao:
    enabled: true
    role: "wechat-official-accounts"

  wenxin:
    enabled: false
    role: "chinese-web-search"

  qwen:
    enabled: false
    role: "general-chinese-search"
```

This does not mean the project must already use a YAML config file.
It is a conceptual example that shows:

- the hub layer handles orchestration
- the provider layer controls which platforms are enabled
- each provider carries a distinct search role

---

## Example Request

```json
{
  "query": "What are users saying about AI coding products across different platforms recently?",
  "providers": ["gemini", "grok", "doubao", "yuanbao"],
  "mode": "parallel"
}
```

## Example Output

```json
{
  "query": "What are users saying about AI coding products across different platforms recently?",
  "results": [
    {
      "provider": "gemini",
      "summary": "Google / web search result summary"
    },
    {
      "provider": "grok",
      "summary": "X / Twitter search result summary"
    },
    {
      "provider": "doubao",
      "summary": "Douyin / Chinese content summary"
    },
    {
      "provider": "yuanbao",
      "summary": "WeChat Official Accounts / Chinese web summary"
    }
  ]
}
```

---

## FAQ

**Is this a crawler framework?**
No. It is a search capability aggregation skill.

**Do I still need browser automation for every provider?**
Reducing that burden is exactly what AI Search Hub is trying to do.

**Do I still need to tune keywords constantly?**
Far less than traditional workflows, because AI Search Hub tries to reuse search systems already optimized by the platforms.

**Why is this useful for agents?**
Because agents need search as a reusable capability, not a pile of brittle scripts.

**Can I add more providers?**
Yes. The design is intentionally lightweight and extensible.

---

## Roadmap

| Stage | Item | Status |
|---|---|---|
| Phase 1 | Browser-based provider runners | Done |
| Phase 2 | Login recovery flow | Done |
| Phase 3 | Isolated browser-profile seeding | Done |
| Phase 4 | Multi-provider search aggregation | In Progress |
| Phase 5 | Unified result output | In Progress |
| Phase 6 | More provider integrations | Planned |
| Phase 7 | Result ranking / fusion | Planned |
| Phase 8 | Evidence / source view | Planned |

---

## Contributing

Issues and PRs are welcome.

If you also believe the future of search should not be **one more crawler stack**,
but **one smarter way to use all existing AI search surfaces together**, feel free to contribute.

---

## Disclaimer

AI Search Hub is designed to reuse platform-native capabilities in a practical and sustainable way.
Please comply with the terms of service, policies, and applicable laws of the platforms you integrate with.

This project focuses on aggregation and orchestration, not on bypassing platform rules.

---

## Final Line

**One Query. All Search.**
Stop rebuilding search from scratch.
Plug into the search power platforms already optimized.
