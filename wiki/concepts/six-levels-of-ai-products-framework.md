---
title: six-levels-of-ai-products-framework
type: concept
category: articles
tags: [AI产品六层次, AI Architect, Runtime vs 开发方式, Prompt Wrapper]
created: 2026-04-26
updated: 2026-04-26
related: [[[Hermes Agent]], [[Claude Code 指南]], [[MCP 模型上下文协议]]]
sources: [file:///Users/txyjs/Documents/Obsidian Vault/raw/email-20260427-转发-用ai产品的六个层次分类ai-architect学员项.txt]
generation: LLM (MiniMax-M2.7-highspeed)
---

# six-levels-of-ai-products-framework

> 本文介绍了AI产品的六个层次分类框架，并基于该框架对AI Architect课程的45个学员项目进行了系统分类。该框架的核心原则是「看runtime，不看开发方式」，关注用户使用时AI在runtime里承担了什么职责。六个层次从L0的「非AI产品」到L6的「AI-native产品」，代表了AI应用深度由浅入深的演进路径。分类结果显示，45个项目中L6最多（17个），L3次之（10个），说明学员项目

## 概述

AI产品的六个层次是一种用于评估AI产品成熟度的分类框架，核心原则是「看runtime，不看开发方式」——关注用户使用时AI在runtime里承担了什么职责，而非开发过程中是否使用了AI。

## 六个层次定义

| 层级 | 名称 | 描述 |
|------|------|------|
| L0 | AI-assisted building | 非AI产品，AI参与开发但用户使用时无AI runtime |
| L1 | Prompt Wrapper | 薄AI工具，将模型调用包装为低摩擦入口 |
| L2 | Grounded AI / RAG | 带知识的AI应用，结合检索增强 |
| L3 | Tool-using AI | 能调用工具的AI应用 |
| L4 | LLM Workflow | 固定流程里的AI |
| L5 | Agentic Core | 真正的智能体核心 |
| L6 | AI-native Product/System | 真正落地的AI系统 |

## 学员项目分类结果

对45个AI Architect学员项目的分类结果：
- **L0**: 5个（AI辅助构建/非AI产品）
- **L1**: 1个（Prompt Wrapper，包括作者的English Editor）
- **L2**: 3个（Grounded AI / RAG应用）
- **L3**: 10个（Tool-using AI应用）
- **L4**: 4个（LLM Workflow）
- **L5**: 5个（Agentic Core）
- **L6**: 17个（AI-native产品/系统）

## 关键洞见

1. **分类维度唯一性**：该框架只衡量「AI应用深度」，需求、解决方案、产品设计、robustness等虽重要但不在评估范围内

2. **同一产品的不同层级**：同样是浏览器插件，根据AI在用户使用时的角色不同，可被分为L0（仅开发辅助）、L3（调用模型解释内容）或L5/L6（主动研究目标）

3. **L1不等于低级项目**：English Editor作为L1项目，因其将高频、明确、模型擅长的任务包装成低摩擦入口，被认为是好的L1设计

## 与传统分类的区别

该框架不关注UI形式或模型新旧，而聚焦于AI是否进入用户真实工作流、是否承担判断/生成/行动职责。

## Related

- [[Hermes Agent]]
- [[Claude Code 指南]]
- [[MCP 模型上下文协议]]

## Sources

- [email 20260427 转发 用ai产品的六个层次分类ai architect学员项](file:///Users/txyjs/Documents/Obsidian Vault/raw/email-20260427-转发-用ai产品的六个层次分类ai-architect学员项.txt)

---
*由 auto_ingest.py 自动生成于 2026-04-26*
