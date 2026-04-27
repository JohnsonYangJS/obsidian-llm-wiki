---
title: hermes-agent
type: entity
category: articles
tags: [Harness Engineering, 自我进化 Agent, 三层记忆系统, Skill 系统]
created: 2026-04-27
updated: 2026-04-27
related: [[[Harness 工程]], [[OpenClaw 指南]], [[Claude Code 指南]], [[Skills 系统]], [[MCP 模型上下文协议]]]
sources: [file:///Users/txyjs/Documents/Obsidian Vault/raw/Hermes-Agent-The-Complete-Guide-v260407.txt]
generation: LLM (MiniMax-M2.7-highspeed)
---

# hermes-agent

> Hermes Agent 是由开源 AI 研究实验室 Nous Research 于 2026 年 2 月发布的 AI Agent 框架，在 GitHub 上两个月内获得超过 27,000 星。它是首个将 Harness Engineering 方法论完整产品化的工具，内置五大核心组件：指令层、约束层、反馈层、记忆层和编排层。与 OpenClaw 的配置即行为模式和 Claude Code 的交互

## 概述

Hermes Agent 是 Nous Research 于 2026 年 2 月发布的开源 AI Agent 框架，是首个将 Harness Engineering 方法论完整内置的产品。其核心理念是：无需用户手动配置，Agent 自主构建、运行和改进自己的"驾驭框架"（Harness）。

## 核心架构：五组件内置系统

Hermes 内置了 Harness Engineering 的五大组件，实现开箱即用：

| 组件 | 传统手动实现 | Hermes 内置系统 |
|------|-------------|----------------|
| 指令层 | 手写 CLAUDE.md | Skill 系统（自动创建+自改进） |
| 约束层 | 配置 hooks/linter/CI | 工具权限+沙箱+按需启用 |
| 反馈层 | 手动评审/评估 Agent | 自改进学习循环（任务后自动回顾） |
| 记忆层 | 手动维护知识库 | 三层记忆+用户建模 |
| 编排层 | 自建多 Agent 管道 | 子 Agent 委托+cron 定时 |

## 三大核心能力

### 1. 自改进学习循环
每次任务完成后自动回顾，积累经验并改进自身行为，无需人工干预。

### 2. 三层记忆系统
- **会话记忆**：当前对话上下文
- **持久化记忆**：跨会话积累的长期知识
- **Skill 记忆**：技能定义与使用经验

### 3. Skill 系统
采用 agentskills.io 标准，与 Claude Code/OpenClaw 互操作。支持自定义技能扩展，已集成 40+ 工具和 MCP 协议。

## 定位对比

| 工具 | 模式 | 特点 |
|------|------|------|
| Claude Code | 交互式编程 | 实时协作的结对编程伙伴 |
| OpenClaw | 配置即行为 | SOUL.md 定义行为，5700+ 社区 Skills |
| Hermes Agent | 自主后台+自进化 | 24/7 运行，自我学习进化 |

## 技术特点

- **MIT 许可证**，完全开源
- 支持任意 LLM API
- 多平台访问（Telegram/Discord/Web）
- 强调用户控制与模型可操控性
- 无内容审查，"无约束的中立对齐"

## 使用场景

- 个人知识助手（跨会话记忆）
- 开发自动化（代码审查到部署）
- 内容创作（研究到草稿）
- 多 Agent 编排协同

## Related

- [[Harness 工程]]
- [[OpenClaw 指南]]
- [[Claude Code 指南]]
- [[Skills 系统]]
- [[MCP 模型上下文协议]]

## Sources

- [Hermes Agent The Complete Guide v260407](file:///Users/txyjs/Documents/Obsidian Vault/raw/Hermes-Agent-The-Complete-Guide-v260407.txt)

---
*由 auto_ingest.py 自动生成于 2026-04-27*
