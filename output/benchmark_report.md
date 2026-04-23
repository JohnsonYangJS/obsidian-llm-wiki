# LLM Wiki Benchmark 报告

> 生成时间：2026-04-23 19:39
> 评估问题数：24 | Chunk 大小：500 字符 | Top-K：5
> 评估方法：纯 Python TF-IDF（naive chunk baseline）

---

## 一、检索效果总览

| 指标 | TF-IDF Baseline | QMD 语义（需 Ollama）|
|------|----------------|----------------------|
| Hit@5 | **75.0%** (18/24) | 待测 |
| Avg MRR | **0.510** | 待测 |

> TF-IDF Baseline 说明：固定 500 字符 chunk + TF-IDF 向量余弦相似度，
> 这是标准 RAG 系统的最常见 baseline，用于衡量 LLM Wiki 知识组织带来的增量价值。

---

## 二、问题详情

| # | 问题 | Top-1 结果文件 | Hit@5 | MRR | 预期文件 |
|---|------|---------------|-------|-----|---------|
| 1 | LLM Wiki 的三层架构是什么？ | `wiki/second-brain.md` | ✅ | 0.50 | wiki/llm-wiki-pattern.md, wiki/index.md |
| 2 | Karpathy 的 LLM Wiki 核心思想是什么？ | `wiki/second-brain.md` | ✅ | 0.50 | wiki/llm-wiki-pattern.md |
| 3 | OpenClaw 的 Skills 系统是什么？ | `wiki/mcp-model-context-protocol.md` | ❌ | 0.00 | wiki/openclaw-guide.md |
| 4 | OpenClaw 和 Claude Code 有什么区别？ | `wiki/openclaw-vs-claude-code.md` | ✅ | 1.00 | wiki/openclaw-vs-claude-code.md |
| 5 | Harness Engineering 是什么？ | `wiki/harness-engineering.md` | ✅ | 1.00 | wiki/harness-engineering.md |
| 6 | Hermes Agent 是什么？ | `wiki/articles/summaries/hermes-agent-从入门到精通-v260407.md` | ✅ | 0.50 | wiki/hermes-agent.md |
| 7 | MCP Model Context Protocol 是什么？ | `wiki/mcp-model-context-protocol.md` | ✅ | 1.00 | wiki/mcp-model-context-protocol.md |
| 8 | Skills 系统如何工作？ | `wiki/skills-system.md` | ✅ | 1.00 | wiki/skills-system.md |
| 9 | 第二大脑 Second Brain 是什么？ | `wiki/second-brain.md` | ✅ | 1.00 | wiki/second-brain.md |
| 10 | Obsidian 如何连接 OpenClaw？ | `wiki/articles/summaries/obsidian-ai-v100.md` | ❌ | 0.00 | wiki/obsidian-ai-guide.md |
| 11 | Dataview 在 Obsidian 中有什么用？ | `wiki/articles/summaries/obsidian-ai-v100.md` | ✅ | 0.25 | wiki/obsidian-ai-guide.md |
| 12 | Claude Code 使用技巧有哪些？ | `wiki/articles/summaries/claude-code-source-code-analysis-v260411.md` | ❌ | 0.00 | wiki/claude-code-guide.md |
| 13 | Polymarket 是什么？ | `wiki/articles/summaries/polymarket-complete-guide-zh-v200.md` | ✅ | 0.25 | wiki/polymarket-guide.md |
| 14 | Auto-ingest 脚本是如何工作的？ | `wiki/index.md` | ✅ | 1.00 | wiki/index.md |
| 15 | 知识库自动化有哪些 Cron 任务？ | `wiki/skills-system.md` | ❌ | 0.00 | wiki/index.md |
| 16 | 如何生成知识库的 D3 图谱？ | `wiki/openclaw-vs-claude-code.md` | ✅ | 0.33 | wiki/index.md |
| 17 | lint_wiki.py 检查哪些内容？ | `wiki/index.md` | ✅ | 1.00 | wiki/index.md |
| 18 | 飞书文件如何自动入库？ | `wiki/openclaw-vs-claude-code.md` | ✅ | 0.33 | wiki/index.md |
| 19 | CLAUDE.md 的 Schema 层规范是什么？ | `wiki/articles/summaries/赖翔-llm-wiki模式.md` | ❌ | 0.00 | CLAUDE.md |
| 20 | 知识库如何做健康检查？ | `wiki/openclaw-vs-claude-code.md` | ✅ | 0.33 | wiki/index.md |
| 21 | 为什么 AI 应该参与知识生产而不是只做检索？ | `wiki/obsidian-ai-guide.md` | ❌ | 0.00 | — |
| 22 | OpenClaw 的 agent 和 skills 是什么关系？ | `wiki/skills-system.md` | ✅ | 1.00 | wiki/openclaw-guide.md, wiki/skills-system.md |
| 23 | MCP 协议解决了什么问题？ | `wiki/mcp-model-context-protocol.md` | ✅ | 1.00 | wiki/mcp-model-context-protocol.md |
| 24 | Obsidian 作为第二大脑的优势是什么？ | `wiki/articles/summaries/obsidian-ai-v100.md` | ✅ | 0.25 | wiki/obsidian-ai-guide.md, wiki/second-brain.md |


## 三、解读与建议

### 如何解读这些数字

- **Hit@5**：相关知识出现在 Top-5 检索结果的比例。75.0% 意味着
  6 道题找不到相关知识，原因通常是：该知识点尚未入库，或 chunk 切分恰好切断了关键段落。

- **MRR（Mean Reciprocal Rank）**：正确答案的排名位置的倒数均值。
  MRR 越高，说明相关知识越靠前。0.510 说明整体排名偏后，有优化空间。

### 下一步

1. **QMD 语义搜索对比**：配置 Ollama + embedding 模型后，重新跑 benchmark 对比 QMD vs TF-IDF
2. **调 Chunk 大小**：试试 300 / 1000 字符，看哪个效果更好
3. **增加问题集**：补充更多基于实际使用场景的问题
4. **LLM 答案质量评估**：不仅看检索指标，还要让 AI 对同一问题给出答案，盲测质量

---

*报告由 benchmark_rag.py 自动生成 | github.com/JohnsonYangJS/obsidian-llm-wiki*
