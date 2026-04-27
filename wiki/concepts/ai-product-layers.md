---
title: ai-product-layers
type: concept
category: articles
tags: [AI-assisted building vs AI runtime, AI产品六层模型, Prompt Wrapper, RAG (检索增强生成)]
created: 2026-04-26
updated: 2026-04-26
related: [[[Hermes Agent]], [[MCP 模型上下文协议]], [[LLM Wiki 模式]], [[Claude Code 指南]]]
sources: [file:///Users/txyjs/Documents/Obsidian Vault/raw/email-20260427-转发-ai产品的六个层次.txt]
generation: LLM (MiniMax-M2.7-highspeed)
---

# ai-product-layers

> 本文阐述了 AI 产品的六个层次与人类 AI 能力的四个层级。核心论点是「会用 AI coding 做东西，不等于会做 AI 系统」——前者是 AI 帮你写代码，后者是你设计系统让 AI 在用户使用时承担理解、判断、行动、记忆、协作和交付。AI 产品六层从浅到深依次为：Prompt Wrapper（薄 AI 工具）、Grounded AI/RAG（带知识的 AI 应用）、Tool-using AI

## 核心论点

会用 AI coding 做出一个东西，不等于会设计一个 AI 系统。前者是 AI 帮你写代码；后者是你设计一个系统，让 AI 在用户使用时承担理解、判断、行动、记忆、协作和交付的职责。

## AI-assisted Building vs AI Runtime

**AI-assisted building**：AI 在开发过程中帮你造软件（如用 Cursor 写代码）。

**AI runtime**：AI 在产品运行过程中替用户工作（系统读取上下文、调用工具、做决策）。

判断一个东西是不是 AI 系统，不看开发时有没有用 AI，而看**用户使用时 AI 有没有参与 runtime**。

## AI 产品的六个层次

| 层次 | 名称 | 描述 |
|------|------|------|
| 1 | Prompt Wrapper | 薄 AI 工具，用户输入 → prompt → LLM → 输出。如标题生成器、邮件润色器 |
| 2 | Grounded AI / RAG | 带知识的 AI 应用，AI 能检索文档、知识库、数据库再回答。如公司知识库助手 |
| 3 | Tool-using AI | 能调用工具的 AI，AI 不只回答，还能调用 API、查日历、更新 CRM |
| 4 | LLM Workflow | 固定流程里的 AI，按步骤完成分类、检索、判断、生成、审批 |
| 5 | Agentic Core | 真正的智能体核心，AI 能 plan → act → observe → update state → continue/stop |
| 6 | AI-native Product | 真正落地的 AI 系统，有低摩擦交互、上下文智能、记忆、权限、主动触发 |

## 人类 AI 能力的四个层级

| 层级 | 名称 | 关键词 | 能力描述 |
|------|------|--------|----------|
| L3 | AI Consumer | Chatting | 把 AI 当更聪明的 Google，主要消费模型输出 |
| L4 | AI Tinkerer / Vibe Coder | One-off | 用 AI coding 做 demo、小工具，但常停留在 happy path |
| L5 | AI Builder | Reliability & Iteration | 能构建可靠 workflow，懂 context engineering、evaluation |
| L6 | AI Architect | Orchestration & Integration | 能设计 agentic system，整合模型、工具、数据、记忆、评估 |

### 本质变化

- L3：我会问 AI
- L4：我会让 AI 帮我做一个东西
- L5：我会把 AI 放进一个可靠流程
- L6：我会设计一个 AI 驱动的系统

## 行业框架参考

- **Anthropic《Building Effective Agents》**：区分 workflow（预定义路径）和 agent（LLM 动态决定流程）
- **OpenAI《A practical guide to building agents》**：Agent 关键在于 LLM 能管理工作流执行、做决策、调用工具、判断任务完成
- **Google Cloud**：成熟 agent 包含 models、grounding、tools、data architecture、orchestration、runtime

## 核心结论

真正的壁垒不是「会不会调用模型」，而是能不能把模型放进真实工作流，并让它**稳定、可控、可评估、可迭代、可主动运行**。最终目标不是「我会用 AI」，而是：我能设计一个 AI 系统，让它在真实世界里可靠地替我工作。

## Related

- [[Hermes Agent]]
- [[MCP 模型上下文协议]]
- [[LLM Wiki 模式]]
- [[Claude Code 指南]]

## Sources

- [email 20260427 转发 ai产品的六个层次](file:///Users/txyjs/Documents/Obsidian Vault/raw/email-20260427-转发-ai产品的六个层次.txt)

---
*由 auto_ingest.py 自动生成于 2026-04-26*
