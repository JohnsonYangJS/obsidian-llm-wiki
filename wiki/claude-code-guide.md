---
title: Claude Code 指南
tags: [claude-code, ai-tool, coding]
created: 2026-04-23
updated: 2026-04-23
related: [[hermes-agent]], [[openclaw-guide]], [[mcp-protocol]], [[harness-engineering]]
---

# Claude Code 指南

## 概述
Anthropic 官方 AI 编程工具，通过自然语言在终端直接操控代码库。是终端 Agent 的代表作，GitHub Star 增速历史第一。

## 核心能力

### 安装与配置
- 官方安装：`curl -fsSL https://claude.ai/install.sh | bash`
- Homebrew：`brew install --cask claude`
- 登录：`claude auth`
- 首次配置后写入 `~/.claude/settings.json`

### 工作模式
| 模式 | 说明 | 适合场景 |
|------|------|----------|
| Plan Mode | 先规划再执行 | 复杂任务 |
| Auto Mode | 直接执行 | 简单任务 |
| `--dangerously-skip-permissions` | 跳过权限确认 | 自动化脚本 |

### 核心文件
- `CLAUDE.md` — 项目记忆文件，放在根目录
- `.claude/` — 缓存、记忆、命令目录
- `~/.claude/settings.json` — 全局配置

### Skills 系统
Skills 是一组规范，告诉 Claude 如何执行特定任务。放在 `~/.claude/skills/` 目录下。

### 多 Agent 协作
- `claude --worktree <name>` — 创建独立工作区
- Subagent — 子进程并行执行
- git worktree — 隔离并行开发

### 工具生态
- MCP（Model Context Protocol）— 连接外部服务
- Hooks — 拦截操作的自动化脚本
- 插件市场 — 社区贡献的扩展

## 进阶技巧
- Pipe 数据：`cat error.log | claude`
- 引用网页：`claude < https://example.com`
- `/compact` — 压缩上下文
- `/browse` — 浏览器操作
- `/project` — 切换项目

## 参考来源
- raw/Claude-Code-Complete-Guide-zh-v260411.txt
- raw/Claude-Code-The-Complete-Guide-v260411.txt

## 相关
- [[hermes-agent]] — 自改进 Agent
- [[openclaw-guide]] — 多渠道 Agent
- [[harness-engineering]] — 工具链设计
