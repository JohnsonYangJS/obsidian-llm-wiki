---
title: cli-to-service-daemon
type: concept
category: articles
tags: [Claude Code CLI, Stream JSON, Child Process Management, Session Lifecycle]
created: 2026-04-24
updated: 2026-04-24
related: [[[Claude Code 指南]], [[MCP 模型上下文协议]]]
sources: [file:///Users/txyjs/Documents/Obsidian Vault/raw/email-20260427-转发-from-cli-tool-to-controllab.txt]
generation: LLM (MiniMax-M2.7-highspeed)
---

# cli-to-service-daemon

> 本文来自 Superlinear Academy，探讨如何将 Claude Code 从交互式 TUI 工具转变为可控的持久化服务。通过 --input-format stream-json 和 --output-format stream-json 标志实现 JSON 流式通信，使用 Node.js child_process 模块管理 Claude 子进程，解析 system.init、ass

## 概述

本文介绍如何将 Claude Code 从交互式 TUI 工具转换为可编程控制的持久化服务，实现与其他系统的集成与编排。

## 核心技术方案

### Stream JSON 模式

Claude CLI 支持通过 `--input-format stream-json` 和 `--output-format stream-json` 标志进入机器对机器通信模式：

```bash
cat | claude \
  --dangerously-skip-permissions \
  --output-format stream-json \
  --input-format stream-json \
  --model sonnet | cat
```

输入输出均为换行分隔的 JSON 对象：

```json
{"type":"user","message":{"role":"user","content":[{"type":"text","text":"hello"}]}}
```

### 事件类型

- **system.init**: 会话初始化，提供 session_id
- **assistant**: 代理响应，包含 text、thinking、tool_use
- **result**: 当前轮次结束
- **rate_limit_event**: 限流事件

## 子进程管理

使用 Node.js `child_process` 模块管理 Claude 进程：

```javascript
const proc = spawn("claude", CLAUDE_ARGS, {
  stdio: ["pipe", "pipe", "pipe"],
});

proc.stdout.on("data", (chunk) => {
  // 解析 JSON 行
  for (const line of lines) {
    const ev = JSON.parse(line);
    // 处理不同事件类型
  }
});
```

## 会话生命周期

会话是生命周期而非聊天日志。创建新对话需要终止旧进程并启动新进程：

```javascript
async function handleNew() {
  await gracefulStop(proc);
  proc = spawnClaude();
}
```

支持 `--resume <session-id>` 恢复历史会话上下文。

## 构建 Daemon 四步骤

1. **进程控制**: 将 Claude CLI 转换为托管子进程
2. **WebSocket 桥接**: 连接本地代理到远程服务器
3. **协议标准化**: 抽象掉厂商特定的事件格式
4. **工具集成**: 使用 MCP 添加自定义能力

## Related

- [[Claude Code 指南]]
- [[MCP 模型上下文协议]]

## Sources

- [email 20260427 转发 from cli tool to controllab](file:///Users/txyjs/Documents/Obsidian Vault/raw/email-20260427-转发-from-cli-tool-to-controllab.txt)

---
*由 auto_ingest.py 自动生成于 2026-04-24*
