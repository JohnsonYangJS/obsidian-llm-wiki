---
title: MCP 模型上下文协议
tags: [mcp, openclaw, tool-integration, ai-agent]
created: 2026-04-23
updated: 2026-04-23
related: [[openclaw-guide|OpenClaw 指南]], [[skills-system|Skills 系统]], [[llm-wiki-pattern|LLM Wiki 模式]], [[claude-code-guide|Claude Code 指南]]
sources: []
---

# MCP 模型上下文协议

> 连接 AI Agent 与外部工具/数据的标准协议，让 AI 能够调用本地应用和数据。

## 概述
MCP（Model Context Protocol）是一种让 AI 模型与外部工具、数据源建立标准化连接的协议。OpenClaw 通过 Skills 系统实现 MCP 能力，支持连接文件系统、浏览器、数据库等多种外部资源。

## 核心概念

- **MCP Server**：提供特定能力的外部服务（如文件系统服务器、数据库服务器）
- **Tool**：MCP Server 暴露的可调用工具
- **Resource**：MCP Server 提供的可读取资源（如文件、数据库记录）
- **Prompt**：预定义的提示模板

## OpenClaw 中的 MCP

OpenClaw 通过 Skills 机制扩展 MCP 能力，常见 Skills：
- `obsidian` — 读写 Obsidian 笔记库
- `filesystem` — 文件系统操作
- `web-search` — 网络搜索
- `git` — Git 版本控制

## 与 Skills 的关系

Skills 是 OpenClaw 对 MCP 的实现方式，两者本质相同：
- **Skills** = OpenClaw 的 MCP 扩展机制
- **MCP** = 更通用的标准协议名称

## 相关链接
- [[openclaw-guide|OpenClaw 指南]]
- [[skills-system|Skills 系统]]
- [[claude-code-guide|Claude Code 指南]]
