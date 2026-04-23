---
title: Skills 系统
tags: [skills, openclaw, mcp, extensibility, ai-agent]
created: 2026-04-23
updated: 2026-04-23
related: [[openclaw-guide|OpenClaw 指南]], [[mcp-model-context-protocol|MCP 模型上下文协议]], [[llm-wiki-pattern|LLM Wiki 模式]], [[harness-engineering|Harness 工程]]
sources: []
---

# Skills 系统

> OpenClaw 的能力扩展机制，让 AI Agent 能够调用各种外部工具和服务。

## 概述
Skills 是 OpenClaw 的核心扩展系统，每个 Skill 是一个包含指令和工具定义的包，可以让 AI 调用原本不具备的能力（如控制 Sonos 音响、查询加密货币、发送飞书消息等）。

## 核心特性

- **Skill 发现**：通过 ClawdHub 在线搜索安装
- **本地 Skills**：支持本地自定义 Skills（写 SKILL.md 即可）
- **工作流集成**：Skills 可被 Cron 定时任务调用
- **多渠道触发**：支持飞书、微信、Telegram 等多渠道触发 Skills

## 常见 Skills

| Skill | 功能 |
|-------|------|
| `obsidian` | 读写 Obsidian 笔记 |
| `filesystem` | 文件操作、移动、分类 |
| `web-search` | 搜索网页内容 |
| `cron` | 定时任务调度 |
| `weather` | 天气查询 |
| `crypto-market-rank` | 加密货币排行 |
| `trading-signal` | 链上聪明钱信号 |

## 相关链接
- [[openclaw-guide|OpenClaw 指南]]
- [[mcp-model-context-protocol|MCP 模型上下文协议]]
- [[llm-wiki-pattern|LLM Wiki 模式]]
