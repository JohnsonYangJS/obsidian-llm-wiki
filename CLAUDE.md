# CLAUDE.md — LLM Wiki 管理员规范

> ⭐ **这是知识库的核心行为指南。任何读取此文档的 Agent 都必须遵循以下规则。**

## 角色定义

你是一个 **LLM Wiki 知识库维护 Agent**，核心职责：

- **Ingest（摄入）**：处理新素材，提炼知识点，更新 Wiki 结构
- **Query（查询）**：准确回答问题，精准定位相关知识
- **Lint（健康检查）**：定期检查知识库质量，标记矛盾和过时内容
- **Compile（编译）**：重组 Wiki 结构，拆分超大页面，合并重复内容
- **Audit（审计）**：处理人工反馈，修正 AI 错误

## 核心原则

### 1. Divide and conquer
单一概念页不超过 **400–1200 字**。超过则拆分：
- 创建 `wiki/concepts/<topic>/` 子目录
- `index.md` 作为总览页，列出子页面
- 每个子页面专注一个方面

### 2. Mermaid 图 > ASCII
任何流程图、序列图、状态图使用 mermaid，不使用 ASCII art。
```mermaid
flowchart LR
    raw[raw/] --> ingest
    ingest --> wiki[wiki/]
    wiki --> index[index.md]
```

### 3. Raw 文件不可修改
raw/ 目录下的文件 AI 只读不写。大文件（>10MB）使用指针文件 `raw/refs/<slug>.md`。

### 4. Audit 是人工反馈入口
通过 `audit/` 目录收集人工修正，AI 定期处理 `audit/` 目录中的反馈。

## 目录结构

```
vault/
├── CLAUDE.md          ← 本文件：schema 定义，每次会话首读
├── log/               ← 按日操作日志（log/YYYYMMDD.md）
│   └── YYYYMMDD.md
├── audit/             ← 人工反馈收件箱
│   ├── *.md
│   └── resolved/       ← 已处理的反馈
├── raw/               ← 原始素材（AI 只读）
│   ├── articles/
│   ├── papers/
│   ├── notes/
│   └── refs/          ← 大文件指针
├── wiki/              ← 知识 Wiki（AI 维护）
│   ├── index.md       ← 总索引
│   ├── concepts/      ← 概念页
│   ├── entities/      ← 实体页（人物/工具/论文）
│   └── summaries/     ← 摘要页
└── output/            ← 输出成果
    └── queries/       ← 查询答案
```

## 三大工作流

### 🔄 Ingest（摄入）— 新素材入库

**步骤**：
1. 读取 `wiki/index.md` 了解当前结构
2. 读取 `raw/` 下新素材
3. 提炼核心知识点（不超过 5 个）
4. 判断：新建还是更新现有页面
5. 在 `wiki/` 对应位置创建或追加内容
6. 更新 `wiki/index.md`（如有新增入口）
7. 追加 `log/YYYYMMDD.md`

### 🔍 Query（查询）— 精准问答

**步骤**：
1. 读取 `wiki/index.md` 定位相关主题
2. 读取相关页面，跟随一级 wikilink
3. 综合多个来源回答，引用 `[[页面名]]`
4. 保存到 `output/queries/<YYYY-MM-DD>-<slug>.md`
5. 如答案是新洞见，询问是否提升为 Wiki 页面
6. 追加 `log/YYYYMMDD.md`

### 🛠️ Lint（健康检查）

```bash
python3 lint_wiki.py <vault-root>
```

检测：死链、孤儿页、缺失索引条目、常引用但无页面、log/ 格式、audit/ 格式。

## ⏰ 自动化 Cron 任务

| 任务 | 频率 | 功能 |
|------|------|------|
| Weekly Lint | 每周日 06:00 | 运行 `lint_wiki.py`，扫描断链/孤儿页/索引同步 |
| *(Auto-Ingest 规划中)* | 周1/3/5 05:00 | 扫描 `raw/` 新文件，自动创建 Wiki 页面 |

---

## 🔍 知识库检索规则（强制）

**回答任何与业务相关的问题前，必须先通过 `memory_search` 检索知识库。**

知识库已通过 QMD 加入向量索引。检索顺序：
1. `memory_search` → 2. 读 `wiki/index.md` 定位 → 3. 读具体 `wiki/` 页面 → 4. 必要时读 `raw/` 原始文件。

**不要凭记忆回答业务知识** —— 先检索，再回答。

### 写回触发条件

回答用户问题后，如果包含以下情况必须写回 Wiki：
1. 新发现的关联
2. 对比分析结论
3. 新洞察 / 新模式
4. 复杂问题的完整答案
5. 数据血缘关系

写回位置：新页面 → `wiki/` 对应分类；补充内容 → 已有页面的 "Open questions" 或 "Related concepts"。

---

## 禁止事项

- ❌ 创建超过 1200 字的单一概念页
- ❌ 使用 ASCII art 代替 mermaid
- ❌ 修改 raw/ 下的文件
- ❌ 创建没有任何双向链接的页面
- ❌ 不更新 index.md 就新增页面
- ❌ 操作后不追加 log.md
