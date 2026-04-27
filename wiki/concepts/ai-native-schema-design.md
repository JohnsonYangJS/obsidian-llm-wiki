---
title: ai-native-schema-design
type: concept
category: articles
tags: [LLM语义空间, Schema设计, 结构化查询, 领域知识建模]
created: 2026-04-27
updated: 2026-04-27
related: [[[LLM Wiki 模式]]]
sources: [file:///Users/txyjs/Documents/Obsidian Vault/raw/email-20260427-转发-都ai原生产品了为什么还需要schema.txt]
generation: LLM (MiniMax-M2.7-highspeed)
---

# ai-native-schema-design

> 探讨在AI原生时代，Schema的设计理念和功能如何根本性转变。旧世界Schema是输入端的强制过滤器，由机器能力下限决定；新世界LLM可以在连续向量空间处理语义，Schema的功能转变为：1) 作为查询的脚手架而非输入过滤器，让结构化join和聚合成为可能；2) 判断力的实时可视化，与领域知识共时演化而非冻结；3) 闭环学习的支点，提供离散化类型系统使归纳学习成为可能。核心洞察：离散是计数的前提

## 概述

在AI原生产品时代，Schema的设计理念需要根本性转变。旧世界Schema是输入端的强制过滤器，由机器处理结构化数据的能力下限决定；LLM时代，Schema的功能从"限制输入"变为"扩展输出"、"承载实时判断力"和"支撑闭环学习"。

## 旧世界Schema的局限

### 存在的理由
机器只能处理结构化数据。Schema必须先把世界裁成能装下的形状，任何不符合Schema的现实都被截断、丢弃、强行变形。

### 冻结的代价
- 判断力继续演化，Schema在里面冻着
- 新方法被塞进老Schema字段里
- 或在SaaS之外平行跑Excel
- 判断力的一部分被Schema排斥到外部

## 新世界Schema的三大功能

### 1. Query的脚手架

Schema不再是"能不能存进去"的门槛，而是"能不能被有意义地查询"的脚手架。

**关键对比**：
- 向量库问答：LLM给出看似合理但不可验证、不可累积、不可比较的答案
- 结构化Join：可以问"所有FunnelState=trailing_no_conversion的租户，按Outcome评分排序，哪种Intervention历史胜率最高"

**为什么需要结构化**：LLM处理的是概率分布，擅长语义插值，不擅长离散事实的精确操作。计数、求和、过滤、join、聚合需要二值精度。

### 2. 判断力的可视化

- 旧世界：判断力先在，Schema是固化产物，一旦刻进去就冻结
- 新世界：Schema是活体，与判断力共时演化

**具体动作**：
- 每个Schema字段附带"为什么是这样切"的元数据
- Schema有版本号，记录判断力演化轨迹
- 建立schema_proposal流程，允许每次访谈/复盘产生Schema修改提案

### 3. 闭环学习的支点

**Schema提供离散的re-identification**：
- LLM的连续相似性是程度问题（0.87还是0.91），不回答"是不是同一回事"
- 学习需要对类型做归纳，需要明确边界的桶才能算胜率
- 胜率 = 成功数 / 总数，需要二值答案

**层级关系**：离散 → 计数 → 归纳 → 学习

**Schema配给LLM外置的categorical perception系统**：LLM负责理解模糊输入，Schema负责把理解结果离散化成可归纳的类型。

## 核心原则

> "这件事过去一直是这么做的，但那是因为旧物理。新物理下还应该这么做吗？"

Schema不是判断力凝固后的化石，而是判断力的实时形状。Rule约束行为，行为改写Rule——工程级别的自反系统，是这一代AI系统跟过去所有软件最深的不同。

## Related

- [[LLM Wiki 模式]]

## Sources

- [email 20260427 转发 都ai原生产品了为什么还需要schema](file:///Users/txyjs/Documents/Obsidian Vault/raw/email-20260427-转发-都ai原生产品了为什么还需要schema.txt)

---
*由 auto_ingest.py 自动生成于 2026-04-27*
