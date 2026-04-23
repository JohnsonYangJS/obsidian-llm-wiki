---
title: Hermes Agent
tags: [hermes, ai-agent, self-improving]
created: 2026-04-23
updated: 2026-04-23
related: [[claude-code-guide]], [[openclaw-guide]], [[llm-wiki-pattern]], [[harness-engineering]]
---

# Hermes Agent

## 概述
自改进 Agent，GitHub Star 27,000+，发布两个月达到此成就。核心特色是「出厂即带缰绳」——Harness 五组件全部内置。

## 与 Claude Code 的核心区别

| 维度 | Claude Code | Hermes Agent |
|------|-------------|--------------|
| 定位 | 编程工具 | 个人 Agent |
| 记忆 | 单会话 | 三层记忆（工作→情节→语义） |
| 工具 | 按需 | 常驻 MCP |
| 自改进 | 无 | Skill 自动进化 |
| 部署 | 本地 | Docker/VPS |

## 三层记忆系统

### Layer 1：工作记忆
当前会话上下文，类似普通 ChatGPT。

### Layer 2：情节记忆
跨会话的持久状态，包括：
- 用户编码偏好
- 项目结构习惯
- 常用工具链

### Layer 3：语义记忆
从对话中提炼的持久洞察，不记代码变更，只记原则。

## 自改进机制
完成复杂任务后，Hermes 会主动创建/更新 Skill。
- Skill 会越用越好
- 每个 Skill 有使用反馈循环

## 多 Agent 编排
`delegate_task` 支持子 Agent 委派：
- 可设置受限工具集（安全机制）
- 主 Agent 负责协调，不直接修改代码
- 典型场景：调研+执行分离

## 安装方式
- Docker（推荐）：`docker pull nousresearch/hermes-agent:latest`
- VPS：约 $5/月
- 配置：`~/.hermes/config.yaml`

## 参考来源
- raw/Hermes-Agent-从入门到精通-v260407.txt
- raw/Hermes-Agent-The-Complete-Guide-v260407.txt

## 相关
- [[claude-code-guide]] — 编程工具
- [[openclaw-guide]] — 多渠道框架
- [[llm-wiki-pattern]] — 知识库模式
