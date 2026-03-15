<div align="center">

# AI Search Hub

### 一次提问，全域搜索。

[English](README.en.md)

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

## 传统方案 vs AI Search Hub

<table>
  <thead>
    <tr>
      <th align="left" width="42%">传统方案</th>
      <th align="left" width="58%">AI Search Hub</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>🔧 <strong>自己写爬虫</strong><br><sub>抓取、解析、维护都要自己扛</sub></td>
      <td>⚡ <strong>直接复用平台原生搜索</strong><br><sub>少造轮子，直接接入平台已经打磨好的入口</sub></td>
    </tr>
    <tr>
      <td>🧩 <strong>一个平台一套自动化</strong><br><sub>接一个平台就多一份维护成本</sub></td>
      <td>🚀 <strong>一次提问，多平台分发</strong><br><sub>统一入口，把不同平台编排到同一条链路里</sub></td>
    </tr>
    <tr>
      <td>🛡️ <strong>反复处理风控与验证码</strong><br><sub>登录态、限流和页面变化持续消耗精力</sub></td>
      <td>🎯 <strong>尽量沿用平台已有入口</strong><br><sub>减少重复对抗，把精力留给结果聚合</sub></td>
    </tr>
    <tr>
      <td>🔍 <strong>自己调关键词和检索策略</strong><br><sub>不断试错才能逼近可用结果</sub></td>
      <td>🧠 <strong>借助平台已优化好的搜索逻辑</strong><br><sub>复用平台已有的排序、理解和搜索体验</sub></td>
    </tr>
    <tr>
      <td>🧱 <strong>结果分散、要手工拼接</strong><br><sub>最后还得自己整合成可消费输出</sub></td>
      <td>📦 <strong>统一输出给 Agent / Workflow</strong><br><sub>从多平台结果回收到一个可复用出口</sub></td>
    </tr>
  </tbody>
</table>

---

## 支持平台

这些平台不是附属补充，而是 AI Search Hub 当前编排的核心搜索入口。

<table>
  <thead>
    <tr>
      <th align="left">Provider</th>
      <th align="left">擅长方向</th>
      <th align="left">典型覆盖</th>
      <th align="left">当前角色</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Gemini</strong><br><sub>Google-first discovery</sub></td>
      <td><code>Google 搜索</code> <code>网页发现</code> <code>知识内容</code></td>
      <td><code>Google</code> <code>公开网页</code> <code>知识站点</code></td>
      <td><img src="https://img.shields.io/badge/Core-16a34a?style=flat-square" alt="Core"></td>
    </tr>
    <tr>
      <td><strong>Grok</strong><br><sub>Real-time social search</sub></td>
      <td><code>X / Twitter</code> <code>实时动态</code> <code>热点讨论</code></td>
      <td><code>实时舆情</code> <code>趋势话题</code> <code>社交信号</code></td>
      <td><img src="https://img.shields.io/badge/Core-16a34a?style=flat-square" alt="Core"></td>
    </tr>
    <tr>
      <td><strong>豆包</strong><br><sub>Chinese trend sensing</sub></td>
      <td><code>中文理解</code> <code>热点话题</code> <code>内容归纳</code></td>
      <td><code>抖音</code> <code>中文内容生态</code> <code>热门内容</code></td>
      <td><img src="https://img.shields.io/badge/Core-16a34a?style=flat-square" alt="Core"></td>
    </tr>
    <tr>
      <td><strong>元宝</strong><br><sub>Chinese source supplement</sub></td>
      <td><code>中文补充检索</code> <code>公众号信源</code> <code>内容交叉验证</code></td>
      <td><code>微信公众号</code> <code>中文网页</code> <code>公开内容</code></td>
      <td><img src="https://img.shields.io/badge/Core-16a34a?style=flat-square" alt="Core"></td>
    </tr>
    <tr>
      <td><strong>文心一言</strong><br><sub>Chinese web expansion</sub></td>
      <td><code>中文搜索</code> <code>公开网页</code> <code>百度生态</code></td>
      <td><code>中文网页</code> <code>搜索结果</code> <code>公开站点</code></td>
      <td><img src="https://img.shields.io/badge/Extended-2563eb?style=flat-square" alt="Extended"></td>
    </tr>
    <tr>
      <td><strong>通义千问</strong><br><sub>Chinese web expansion</sub></td>
      <td><code>中文搜索</code> <code>网页问答</code> <code>公开内容</code></td>
      <td><code>中文网页</code> <code>搜索入口</code> <code>公开信息</code></td>
      <td><img src="https://img.shields.io/badge/Extended-2563eb?style=flat-square" alt="Extended"></td>
    </tr>
    <tr>
      <td><strong>More</strong><br><sub>Extensible surface</sub></td>
      <td><code>持续扩展</code> <code>更多入口</code> <code>更多平台</code></td>
      <td><code>社交媒体</code> <code>搜索平台</code> <code>垂直内容源</code></td>
      <td><img src="https://img.shields.io/badge/Future-6b7280?style=flat-square" alt="Future"></td>
    </tr>
  </tbody>
</table>

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

## 覆盖的内容世界

通过不同平台已经打磨好的搜索能力，AI Search Hub 可以间接覆盖这些核心内容世界：

<table>
  <tr>
    <td width="33%">
      <strong>🌐 全球网页</strong><br>
      <sub>Google、公开网页、知识站点</sub>
    </td>
    <td width="33%">
      <strong>⚡ 实时社交</strong><br>
      <sub>X / Twitter、Reddit、热点讨论</sub>
    </td>
    <td width="33%">
      <strong>🔥 中文热点</strong><br>
      <sub>微博、抖音、中文热门内容</sub>
    </td>
  </tr>
  <tr>
    <td width="33%">
      <strong>📰 微信生态</strong><br>
      <sub>微信公众号、中文信源补充</sub>
    </td>
    <td width="33%">
      <strong>🧭 海外内容</strong><br>
      <sub>海外社交媒体、公开趋势信息</sub>
    </td>
    <td width="33%">
      <strong>🏮 中文互联网</strong><br>
      <sub>中文网页、垂直站点、内容生态</sub>
    </td>
  </tr>
</table>

<details>
  <summary>原始列表备份</summary>

  <ul>
    <li>Google</li>
    <li>微博</li>
    <li>抖音</li>
    <li>X / Twitter</li>
    <li>Reddit</li>
    <li>微信公众号</li>
    <li>各类公开网页内容</li>
    <li>海外社交媒体</li>
    <li>中文互联网内容生态</li>
  </ul>
</details>

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

## Contributing

欢迎提交 Issues 和 PR。

如果你也认同未来的搜索不应该是 **再写一个更重的爬虫系统**，
而应该是 **更聪明地把现有 AI 搜索入口统一起来**，欢迎一起参与。
