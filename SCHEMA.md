# SCHEMA.md — 页面模板规范

## 标准 Wiki 页面模板

```markdown
---
title: 页面标题
tags: [tag1, tag2]
created: YYYY-MM-DD
updated: YYYY-MM-DD
related: [[相关页面1]], [[相关页面2]]
---

# 页面标题

## 概述
（一句话说明这是什么）

## 核心要点
- 要点 1
- 要点 2
- 要点 3

## 详细内容

## 相关链接
- [[相关主题1]]
- [[相关主题2]]

## 参考来源
- raw/原始素材文件名
```

## 标签规范
- 工具类：`#claude-code`, `#hermes`, `#openclaw`, `#obsidian`
- 概念类：`#llm-wiki`, `#knowledge-management`, `#agent`
- 主题类：`#polymarket`, `#coding`, `#productivity`

## 命名规范
- 文件名用英文或拼音，页面标题可用中文
- 概念页用 `PascalCase` 或全小写加连字符
- 示例：`claude-code-guide.md`、`llm-wiki-pattern.md`
