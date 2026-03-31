---
name: ai-search-hub-routing
description: Machine-readable routing strategy for AI Search Hub. An AI agent must follow this document to decide which site(s) to query based on the user's question. This is the decision layer that sits above run_web_chat.py.
---

# AI Search Hub — Routing Strategy

This document tells you **which site(s) to call** for a given user question. Read this before invoking `scripts/run_web_chat.py`.

---

## Core Principle

Do not send every question to every platform. Analyze the question first, then route to the platform(s) whose underlying data world is most likely to contain the best answer.

---

## Step 1 — Classify the Question

Read the user's question and determine two things:

### 1.1 Geographic / Language Orientation

| Signal | Classification |
|---|---|
| Question is in English, or asks about global / Western topics | **International** |
| Question is in Chinese, or asks about Chinese market / Chinese internet topics | **Domestic (China)** |
| Question mixes both, or the topic spans both worlds | **Both** |

### 1.2 Data Source Affinity

Identify which content ecosystem is most likely to have the answer:

| Signal in the Question | Likely Best Source | Parent Company | Recommended Site |
|---|---|---|---|
| **International / Global** |
| Mentions Twitter / X, Elon Musk, trending tweets, real-time social discussion, Western public figures' social posts | X / Twitter ecosystem | xAI | `grok` |
| Mentions Google, global web pages, English knowledge sites, Wikipedia, Stack Overflow, international tech | Google ecosystem | Google | `gemini` |
| **Domestic (China) — By Company Ecosystem** |
| Mentions 微信公众号, WeChat articles, 腾讯, QQ, 微信生态, or the question is about content typically published on WeChat public accounts (e.g. Chinese industry analysis articles, Chinese media reports) | Tencent / WeChat ecosystem | 腾讯 Tencent | `yuanbao` |
| Mentions 抖音, TikTok (Chinese), 字节跳动, ByteDance, 今日头条, 火山引擎, or the question is about Chinese trending topics, short video trends, Chinese pop culture, Chinese consumer trends | ByteDance / Douyin ecosystem | 字节跳动 ByteDance | `doubao` |
| Mentions 美团, 大众点评, 外卖, 本地生活, 餐饮, 酒店, 旅游攻略, or the question is about local services, lifestyle, food, travel, merchant reviews | Meituan / Dianping ecosystem | 美团 Meituan | `longcat` |
| Mentions 淘宝, 天猫, 阿里巴巴, 1688, 钉钉, or the question is about e-commerce, B2B, enterprise services, cloud computing | Alibaba ecosystem | 阿里巴巴 Alibaba | `qwen` |
| Explicitly asks for MiniMax / MiniMax Agent / 海螺 / MiniMax 平台 | MiniMax ecosystem | MiniMax | `minimaxi` |
| Explicitly asks for Kimi / moonshot / 月之暗面, or the question requires long-context reading, document analysis, research report summarization | Moonshot AI ecosystem | 月之暗面 Moonshot AI | `kimi` |
| Mentions 微博, Weibo hot search, Chinese celebrity news, Chinese public opinion | Weibo / Sina ecosystem | 新浪 Sina | `doubao` or `longcat` |
| **Domestic — By Content Type** |
| Chinese lifestyle, local services, food recommendations, travel guides, merchant information | Meituan knowledge base | 美团 Meituan | `longcat` |
| General Chinese knowledge, industry reports, structured summaries, Chinese academic or professional content | Aggregated Chinese knowledge | Multiple | `longcat` |
| Broad Chinese web search, general Chinese internet content, no specific ecosystem affinity | Chinese web | Multiple | `qwen` |
| Asks about a specific URL or web page content | Depends on the URL's language and origin | — | See URL routing below |

---

## Step 2 — Route to Site(s)

### International Questions → `grok` and/or `gemini`

```
User: "What are people saying about the new OpenAI model on Twitter?"
→ grok

User: "Find me recent research papers on transformer architectures"
→ gemini

User: "Summarize Elon Musk's recent posts on X"
→ grok

User: "What is the latest news about Apple Vision Pro?"
→ gemini + grok (gemini for web/news, grok for social reactions)
```

### Domestic (China) Questions → Route by Ecosystem

```
User: "帮我搜一下微信公众号上关于新能源汽车的深度分析文章"
→ yuanbao (WeChat / Tencent ecosystem)

User: "最近抖音上什么话题最火？"
→ doubao (Douyin / ByteDance ecosystem)

User: "帮我看看微信公众号'虎嗅'最近发了什么"
→ yuanbao (explicitly WeChat public account)

User: "字节跳动最近有什么新产品动态？"
→ doubao (ByteDance ecosystem)

User: "帮我整理一下中国半导体行业最新的研究报告"
→ longcat (Chinese knowledge / industry reports)

User: "杭州有什么好吃的？"
→ longcat (美团本地生活) or doubao (抖音热门内容)

User: "帮我找一下北京靠谱的日料店"
→ longcat (大众点评/美团商户数据)

User: "微博上大家怎么看这次的政策变化？"
→ doubao (抖音/头条舆论) or longcat (综合观点)
```

### Mixed / Broad Questions → Multiple Sites

```
User: "帮我对比一下国内外对 AI Agent 的看法"
→ gemini + grok (international) + longcat or qwen (domestic)

User: "Search for what people are saying about this topic globally and in China"
→ grok + gemini + doubao or qwen
```

---

## Step 3 — Ecosystem Affinity Decision Tree

When the question does not explicitly mention a platform, use this decision tree:

```
Is the question about international / English content?
├── YES
│   ├── Is it about real-time social discussion, trending opinions, or specific people's posts?
│   │   ├── YES → grok
│   │   └── NO → gemini
│   └── Unsure → gemini + grok
│
└── NO (Chinese / domestic content)
    ├── Does it involve 微信, 公众号, WeChat, 腾讯, or content typically found in WeChat articles?
    │   └── YES → yuanbao (腾讯系)
    ├── Does it involve 抖音, 字节, ByteDance, 头条, short video trends, or Chinese pop culture / consumer trends?
    │   └── YES → doubao (字节系)
    ├── Does it involve 美团, 大众点评, 外卖, 本地生活, 餐饮, 酒店, 旅游攻略, merchant reviews?
    │   └── YES → longcat (美团系)
    ├── Does it involve 淘宝, 天猫, 阿里巴巴, 1688, 钉钉, e-commerce, or enterprise services?
    │   └── YES → qwen (阿里系)
    ├── Does it involve 微博, Chinese celebrity, Chinese public opinion?
    │   └── YES → doubao (字节系，含头条) or longcat (综合)
    ├── Does it need structured knowledge, industry reports, or professional Chinese content?
    │   └── YES → longcat (美团知识库)
    ├── Does the question explicitly mention Kimi / moonshot / 月之暗面, or require long-context analysis, document reading?
    │   └── YES → kimi (月之暗面)
    └── General Chinese web question, no specific ecosystem?
        └── qwen (阿里系，通用搜索)
```

---

## Step 4 — URL-Based Routing

If the user provides a URL and asks the AI platform to read, extract, or summarize it:

| URL Pattern | Recommended Site | Parent Company |
|---|---|---|
| **Tencent 腾讯系** |
| `mp.weixin.qq.com/*` | `yuanbao` | 腾讯 |
| `weixin.qq.com/*` | `yuanbao` | 腾讯 |
| `qq.com/*` | `yuanbao` | 腾讯 |
| **ByteDance 字节系** |
| `toutiao.com/*` | `doubao` | 字节跳动 |
| `douyin.com/*` | `doubao` | 字节跳动 |
| `ixigua.com/*` | `doubao` | 字节跳动 |
| `feishu.cn/*`, `larksuite.com/*` | `doubao` | 字节跳动 |
| **Meituan 美团系** |
| `dianping.com/*` | `longcat` | 美团 |
| `meituan.com/*` | `longcat` | 美团 |
| **Alibaba 阿里系** |
| `taobao.com/*`, `tmall.com/*` | `qwen` | 阿里巴巴 |
| `1688.com/*` | `qwen` | 阿里巴巴 |
| `aliyun.com/*` | `qwen` | 阿里巴巴 |
| `dingtalk.com/*` | `qwen` | 阿里巴巴 |
| **International** |
| `twitter.com/*`, `x.com/*` | `grok` | xAI |
| `*.google.com/*` | `gemini` | Google |
| `youtube.com/*` | `gemini` | Google |
| **Other Chinese** |
| `weibo.com/*`, `weibo.cn/*` | `doubao` or `longcat` | 新浪 |
| `zhihu.com/*` | `qwen` or `longcat` | 知乎 |
| `baidu.com/*` | `qwen` or `longcat` | 百度 |
| `bilibili.com/*` | `doubao` or `qwen` | B站 |
| `xiaohongshu.com/*` | `doubao` | 小红书 |
| `agent.minimaxi.com/*` | `minimaxi` | MiniMax |
| Unknown or mixed | `gemini` (broadest web) | — |

---

## Step 5 — Multi-Site Execution

When routing to multiple sites, run them as separate invocations:

```bash
# Example: international + domestic comparison
python scripts/run_web_chat.py --site grok   --prompt "..." --output out/grok_result.txt
python scripts/run_web_chat.py --site gemini --prompt "..." --output out/gemini_result.txt
python scripts/run_web_chat.py --site doubao --prompt "..." --output out/doubao_result.txt
```

After all invocations complete, read the output files and synthesize the results for the user.

If the user's question is time-sensitive or they are waiting, prefer running fewer but more targeted sites over running all sites.

---

## Step 6 — Fallback Rules

1. **If unsure about domestic ecosystem affinity**, default to `qwen` — it has the broadest Chinese web coverage.
2. **If unsure about international routing**, default to `gemini` — it has the broadest global web coverage.
3. **If a site fails or returns no useful answer**, retry with the next most relevant site from the same category.
4. **If the user explicitly requests a specific site**, always honor that request regardless of routing logic.

---

## Quick Reference Table

| User Intent | Primary Site | Secondary Site | Parent Company |
|---|---|---|---|
| **International** |
| Twitter / X social search | `grok` | — | xAI |
| Google / global web search | `gemini` | `grok` | Google |
| **Domestic — By Company** |
| 微信公众号 / WeChat / 腾讯系内容 | `yuanbao` | `longcat` | 腾讯 |
| 抖音 / 头条 / 字节系内容 | `doubao` | `qwen` | 字节跳动 |
| 美团 / 大众点评 / 本地生活 | `longcat` | `doubao` | 美团 |
| 淘宝 / 天猫 / 阿里系内容 | `qwen` | `longcat` | 阿里巴巴 |
| 明确要求 MiniMax 平台 | `minimaxi` | `qwen` | MiniMax |
| 明确要求 Kimi / 长文档分析 / 研究报告总结 | `kimi` | `longcat` | 月之暗面 |
| 微博 / 新浪系内容 | `doubao` | `longcat` | 新浪 |
| **Domestic — By Content Type** |
| 本地生活服务 / 餐饮 / 酒店 / 旅游 | `longcat` | `doubao` | 美团 |
| 短视频 / 热点 / 娱乐 | `doubao` | `longcat` | 字节跳动 |
| 电商 / 企业服务 | `qwen` | `doubao` | 阿里巴巴 |
| 行业报告 / 专业知识 | `longcat` | `qwen` | 美团 / 阿里 |
| 通用中文搜索 | `qwen` | `longcat` | 阿里巴巴 / 美团 |
| **URL / Cross-border** |
| URL extraction (Chinese) | Match by URL domain | `qwen` as fallback | — |
| URL extraction (English) | `gemini` | `grok` | Google / xAI |
| Cross-border comparison | `gemini` + `grok` | `doubao` or `qwen` | — |
