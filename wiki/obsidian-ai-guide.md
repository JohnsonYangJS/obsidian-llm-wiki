---
title: Obsidian AI 指南
tags: [obsidian, note-taking, ai-tool]
created: 2026-04-23
updated: 2026-04-23
related: [[llm-wiki-pattern]], [[second-brain]], [[claude-code-guide]]
---

# Obsidian AI 指南

## 概述
本地优先 Markdown 笔记工具。三个独立十亿级项目不约而同选择了它作为知识管理底层。完全本地存储，AI 可直接读写文件。

## 为什么适合 AI
- **Markdown 文件** = AI 原生格式
- **零延迟** = 本地文件读取
- **完全私有** = 不依赖云服务
- **双向链接** = 构建知识图谱

## 核心功能

### 双向链接 `[[页面名]]`
明确标注页面间关系，构建知识网络。

### 图谱视图
可视化知识之间的关系，发现隐藏联系。

### 模板系统
标准化笔记结构，对 AI 友好。

### 插件生态
5000+ 插件，可接入 AI 能力。

## 与 Claude Code 配合
在 vault 根目录创建 `CLAUDE.md`，Claude Code 启动时自动读取：
- 注入项目规范
- 定义笔记分类规则
- 指导 AI 如何处理笔记

## 最佳目录结构（PARA）
```
vault/
├── Areas/      ← 项目和责任领域
├── Resources/  ← 主题资源
├── Archives/   ← 归档
└── Notes/      ← 随机笔记
```

## LLM Wiki 架构
配合 OpenClaw 时推荐三层：
- raw/ — 原始素材
- wiki/ — 知识 Wiki
- output/ — 输出成果

## 参考来源
- raw/Obsidian-AI-v1.0.0.txt
- raw/Obsidian-AI-The-Complete-Guide-v1.0.0.txt

## 相关
- [[llm-wiki-pattern]] — AI 自管理知识库
- [[second-brain]] — 第二大脑
- [[claude-code-guide]] — AI 编程工具
