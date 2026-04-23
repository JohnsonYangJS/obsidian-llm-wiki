---
title: summaries/赖翔-llm-wiki模式
type: summary
source_type: article
date: 2026-04-2
ingested: 2026-04-23
tags: [wiki, title, 复刻, 大神的]
---

# 赖翔 LLM Wiki模式

**Source**: file:///Users/txyjs/Documents/Obsidian Vault/raw/articles/赖翔-LLM-Wiki模式.md · 2026-04-2

## Key takeaways

- wiki · title · 复刻 · 大神的 · 模式

## Summary

title: "复刻 Karpathy 大神的 LLM Wiki 模式：用 OpenClaw + Obsidian 打造\"会自己生长\"的知识库"

source: "https://mp.weixin.qq.com/s/1fQmshZCYMenfFuWxOjE6w"

created: 2026-04-23

description: "2026 年 4 月初，Andrej Karpathy 发了一条推特，提出了一个让无数 AI 玩家兴奋的新模式："

1. 1. **Ingest（摄入）** — 放入新文章/数据 → LLM 分析 → 自动更新 Wiki + 索引 + 日志

2. 2. **Query（查询）** — 你提问 → LLM 搜索 Wiki → 回答 → 好的答案自动存为新 Wiki 页

3. 3. **Lint（健康检查）** — 定期检查矛盾、孤儿页、过时声明、缺失引用

- • **`index.md`** — 内容导向索引，LLM 查询时先读这个文件定位相关页面

- • **`log.md`** — 追加式操作日志，固定前缀格式，可用 Unix 工具解析

## Concepts introduced / referenced

[[wiki]] · [[title]] · [[复刻]] · [[大神的]] · [[模式]]
