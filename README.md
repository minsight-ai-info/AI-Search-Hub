# AI Search Hub（国内平台 / camofox 版）

AI Search Hub 是一个基于 **camofox 浏览器会话复用**的国内 AI 搜索与问答聚合工具。它把一次提问分发到已验证的平台，并只回收各平台的**最终回答正文**，避免把登录页、思考过程、检索状态或浏览器 UI 误当答案。

> 本地维护策略：**只支持国内平台，不再尝试或调度国外平台。**

## 已验证平台

| 平台 | CLI 标识 | 特性 |
|---|---|---|
| 通义千问 | `qwen` | 中文网页研究、带完成信号的回答提取 |
| 豆包 | `doubao` | 字节内容生态；识别流式完成和 SSE 限流错误 |
| Kimi | `kimi` | 长文本研究；排除 Think/规划块，只取最终正文 |
| MiniMax Agent | `minimaxi` | ProseMirror 编辑器输入；提取 assistant 最终消息 |
| LongCat | `longcat` | 联网检索；排除检索状态，只取 Markdown 正文 |

所有上述平台均已通过登录态复用、短回答和 600 字级长回答的端到端验证。

## 前置条件

- Python 3.10+
- `camofox-browser` CLI 在 `PATH` 中
- camofox 服务运行于 `localhost:9377`
- 已在 camofox 中完成各平台登录并保存 session

查看 session：

```bash
camofox-browser session list --format json
```

登录完成后保存 session：

```bash
camofox-browser session save qwen
camofox-browser session save doubao
camofox-browser session save kimi
camofox-browser session save minimaxi
camofox-browser session save longcat
```

不要把密码、验证码、Cookie 或其他凭据写入仓库或聊天记录。

## 单平台调用

```bash
cd /home/wang/ai-search-hub
python3 scripts/run_camofox_chat.py \
  --site qwen \
  --prompt "请整理这个问题的可核验信息，并列出来源。" \
  --timeout 180 \
  --min-answer-chars 300 \
  --output /home/wang/artifacts/documents/qwen-answer.txt
```

可用 `--site`：`qwen`、`doubao`、`kimi`、`minimaxi`、`longcat`。

## 多平台批量调用

页面准备和提问按顺序完成，随后对各 tab 并发轮询，避免 camofox 的并发导航冲突：

```bash
python3 scripts/run_camofox_batch.py \
  --sites qwen doubao kimi minimaxi longcat \
  --prompt "请检索并区分官方资料、独立测试和媒体传闻。" \
  --timeout 180 \
  --min-answer-chars 300 \
  --stable-rounds 3 \
  --output-dir /home/wang/artifacts/documents/ai-search-hub-run
```

输出目录包含每个平台的 `<site>.txt` 以及 `batch-summary.json`。短暂的 camofox RPC 超时会保留 tab 并重试；平台总超时或明确的限流错误才会标为失败。

## 路由建议

- 中文公开网页、阿里生态：Qwen
- 抖音 / 今日头条语境、中文热点：豆包
- 长文档、研究资料、长回答整理：Kimi
- MiniMax Agent 或通用中文任务：MiniMax
- 美团 / 本地生活、中文联网检索：LongCat

更详细的策略见 [ROUTING.md](ROUTING.md)。

## 运行与测试

```bash
python3 -m unittest tests/test_phase1_reliability.py -q
python3 -m py_compile scripts/camofox_runner.py scripts/run_camofox_chat.py scripts/run_camofox_batch.py
```

测试输出、截图和临时调试文件统一写入 `/home/wang/artifacts/`，不提交到仓库。

## 目录

```text
scripts/
  camofox_runner.py       # camofox CLI 封装、输入和多行结果解析
  run_camofox_chat.py     # 单平台登录复用、提交、完成判定和正文提取
  run_camofox_batch.py    # 串行准备 + 并发轮询的批量执行器
tests/
  test_phase1_reliability.py
ROUTING.md                # 国内平台路由说明
SKILL.md                  # Hermes 项目技能说明
```

## 已知约束

- 页面结构、登录风控、限流和网络错误均可能随平台变化；先看 `batch-summary.json`，不要把失败平台的空结果当结论。
- 仅根据可核验的一手来源下结论；平台生成内容本身不是事实证明。
- 需要新增平台时，先完成登录、短回答、长回答和完成状态验证，再加入 `SITE_CONFIG`。
