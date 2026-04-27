---
title: migration-story-context-infrastructure-to-claude-code
type: concept
category: articles
tags: [Portable Doc Layer, Claude Code Integration, Mirror Sync Tool, Agent Runtime Projection]
created: 2026-04-26
updated: 2026-04-26
related: [[[Claude Code 指南]], [[Skills 系统]]]
sources: [file:///Users/txyjs/Documents/Obsidian Vault/raw/email-20260427-转发-从-context-infrastructure-文件.txt]
generation: LLM (MiniMax-M2.7-highspeed)
---

# migration-story-context-infrastructure-to-claude-code

> 本文是一份实战记叙，描述如何将朴素的 portable doc 文件夹（来自 context-infrastructure 仓库的 rules/ 目录）演化为一套能装进 Claude Code、可管理多个子体、能反向蒸馏 lesson 的可插拔系统。文章揭示了朴素 portable layer 的三个核心局限，并提供从母仓库建设到 Claude Code 主投影安装的完整四步路径，包含 Phase

## 概述

本文记录了将 context-infrastructure 仓库的朴素 `rules/` 文件夹演化为完整 Claude Code 工作系统的完整路径。核心价值在于揭示 portable layer 的三个工程缺口，并提供可复制的安装方法论。

## 起点与局限

### 朴素 rules/ 文件夹结构
- `rules/SOUL.md` — 人格定义
- `rules/USER.md` — 用户 profile
- `rules/COMMUNICATION.md` — 沟通风格
- `rules/WORKSPACE.md` — 目录路由
- `rules/axioms/` — 决策原则
- `rules/skills/` — 可复用工作流

### 三个核心局限
1. **无 agent runtime 主投影**：语义层与 runtime 层耦合，换 runtime 需重做
2. **无项目特化对接面**：缺乏 portable 层与具体项目的衔接协议
3. **无 lesson 回流通道**：项目经验无法升级回 portable 层复用

## 四步演进路径

### 第一步：提升为母仓库

加入 Philosophy 层（First Principles + 50+ axioms），建立 4 层语义边界：

| 层 | 内容 | 跨项目 | 跨 runtime |
|---|---|---|---|
| Philosophy | First Principles + 50+ axioms | ✅ | ✅ |
| Identity | SOUL / USER / COMMUNICATION | ✅ | ✅ |
| Working Environment | R-rules / routing / entry doc | ❌ | ❌ |
| Execution | skills 通用部分 + 业务工具 | 部分 ✅ | 部分 ✅ |

关键机制：reconciliation 协议解决 fork 间的 axiom 编号冲突。

### 第二步：Claude Code 主投影安装

#### Phase 0：跨投影同步工具

建立 `bridging/` 目录，包含：
- `mirror_sync.py`：四个命令（`--register` / `--apply` / `--check` / `--list`）
- `mirror_manifest.json`：外置 sync 状态

设计原则：
- 零 metadata 进文档
- 外置 manifest 保持文档纯净
- 支持 `addendum_marker` 保留项目本地补充段

#### Phase 1-6：逐层构建

- **Phase 1**：Identity 核心（SOUL/USER/COMMUNICATION/PROJECT_ADAPTER）
- **Phase 2**：Routing 表与入口协议
- **Phase 3**：R-rules 拆分与索引
- **Phase 4**：Axioms 完整填充
- **Phase 5**：Skills 工作流填充
- **Phase 6**：全量镜像校验

## 关键设计

### 4 层语义边界
每条 artifact 入 portable 层前需明确所属层级，每条 R-rule 带 portability 标签：
- `<portable>`：跨项目通用
- `<portable-shape>`：形态通用内容特化
- `<project>`：纯项目特化

### Mirror Sync 机制
支持项目本地补充段而不污染 portable 母版，通过 `addendum_marker` 标记保留区域。

## Related

- [[Claude Code 指南]]
- [[Skills 系统]]

## Sources

- [email 20260427 转发 从 context infrastructure 文件](file:///Users/txyjs/Documents/Obsidian Vault/raw/email-20260427-转发-从-context-infrastructure-文件.txt)

---
*由 auto_ingest.py 自动生成于 2026-04-26*
