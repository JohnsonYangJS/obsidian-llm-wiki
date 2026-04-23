---
title: LLM Wiki 模式
tags: [llm-wiki, knowledge-management, karpathy]
created: 2026-04-23
updated: 2026-04-23
related: [[obsidian-ai-guide]], [[second-brain]], [[claude-code-guide]]
---

# LLM Wiki 模式

## 概述
Andrej Karpathy 2026 年 4 月提出的知识库新范式。核心思想：让 LLM 不仅是工具，更是知识生产的一环——参与知识的摄入、索引、查询和健康检查。

## 三种核心工作流

### 1. Ingest（摄入）
放入新素材 → LLM 分析 → 自动更新 Wiki + 索引 + 日志

### 2. Query（查询）
提问 → LLM 搜索 Wiki → 回答 → 好答案自动存为新 Wiki 页

### 3. Lint（健康检查）
定期检查：矛盾、孤儿页、过时声明、缺失引用

## 两个关键文件

### index.md
内容导向索引，LLM 查询时第一个读的文件。
- 按主题分类
- 链接到各 Wiki 页面
- 由 AI 动态维护

### log.md
追加式操作日志，固定前缀格式。
- 可用 Unix 工具解析
- 便于回溯和审计

## OpenClaw + Obsidian 实现

### Obsidian（存储层）
- 本地 Markdown，AI 可直接读写
- 双向链接构建知识图谱
- Git 版本控制

### OpenClaw（执行层）
- 24/7 自动响应
- 记忆系统积累偏好
- Skills 扩展能力
- Obsidian MCP 连接笔记
- Cron 定时 Lint 检查

## 三层目录架构
```
vault/
├── raw/        ← 原始素材
├── wiki/       ← 知识 Wiki
└── output/    ← 输出成果
```

## 核心洞察
- 知识是动态的，不是静态存档
- 用得越多，知识库越精准
- 飞轮效应：输入越多 → 产出越准 → 使用越多

## 相关
- [[obsidian-ai-guide]] — 存储层工具
- [[second-brain]] — 第二大脑理念
- [[claude-code-guide]] — 可作为执行引擎
