<div align="center">

# AI Search Hub

### One Query. All Search.

[中文](README.md)

[![Repo](https://img.shields.io/badge/Repo-GitHub-181717?style=flat-square&logo=github)](https://github.com/minsight-ai-info/AI-Search-Hub)
[![Type](https://img.shields.io/badge/type-open--source%20skill-black?style=flat-square)](https://github.com/minsight-ai-info/AI-Search-Hub)
[![Status](https://img.shields.io/badge/status-active-success?style=flat-square)](https://github.com/minsight-ai-info/AI-Search-Hub)
[![Mode](https://img.shields.io/badge/mode-browser--driven-blue?style=flat-square)](https://github.com/minsight-ai-info/AI-Search-Hub)

<p>
  <img src="https://img.shields.io/badge/Claude_Code-black?style=flat-square&logo=anthropic&logoColor=white" alt="Claude Code">
  <img src="https://img.shields.io/badge/OpenAI_Codex_CLI-412991?style=flat-square&logo=openai&logoColor=white" alt="OpenAI Codex CLI">
  <img src="https://img.shields.io/badge/Cursor-000?style=flat-square&logo=cursor&logoColor=white" alt="Cursor">
  <img src="https://img.shields.io/badge/Kiro-232F3E?style=flat-square&logo=amazon&logoColor=white" alt="Kiro">
  <img src="https://img.shields.io/badge/OpenClaw-FF6B35?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJMNCA3djEwbDggNSA4LTV2LTEweiIgZmlsbD0id2hpdGUiLz48L3N2Zz4=&logoColor=white" alt="OpenClaw">
  <img src="https://img.shields.io/badge/Antigravity-4285F4?style=flat-square&logo=google&logoColor=white" alt="Google Antigravity">
  <img src="https://img.shields.io/badge/OpenCode-00D4AA?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTkuNCA1LjJMMyAxMmw2LjQgNi44TTIxIDEybC02LjQtNi44TTE0LjYgMTguOCIgc3Ryb2tlPSJ3aGl0ZSIgZmlsbD0ibm9uZSIgc3Ryb2tlLXdpZHRoPSIyIi8+PC9zdmc+&logoColor=white" alt="OpenCode">
  <img src="https://img.shields.io/badge/🌐_Multi--Language-blue?style=flat-square" alt="Multi-Language">
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="MIT License">
</p>

**An open-source skill for aggregating platform-native AI search.**
**Bring tech updates, public sentiment, and daily planning into your OpenClaw with stronger search power.**

</div>

---

## Plug Big-Tech Native Search into Your OpenClaw

AI Search Hub is an open-source skill that turns fragmented AI search surfaces into one reusable search hub.

It lets you directly leverage search surfaces and search frameworks already refined by major AI platforms, then route tech updates, public sentiment, and daily planning into your own agents and workflows.

It is not trying to make you maintain:

- fragile crawler stacks
- separate browser automation flows for every provider
- endless login, captcha, rate-limit, and anti-bot recovery
- constant keyword and prompt tuning
- manual cleanup of scattered results

Its job is simple:

> **Turn multiple AI search surfaces into one entrypoint, and directly leverage search systems already refined by major platforms.**

<table width="100%">
  <tr>
    <td width="50%" align="center">
      <img src="docs/images/grok-result.png" alt="Grok run result" width="100%">
      <br>
      <sub>Real Grok run result</sub>
    </td>
    <td width="50%" align="center">
      <img src="docs/images/doubao-result.png" alt="Doubao run result" width="100%">
      <br>
      <sub>Real Doubao run result</sub>
    </td>
  </tr>
</table>

---

## Install

AI Search Hub is not a traditional SDK. It is a skill.

Give this repository to any skill-capable agent or tool such as `OpenClaw`, `Claude Code`, `Codex`, or `Cursor`, and let it install or mount the skill directly.

---

## Traditional Workflow vs AI Search Hub

<table width="100%">
  <thead>
    <tr>
      <th align="left" width="50%">Traditional workflow</th>
      <th align="left" width="50%">AI Search Hub</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>🔧 <strong>Build crawlers yourself</strong><br><sub>You own scraping, parsing, and long-term maintenance</sub></td>
      <td>⚡ <strong>Reuse platform-native search</strong><br><sub>Plug directly into mature search surfaces</sub></td>
    </tr>
    <tr>
      <td>🧩 <strong>One automation flow per provider</strong><br><sub>Every new source adds one more integration to maintain</sub></td>
      <td>🚀 <strong>One query, multi-provider dispatch</strong><br><sub>Use one entrypoint for multiple search providers</sub></td>
    </tr>
    <tr>
      <td>🛡️ <strong>Constant anti-bot handling</strong><br><sub>Login, rate limits, and UI changes drain engineering time</sub></td>
      <td>🎯 <strong>Lean on existing platform entry points</strong><br><sub>Reduce repeated recovery work and focus on orchestration</sub></td>
    </tr>
    <tr>
      <td>🔍 <strong>Endless keyword tuning</strong><br><sub>Usable coverage often needs constant search tweaking</sub></td>
      <td>🧠 <strong>Reuse provider-optimized search logic</strong><br><sub>Reuse ranking, retrieval, and interaction patterns</sub></td>
    </tr>
    <tr>
      <td>🧱 <strong>Manual result stitching</strong><br><sub>You still need to unify scattered outputs afterward</sub></td>
      <td>📦 <strong>Unified output for agents and workflows</strong><br><sub>Pull results back into one reusable output channel</sub></td>
    </tr>
  </tbody>
</table>

---

## Supported Platforms

These platforms are not side notes. They are the search surfaces AI Search Hub orchestrates first.

<table width="100%">
  <thead>
    <tr>
      <th align="left" width="24%">Provider</th>
      <th align="left" width="30%">Search Strength</th>
      <th align="left" width="30%">Typical Coverage</th>
      <th align="left" width="16%">Role</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Gemini</strong><br><sub>Google-first discovery</sub></td>
      <td><code>Google search</code> <code>web discovery</code> <code>knowledge lookup</code></td>
      <td><code>Google</code> <code>public web</code> <code>knowledge sites</code></td>
      <td><img src="https://img.shields.io/badge/Core-16a34a?style=flat-square" alt="Core"></td>
    </tr>
    <tr>
      <td><strong>Grok</strong><br><sub>Real-time social search</sub></td>
      <td><code>X / Twitter</code> <code>live signals</code> <code>trend discovery</code></td>
      <td><code>real-time posts</code> <code>social chatter</code> <code>trending topics</code></td>
      <td><img src="https://img.shields.io/badge/Core-16a34a?style=flat-square" alt="Core"></td>
    </tr>
    <tr>
      <td><strong>Doubao</strong><br><sub>Chinese trend sensing</sub></td>
      <td><code>Chinese understanding</code> <code>hot topics</code> <code>content summarization</code></td>
      <td><code>Douyin</code> <code>Chinese content</code> <code>trending discussions</code></td>
      <td><img src="https://img.shields.io/badge/Core-16a34a?style=flat-square" alt="Core"></td>
    </tr>
    <tr>
      <td><strong>Yuanbao</strong><br><sub>Chinese source supplement</sub></td>
      <td><code>Chinese supplement</code> <code>official account lookup</code> <code>source cross-checking</code></td>
      <td><code>WeChat Official Accounts</code> <code>Chinese web</code> <code>public content</code></td>
      <td><img src="https://img.shields.io/badge/Core-16a34a?style=flat-square" alt="Core"></td>
    </tr>
    <tr>
      <td><strong>Wenxin Yiyan</strong><br><sub>Chinese web expansion</sub></td>
      <td><code>Chinese search</code> <code>public web</code> <code>Baidu ecosystem</code></td>
      <td><code>Chinese pages</code> <code>search results</code> <code>public sites</code></td>
      <td><img src="https://img.shields.io/badge/Extended-2563eb?style=flat-square" alt="Extended"></td>
    </tr>
    <tr>
      <td><strong>Qwen / Tongyi</strong><br><sub>Chinese web expansion</sub></td>
      <td><code>Chinese search</code> <code>web Q&amp;A</code> <code>public content</code></td>
      <td><code>Chinese web</code> <code>search surfaces</code> <code>open information</code></td>
      <td><img src="https://img.shields.io/badge/Extended-2563eb?style=flat-square" alt="Extended"></td>
    </tr>
    <tr>
      <td><strong>More</strong><br><sub>Extensible surface</sub></td>
      <td><code>continuous expansion</code> <code>new surfaces</code> <code>new providers</code></td>
      <td><code>social media</code> <code>search platforms</code> <code>vertical sources</code></td>
      <td><img src="https://img.shields.io/badge/Future-6b7280?style=flat-square" alt="Future"></td>
    </tr>
  </tbody>
</table>

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

## Search Worlds It Can Reach

By reusing platform-native search capabilities, AI Search Hub can indirectly reach these core search worlds:

<table width="100%">
  <tr>
    <td width="33%">
      <strong>🌐 Global Web</strong><br>
      <sub>Google, public websites, knowledge pages</sub>
    </td>
    <td width="33%">
      <strong>⚡ Real-Time Social</strong><br>
      <sub>X / Twitter, Reddit, live discussions</sub>
    </td>
    <td width="33%">
      <strong>🔥 Chinese Trends</strong><br>
      <sub>Weibo, Douyin, Chinese hot topics</sub>
    </td>
  </tr>
  <tr>
    <td width="33%">
      <strong>📰 WeChat Ecosystem</strong><br>
      <sub>WeChat Official Accounts, source supplements</sub>
    </td>
    <td width="33%">
      <strong>🧭 Overseas Signals</strong><br>
      <sub>overseas social media, public trend signals</sub>
    </td>
    <td width="33%">
      <strong>🏮 Chinese Internet</strong><br>
      <sub>Chinese web pages, vertical sites, content ecosystems</sub>
    </td>
  </tr>
</table>

<details>
  <summary>Original list backup</summary>

  <ul>
    <li>Google</li>
    <li>Weibo</li>
    <li>Douyin</li>
    <li>X / Twitter</li>
    <li>Reddit</li>
    <li>WeChat Official Accounts</li>
    <li>public web pages</li>
    <li>overseas social media</li>
    <li>Chinese internet ecosystems</li>
  </ul>
</details>

The point is not to crawl every platform yourself.
The point is:

> **Let platforms search the worlds they already know best.**

---

## Advanced Usage

### Example Configuration

```yaml
# agents/openai.yaml
interface:
  display_name: "AI Search Hub"
  short_description: "Run AI Search Hub browser scripts across supported AI platforms"
  default_prompt: "Use $ai-search-hub to run one of the repository chat sites with automatic Chrome debug startup and login waiting."

policy:
  allow_implicit_invocation: true
```

This is not a conceptual interface. It is the actual agent configuration snippet currently used in the repository.
The runtime entrypoint is still `scripts/run_web_chat.py`.

---

### Example Request

```bash
python3 scripts/run_web_chat.py \
  --site doubao \
  --prompt "Help me plan a Xinjiang travel route" \
  --output out/doubao_xinjiang_route.txt

python3 scripts/run_web_chat.py \
  --site grok \
  --prompt "Summarize Elon Musk's posts on X from the last 14 days, list them by date in descending order, and include links" \
  --output out/grok_musk_recent.txt
```

### Example Output

Doubao output excerpt:

```text
1. Northern Xinjiang classic loop, 7-10 days
Urumqi -> Heavenly Lake -> Keketuohai -> Burqin -> Five-Colored Beach -> Kanas -> Hemu -> Urho Ghost City -> Sayram Lake

2. Ili grassland and flower route, 6-8 days
Urumqi -> Sayram Lake -> Guozigou -> Huocheng lavender -> Tekes -> Kalajun -> Xiata -> Nalati -> Duku Highway
```

Grok output excerpt:

```text
2026-03-15: Starlink now available in Kuwait
2026-03-15: Couldn't script it better
2026-03-15: SpaceX 24th anniversary related post

Overall, the recent pattern on X is mostly three buckets: xAI/Grok and X platform promotion, Starlink/SpaceX, and frequent political commentary.
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

## Contributing

Issues and PRs are welcome.

If you also believe the future of search should not be **one more crawler stack**,
but **one smarter way to use all existing AI search surfaces together**, feel free to contribute.
