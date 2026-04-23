---
title: OpenClaw 指南
tags: [openclaw, ai-agent, framework]
created: 2026-04-23
updated: 2026-04-23
related: [[claude-code-guide]], [[hermes-agent]], [[obsidian-ai-guide]], [[skills-system]]
---

# OpenClaw 指南

## 概述
开源 Agent 框架，不到 5 个月从 0 到 33 万 GitHub Stars，成为历史增速第一开源项目。支持飞书、微信、WhatsApp 等多渠道接入。

## 核心架构

### Gateway
24/7 后台守护进程，处理所有消息路由和 Agent 执行。

### Channel
接收消息的渠道插件（飞书/微信/Telegram/Discord 等）。

### Agent
核心 AI 模块，包含：
- Workspace（工作区）
- Memory（记忆系统）
- Skills（能力扩展）

## 记忆系统
- MEMORY.md — 自动保存的会话摘要
- 每个项目独立的记忆文件
- AGENTS.md — 平台规范

## Skills 生态
ClawHub 上 13,000+ 社区 Skills：
- 飞书/日历/任务集成
- 代码/Git/Shell 工具
- 内容创作/社交媒体
- 数据分析/可视化

## 部署方式
- 本地安装（npm）
- Docker（推荐）
- 云厂商一键部署

## 安全模型
- ACP Provenance — Agent 身份验证
- 设备配对短期 token
- 敏感信息隔离

## 参考来源
- raw/OpenClaw-Complete-Guide-zh-v1.4.0.txt
- raw/OpenClaw-The-Complete-Guide-v260411.txt

## 相关
- [[hermes-agent]] — 自改进 Agent
- [[claude-code-guide]] — 编程工具
- [[obsidian-ai-guide]] — 笔记工具
- [[skills-system]] — 能力扩展机制
