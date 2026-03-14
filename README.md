<div align="center">

# AI Search Hub

### 一次提问，全域搜索。

[English](README.en.md)

[![Repo](https://img.shields.io/badge/Repo-GitHub-181717?style=flat-square&logo=github)](https://github.com/minsight-ai-info/AI-Search-Hub)
[![Type](https://img.shields.io/badge/type-open--source%20skill-black?style=flat-square)](https://github.com/minsight-ai-info/AI-Search-Hub)
[![Status](https://img.shields.io/badge/status-active-success?style=flat-square)](https://github.com/minsight-ai-info/AI-Search-Hub)
[![Mode](https://img.shields.io/badge/mode-browser--driven-blue?style=flat-square)](https://github.com/minsight-ai-info/AI-Search-Hub)

**一个聚合多平台 AI 原生搜索能力的开源 Skill。**
**一次提问，并行调用多个 AI 平台的搜索入口。**

</div>

---

## 把多平台 AI 搜索接成一个入口

AI Search Hub 是一个开源 Skill，用来把分散在不同 AI 平台里的搜索能力，整理成一个可复用的搜索中枢。

它不想让你继续维护：

- 一堆脆弱爬虫
- 每个平台各自一套浏览器自动化
- 反复登录、验证码、限流、风控处理
- 无休止的关键词试错和提示词微调
- 最后还要人工收拾碎片结果

它想做的事情很直接：

> **把各大平台已经优化好的原生搜索入口统一接进来，让 Agent、工作流和自动化系统可以直接复用。**

---

## 比传统搜索工程更轻

很多“全网搜索”项目最后都会越来越重：

- 要写爬虫
- 要跑浏览器
- 要扛平台变更
- 要处理登录态和风控
- 要维护每个平台的独立适配
- 要自己清洗和整合结果

AI Search Hub 选择另一条路：

> **不重造搜索系统，直接复用平台已经打磨好的搜索能力。**

平台已经把搜索质量、排序逻辑、入口接入和交互体验打磨得很强。
AI Search Hub 不重复造轮子，它负责把这些能力编排起来。

---

## 传统方案 vs AI Search Hub

| 传统方案 | AI Search Hub |
|---|---|
| 自己写爬虫 | 直接复用平台原生搜索 |
| 一个平台一套自动化 | 一次提问，多平台分发 |
| 反复处理风控与验证码 | 尽量沿用平台已有入口 |
| 自己调关键词和检索策略 | 借助平台已优化好的搜索逻辑 |
| 结果分散、要手工拼接 | 统一输出给 Agent / Workflow |

---

## 工作方式

### 1. 接收一次提问

用户或 Agent 只输入一次问题，不需要为每个平台重复组织查询。

### 2. 分发到多个平台

同一个问题会被发送到多个 Provider，让它们各自去搜索自己最擅长的数据世界。

### 3. 复用平台原生能力

Gemini 擅长 Google / 网页搜索。
Grok 擅长 X / Twitter 实时搜索。
豆包、元宝、通义千问、文心一言更适合不同层次的中文互联网内容。

### 4. 收集并整理结果

多平台返回的内容会被拉回同一个出口，后续可以统一做标准化、融合和工作流消费。

### 5. 返回给 Agent 或系统

最终结果不是停留在浏览器页面，而是成为 Agent、研究系统、监控流程或自动化链路里的可复用输入。

---

## Provider 一览

| Provider | 优势方向 | 典型覆盖 | 当前角色 |
|---|---|---|---|
| Gemini | Google / 网页搜索 | Google、公开网页、知识内容 | 核心 |
| Grok | X / Twitter 实时搜索 | 热点讨论、实时动态、社交舆情 | 核心 |
| 豆包 | 中文内容理解 | 抖音、中文内容生态、热门话题 | 核心 |
| 元宝 | 中文生态补充 | 微信公众号、中文网页内容 | 核心 |
| 文心一言 | 中文搜索扩展 | 中文搜索、公开网页 | 扩展 |
| 通义千问 | 中文搜索扩展 | 中文搜索、公开网页 | 扩展 |
| 更多平台 | 持续扩展 | 更多社交媒体 / 搜索入口 | Future |

---

## 覆盖的内容世界

通过不同平台已经打磨好的搜索能力，AI Search Hub 可以间接覆盖多种主流来源，例如：

- Google
- 微博
- 抖音
- X / Twitter
- Reddit
- 微信公众号
- 各类公开网页内容
- 海外社交媒体
- 中文互联网内容生态

重点不是你自己去一个个平台写爬虫，
而是：

> **借助平台已经连接好的数据世界，直接完成多平台搜索。**

---

## 配置示例

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

这个配置不代表项目里现在一定已经有这样一个 YAML 文件。
它只是一个概念示例，用来表达：

- Hub 层负责统一调度
- Provider 层负责接入不同平台
- 不同平台承担不同搜索角色

---

## 请求示例

```json
{
  "query": "最近 AI 编程产品在不同平台的用户反馈",
  "providers": ["gemini", "grok", "doubao", "yuanbao"],
  "mode": "parallel"
}
```

## 返回示例

```json
{
  "query": "最近 AI 编程产品在不同平台的用户反馈",
  "results": [
    {
      "provider": "gemini",
      "summary": "Google / 网页搜索结果摘要"
    },
    {
      "provider": "grok",
      "summary": "X / Twitter 搜索结果摘要"
    },
    {
      "provider": "doubao",
      "summary": "抖音 / 中文内容摘要"
    },
    {
      "provider": "yuanbao",
      "summary": "微信公众号 / 中文网页内容摘要"
    }
  ]
}
```

---

## FAQ

**这是一个爬虫框架吗？**
不是。它是一个搜索能力聚合 Skill。

**是不是还得自己维护每个平台的浏览器自动化？**
这正是 AI Search Hub 想减少的负担。

**是不是还得一直调关键词？**
相比传统搜索流程会少很多，因为它尽量复用平台已经优化好的搜索能力。

**为什么这对 Agent 很重要？**
因为 Agent 需要的是可调用的搜索能力，而不是一堆脆弱脚本。

**能不能继续加新的平台？**
可以。这个设计本来就是轻量、可扩展的。

---

## Roadmap

| 阶段 | 内容 | 状态 |
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

欢迎提交 Issues 和 PR。

如果你也认同未来的搜索不应该是 **再写一个更重的爬虫系统**，
而应该是 **更聪明地把现有 AI 搜索入口统一起来**，欢迎一起参与。

---

## Disclaimer

AI Search Hub 的目标是以务实、可持续的方式复用平台原生能力。
请遵守你接入平台对应的服务条款、平台政策和适用法律。

这个项目关注的是聚合与编排，不是绕过平台规则。

---

## Final Line

**一次提问，全域搜索。**
不用从零重建搜索。
直接接入平台已经打磨好的搜索能力。
