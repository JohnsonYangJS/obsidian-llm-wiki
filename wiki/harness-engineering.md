---
title: Harness 工程
tags: [harness, engineering, ai-toolchain, development]
created: 2026-04-23
updated: 2026-04-23
related: [[claude-code-guide|Claude Code 指南]], [[skills-system|Skills 系统]], [[openclaw-guide|OpenClaw 指南]], [[llm-wiki-pattern|LLM Wiki 模式]]
sources: []
---

# Harness 工程

> 为 AI Agent 构建可靠工具链的工程实践，让 AI 能够稳定地执行复杂任务。

## 概述
Harness（挽具/ harness engineering）指的是为 AI Agent 设计、构建和维护外部工具链的工程实践。核心目标是让 AI 能够可靠地调用外部工具完成任务，就像给机器人打造一副可靠的四肢。

## 核心原则

### 1. 最小权限
每个工具只暴露必要的权限，避免过度授权带来的安全风险。

### 2. 容错设计
外部服务会失败，工具调用需要优雅降级：
- 重试机制（指数退避）
- 超时处理
- 备用方案

### 3. 可观测性
工具调用应该有日志和监控：
- 输入输出可追踪
- 失败原因可排查
- 性能可测量

### 4. 渐进增强
不要一开始设计完美的工具，先从最小可用工具开始，逐步扩展。

## 实践案例

OpenClaw 的 Skills 系统是 Harness 工程的典型实现：
- 每个 Skill 定义工具能力
- 工具调用通过 Skills 扩展
- 支持 Cron 定时调用
- 支持多渠道触发

## 相关链接
- [[openclaw-guide|OpenClaw 指南]]
- [[skills-system|Skills 系统]]
- [[claude-code-guide|Claude Code 指南]]
