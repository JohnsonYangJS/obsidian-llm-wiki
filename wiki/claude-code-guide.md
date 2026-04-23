---
title: Claude Code 指南
tags: [claude-code, ai-agent, coding, openclaw]
created: 2026-04-23
updated: 2026-04-23
related: [[openclaw-vs-claude-code]], [[hermes-agent]], [[mcp-model-context-protocol]]
sources: [raw/Claude-Code-Complete-Guide-zh-v260411.pdf]
---

# Claude Code 指南

> AI 编程工具，终端 Agent 代表作，通过自然语言指令完成代码编写、调试和重构。

## 概述
Claude Code 是 Anthropic 推出的 CLI 编程 Agent，深度集成 Claude 模型。用户在终端通过自然语言与 AI 交互，AI 可以读写文件系统、执行命令、重构代码。是 LLM Wiki 模式中"战术层"的代表工具。

## 核心功能

- **代码编写**：根据描述生成完整代码文件
- **代码调试**：理解错误信息，定位并修复问题
- **代码重构**：改善代码结构，不改变功能
- **终端执行**：直接运行命令，实时获取反馈
- **上下文理解**：支持超长上下文（200K），理解大型代码库

## 架构特点

- 基于 MCP（Model Context Protocol）连接外部工具
- 支持 filesystem、grep、bash 等内置工具
- 可通过 Skills 扩展更多能力

## 相关链接
- [[openclaw-vs-claude-code|OpenClaw vs Claude Code]] — 两者定位对比
- [[hermes-agent|Hermes Agent]] — 另一个自改进 Agent
- [[mcp-model-context-protocol|MCP 模型上下文协议]] — 连接 AI 与工具的标准协议
