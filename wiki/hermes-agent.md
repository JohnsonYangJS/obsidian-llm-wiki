---
title: Hermes Agent
tags: [hermes-agent, ai-agent, self-improvement, memory]
created: 2026-04-23
updated: 2026-04-23
related: [[claude-code-guide]], [[llm-wiki-pattern]], [[openclaw-guide]]
sources: [raw/Hermes-Agent-The-Complete-Guide-v260407.pdf]
---

# Hermes Agent

> 自改进 Agent，带三层记忆系统，能够从历史交互中持续学习和优化。

## 概述
Hermes Agent 是一种自改进型 AI Agent，通过记忆系统积累经验，逐步提升任务完成质量。其核心创新在于三层记忆架构：工作记忆（短期上下文）、情境记忆（会话历史）、长期记忆（跨会话知识）。

## 三层记忆系统

- **工作记忆**：当前会话内的上下文，Agent 实时使用
- **情境记忆**：最近会话的摘要，帮助 Agent 理解用户偏好
- **长期记忆**：持久化知识，通过向量检索召回

## 自改进机制

Agent 在每次任务完成后评估表现，将有效策略记录到长期记忆，供未来类似任务参考。随时间推移，Agent 越来越擅长处理用户的个性化需求。

## 相关链接
- [[llm-wiki-pattern|LLM Wiki 模式]] — 知识管理维度的自改进
- [[openclaw-guide|OpenClaw 指南]] — 支持记忆系统的 Agent 框架
- [[claude-code-guide|Claude Code 指南]] — 编程场景的 Agent
