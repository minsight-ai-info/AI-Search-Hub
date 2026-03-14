# AI Search Hub

[English](README.md)

<div align="center">

### 一次提问，分发到多个 AI 平台

[![GitHub stars](https://img.shields.io/github/stars/minsight-ai-info/AI-Search-Hub?style=flat-square)](https://github.com/minsight-ai-info/AI-Search-Hub/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/minsight-ai-info/AI-Search-Hub?style=flat-square)](https://github.com/minsight-ai-info/AI-Search-Hub/network/members)
[![GitHub issues](https://img.shields.io/github/issues/minsight-ai-info/AI-Search-Hub?style=flat-square)](https://github.com/minsight-ai-info/AI-Search-Hub/issues)
[![类型](https://img.shields.io/badge/type-open--source%20skill-black?style=flat-square)](https://github.com/minsight-ai-info/AI-Search-Hub)

</div>

AI Search Hub 是一个基于浏览器自动化的开源 skill。它的目标是把同一个问题发送到多个 AI 平台，再把结果整理成可供工作流继续消费的统一输入。

这个项目不想重复造一个“全能爬虫系统”，而是专注在下面几层：

- 平台原生搜索 / 聊天入口
- 隔离浏览器会话
- 登录恢复流程
- 问题分发
- 回复提取
- 后续再叠加统一聚合层

## 这个仓库当前已经有什么

当前仓库承载的是产品底层执行能力。

已经实现的部分包括：

- 统一入口：`scripts/run_web_chat.py`
- `qwen`、`doubao`、`yuanbao`、`longcat`、`gemini`、`grok` 的站点适配脚本
- 基于用户本地活跃 Chrome profile 的隔离副本启动
- 登录检测与“登录后自动继续”流程
- 优先使用 DOM 级输入，降低用户在桌面其他地方操作时的干扰
- 针对 wrapper 和站点驱动的自动化测试

README 里所描述的“多平台统一聚合入口”是下一步要补齐的核心能力。

## 为什么是 AI Search Hub

很多“全网搜索”方案最后都会变成：

- 自己维护爬虫
- 自己维护浏览器自动化
- 自己处理登录态和验证码
- 自己处理反爬和风控
- 每个平台都做一遍搜索适配
- 反复调整提示词和关键词
- 最后还要自己把碎片结果再拼起来

AI Search Hub 选的是更窄、但更实用的一条路：

> 直接接住平台已经优化好的搜索和聊天能力。

重点不是替代这些平台的检索系统。
重点是把它们编排起来。

## 当前 Provider 状态

| Provider | 状态 | 说明 |
|---|---|---|
| Qwen | 可用 | 已做过真实问答验证 |
| 豆包 | 可用 | 已做过真实问答验证 |
| 元宝 | 可用 | 登录分支修正后已做真实验证 |
| LongCat | 可用但有限制 | 问答链路可跑通，但站点可能限流 |
| Gemini | 实验中 | Chrome/profile 启动与页面状态还在继续打磨 |
| Grok | 实验中 | 验证页与页面状态处理还在继续打磨 |
| 文心一言 | 计划中 | 还未实现 |

## 工作方式

1. 接收一个问题。
2. 打开或复用隔离的 Chromium 调试会话。
3. 以用户本地活跃 Chrome profile 作为种子来源生成副本。
4. 打开目标站点并判断是否需要登录。
5. 如果需要登录，则等待用户完成后自动继续。
6. 输入问题、发送并等待稳定回复。
7. 把结果写入标准输出文件，供后续工作流继续消费。

## 仓库结构

```text
scripts/
  run_web_chat.py
  generic_web_chat_playwright.py
  doubao_playwright.py
  yuanbao_playwright.py
  longcat_playwright.py

tests/
  test_run_web_chat.py
  test_generic_web_chat_playwright.py
  test_longcat_playwright.py

docs/
  superpowers/specs/
  superpowers/plans/
```

## 快速开始

通过统一 wrapper 运行单个 provider：

```bash
python3 scripts/run_web_chat.py --site qwen --prompt "AI 最新新闻"
```

当前支持的 `--site`：

- `qwen`
- `doubao`
- `yuanbao`
- `longcat`
- `gemini`
- `grok`

## 验证

运行当前测试集：

```bash
python3 -m unittest tests.test_run_web_chat tests.test_generic_web_chat_playwright tests.test_longcat_playwright -v
```

静态语法检查：

```bash
python3 -m py_compile scripts/run_web_chat.py scripts/generic_web_chat_playwright.py scripts/doubao_playwright.py scripts/longcat_playwright.py scripts/yuanbao_playwright.py
```

## Roadmap

- 增加真正的 hub 聚合入口，返回统一 JSON
- 继续打磨 Gemini 支持
- 继续打磨 Grok 支持
- 增加文心一言
- 在 provider 原始结果之上增加聚合与融合能力

## 项目方向

AI Search Hub 想做的是一个轻量的编排层，而不是一个越来越重的爬虫框架。

长期价值在于：

- 一个问题
- 多个 provider 原生结果通道
- 一个统一输出契约
- 更顺手的下游 Agent 工作流
