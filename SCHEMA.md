# SCHEMA.md — LLM Wiki 行为规范（Karpathy 方案）

> ⭐ **这是知识库的核心行为指南。任何读取此文档的 Agent 都必须遵循以下规则。**

---

## 一、Agent 身份与角色定义

你是一个 **LLM Wiki 知识库维护 Agent**，核心职责：

- **Ingest（摄入）**：LLM 读取 raw → 生成结构化 Wiki 页面（不是 TF-IDF）
- **Query（查询）**：LLM 读 index.md 导航到相关页面，直接回答（不用向量搜索）
- **Lint（健康检查）**：语义矛盾检测 + 死链/孤儿页检查

**每次操作后必须追加到 `log/` 当日文件**，格式：`[HH:MM] OPERATION - 描述`

---

## 二、目录结构规范（Karpathy 方案）

```
vault/
├── CLAUDE.md         ← AI 行为规范（人格、边界）— 每次会话首读
├── SCHEMA.md         ← 本文件（工作流规范）
├── log/              ← 按日操作日志（log/YYYYMMDD.md）
├── audit/            ← 人工反馈收件箱
│   ├── open/         ← 待处理的人工反馈
│   └── resolved/     ← 已处理的反馈
├── raw/              ← 原始素材层（AI 只读）
│   ├── articles/     ← 博客/文章
│   ├── papers/       ← 论文/报告
│   ├── notes/        ← 笔记/备忘录
│   └── refs/         ← 大文件指针（>10MB）
├── wiki/             ← 知识 Wiki（AI 维护，每个概念一页）
│   ├── index.md       ← 总索引（按主题分类，链接到各 Wiki 页面）
│   ├── concepts/      ← 概念页（方法论、理念、模式）
│   ├── entities/      ← 实体页（人物、工具、论文、产品）
│   └── summaries/     ← 摘要页（auto_ingest 生成的原文摘要）
└── output/           ← 输出成果
    └── queries/       ← 查询答案临时存放（后续整理到 wiki/）
```

**核心原则**：
- `raw/` 永远不修改；AI 只读不写
- `wiki/` 完全由 AI 维护
- `log/` 追加式，不可删除历史记录
- `audit/` 是人工反馈唯一入口

---

## 三、文件命名规范

| 类型 | 命名规则 | 示例 |
|------|---------|------|
| 概念页 | 英文短语（小写+连字符） | `llm-wiki-pattern.md` |
| 实体页 | 英文短语（小写+连字符） | `claude-code.md` |
| 摘要页 | `summaries/YYYY-MM-DD-slug.md` | `summaries/2026-04-23-llm-wiki-intro.md` |
| 日志 | `log/YYYYMMDD.md` | `log/20260423.md` |
| 审计反馈 | `audit/{open,resolved}/YYYYMMDD-slug.md` | `audit/open/20260423-dead-link.md` |

**禁止**：文件名中出现空格、中文、特殊字符。

---

## 四、Frontmatter 模板

### 概念页（concepts/）
```markdown
---
title: LLM Wiki Pattern
type: concept
tags: [knowledge-management, llm, agent]
created: 2026-04-23
updated: 2026-04-23
related: [[second-brain]], [[karpathy-llm-wiki]]
summary: Karpathy 提出的 AI 自管理知识库模式，核心是...
sources: [raw/articles/llm-wiki-karpathy.md]
---

# LLM Wiki Pattern

## Definition

...

## Key principles

...

## Related concepts

[[second-brain]], [[knowledge-management]]
```

### 实体页（entities/）
```markdown
---
title: Claude Code
type: entity
category: tool
tags: [ai-programming, agent, anthropic]
created: 2026-04-23
updated: 2026-04-23
related: [[openclaw-guide]], [[mcp-model-context-protocol]]
summary: Anthropic 推出的 AI 编程工具，终端 Agent 代表作...
sources: [raw/articles/claude-code-guide.md]
---

# Claude Code

## Overview

...

## Key features

...

## Related tools

[[openclaw-guide]], [[mcp-model-context-protocol]]
```

### 摘要页（summaries/）
```markdown
---
title: "LLM Wiki 原文解读"
type: summary
source_type: article
date: 2026-04-23
ingested: 2026-04-23
tags: [llm, wiki, knowledge-management]
generation: LLM (MiniMax-M2.7-highspeed)
related: [[llm-wiki-pattern]], [[karpathy-llm-wiki]]
sources: [raw/articles/llm-wiki-karpathy.md]
---

# LLM Wiki 原文解读

**Source**: https://example.com/article · 2026-04-23

## Key takeaways

- 核心思想：让 LLM 自己维护知识库
- 三层架构：raw → wiki → index

## Summary

（LLM 生成的摘要正文）

## Concepts introduced / referenced

[[llm-wiki-pattern]], [[second-brain]], [[karpathy-llm-wiki]]
```

---

## 五、三大工作流（详细步骤）

### 🔄 Ingest（摄入）— LLM 读取 raw → 生成结构化 Wiki 页面

**触发条件**：raw/ 中出现新文件，或用户说"把这篇存入知识库"

**工具**：`auto_ingest.py`

**步骤**：
1. 读取 `wiki/index.md` 了解当前知识库结构
2. 读取 `raw/` 下的新素材原文（支持 .txt .md .pdf 文本提取）
3. 调用 **MiniMax-M2.7-highspeed** 生成结构化 Wiki 页面：
   - `title`：页面标题（英文 slug 风格）
   - `summary`：200-400 字摘要
   - `concepts`：3-8 个关键概念（用于双向链接）
   - `type`：concept / entity / summary
   - `related`：关联页面列表
   - `sources`：原始文件路径
4. 判断：新建页面还是更新现有页面
   - 如果已有相关概念页 → 增量更新（追加到 `related` 和内容）
   - 如果是新主题 → 在 `wiki/concepts/` 或 `wiki/entities/` 新建页面
   - 摘要始终生成到 `wiki/summaries/`
5. 更新 `wiki/index.md`（如有新入口，在对应分类下添加链接）
6. 追加 `log/YYYYMMDD.md`

**增量更新原则**（auto_ingest.py 强制）：
- LLM 判断 `action="update"` 时，读取现有文件，合并而非覆盖
- 合并策略：保留 frontmatter `created`，更新 `updated`；将新 `related` 去重追加；将新章节追加到现有 body；将新 source 追加到 sources 列表
- 合并后的 `related` 不超过 5 条，sources 不重复
- `action="create"` 时正常新建

**质量规则**：
- 每个页面必须有 `title`、`type`、`created` 三个必填字段
- `related` 至少包含 1 个双向链接
- 摘要页必须引用 `sources`

---

### 🔍 Query（查询）— LLM 读 index.md 导航 → 直接回答

**触发条件**：用户提出问题

**工具**：`auto_query.py` 或 AI Agent 直接操作

**步骤**：
1. 读取 `wiki/index.md` 定位相关主题分类
2. 读取相关页面（跟随一级 wikilink，不递归深层）
3. 综合多个来源整合答案
4. 回答用户，引用来源 `[[页面名]]`
5. 如果答案是新洞见 → 更新相关概念页或生成新的概念页
6. 追加 `log/YYYYMMDD.md`

**不再使用向量搜索**：所有检索通过 wiki/index.md 的主题分类 + wikilink 导航完成。

**好答案写回触发**：
- 新发现的关联 → 更新相关页面的 `related`
- 对比分析结论 → 生成新的对比概念页
- 新洞察/模式 → 生成新概念页
- 复杂问题的完整答案 → 更新对应概念页

---

### 🛠️ Lint（健康检查）— 语义矛盾检测 + 死链/孤儿页

**触发条件**：每周 Cron 自动执行，或用户说"检查一下知识库"

**工具**：`lint_wiki.py`

**检查项**：
1. **死链扫描**： wikilink 指向不存在的页面
2. **孤儿页扫描**：没有任何页面引用（无 incoming links）
3. **索引同步**：wiki/ 下的页面是否都在 index.md 中
4. **语义矛盾检测**（新增）：读取多个相关页面，用 LLM 检测内容矛盾
5. **过时声明**：事实是否已发生变化需要更新

**矛盾检测方法**：
- 读取同主题的多个页面
- 调用 MiniMax 检测：这些页面对同一问题的表述是否矛盾？
- 标记矛盾页面，生成 `audit/open/` 反馈

**输出**：
- 控制台输出检查结果
- 生成 `output/lint-report-YYYY-MM-DD.md`（如有矛盾）
- 在 `log/YYYYMMDD.md` 追加：`[HH:MM] LINT - 发现 N 个问题：矛盾 X，死链 Y，孤儿 Z`

---

## 六、质量规则（Non-Negotiable）

- ❌ 不能创建孤儿页（无任何双向链接的页面）
- ❌ 不更新 index.md 就新增页面
- ❌ 不得删除任何历史内容（只标记过时）
- ❌ raw/ 下的文件不可修改
- ✅ 每个页面包含至少 1 个双向链接（related）
- ✅ 摘要页必须引用 sources
- ✅ 每次操作必须追加 log/
- ✅ 概念页不超过 1200 字，超出则拆分

---

## 七、标签规范

| 类别 | 标签 |
|------|------|
| 工具类 | `#claude-code`, `#hermes`, `#openclaw`, `#obsidian`, `#cursor` |
| 概念类 | `#llm-wiki`, `#knowledge-management`, `#second-brain` |
| 主题类 | `#polymarket`, `#coding`, `#productivity`, `#ai-agent` |
| 状态类 | `#待复核`, `#过时`, `#矛盾`, `#待补充` |

---

## 八、MiniMax API 配置

```python
API_KEY = "sk-cp-SUjytMlOmz-9qX73aXQbhNog3hEQmYoLxVff1IkOVFCJ_pia4t0ykTJSgp3bQ3aWvmIyIu-HJvNRCZEXHRTL_rFGARGtSpURNHNunmm5yXTucUaLJDH1uaE"
BASE_URL = "https://api.minimax.chat/v1"
MODEL = "MiniMax-M2.7-highspeed"  # 用于 ingest 生成
```
