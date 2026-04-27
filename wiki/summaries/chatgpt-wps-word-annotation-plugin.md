---
title: chatgpt-wps-word-annotation-plugin
type: summary
category: articles
tags: [ChatGPT 辅助开发, WPS/Word VBA 宏, 文档多层级标注模式, 提示工程]
created: 2026-04-24
updated: 2026-04-24
related: [[[Claude Code 指南]], [[OpenClaw 指南]], [[email 20260424 转发 pm copilot我尝试为自己打造的agent]]]
sources: [file:///Users/txyjs/Documents/Obsidian Vault/raw/email-20260427-转发-我用chatgpt一个下午把word文档根据不同重要程.txt]
generation: LLM (MiniMax-M2.7-highspeed)
---

# chatgpt-wps-word-annotation-plugin

> 一位设计师（非开发者）使用 ChatGPT 一下午时间，成功为 WPS/Word 文档制作了不同重要程度标注模式的插件。该工具允许用户预设多种强调格式（如文字加粗、红色、浅红底色等层级），并像 Word 标题样式一样一键调用，省去重复设置格式的繁琐操作。文章详细记录了作者从提出需求、与 AI 反复沟通、克服技术障碍（如 VBA 环境切换、宏文件配置、WPS 限制等）到最终完成 MVP 的完整过程，

## 项目背景

作者是 Word/WPS 的重度用户，习惯用不同标注来区分笔记的重要程度层级，如：
- 最高级：红色文字 + 加粗 + 浅红底色
- 中级：黄色底色
- 基础：普通加粗

传统方式每次标注都需要重复操作：选中文字 → 加粗 → 选择文字颜色 → 选择底色，效率低下。

## 解决方案

作者希望实现类似「标题样式」的一键标注功能——预设好不同层级的强调格式后，直接选择调用。

## 开发过程

### 第一阶段：初步尝试与挫折

作者向 ChatGPT 描述需求后，AI 给出了三个技术方案，但信息过于宽泛，包含大量专业术语，导致非技术背景的作者难以理解，一度想放弃。

### 第二阶段：改进提问方式

作者反思后发现问题出在提问质量上。通过查找资料优化提问模板，将需求拆解为：背景、目标、可性行判断、实现路径对比、风险与难点、工作量预估等结构化内容。改进后的提问获得了更清晰、可操作的答案。

### 第三阶段：逐步实现

- 使用 VBA 宏方案（需切换到 VB 环境）
- 解决文档保存和宏文件配置问题
- 成功实现核心功能

### 遇到的限制

- WPS 不支持 ActiveX 按钮面板
- WPS 不支持直接设置快捷键列表

虽然部分功能受限，但核心目标已达成。

## 关键经验总结

1. **提问质量决定答案质量**：不要随意聊天，要有结构化的问题描述
2. **持续反馈**：遇到不懂的概念立即追问，可要求 AI 用小白能理解的方式解释
3. **不放弃**：AI 会持续帮助，直到问题解决
4. **MVP 思维**：先走通核心功能，附加功能可后续迭代

## Related

- [[Claude Code 指南]]
- [[OpenClaw 指南]]
- [[email 20260424 转发 pm copilot我尝试为自己打造的agent]]

## Sources

- [email 20260427 转发 我用chatgpt一个下午把word文档根据不同重要程](file:///Users/txyjs/Documents/Obsidian Vault/raw/email-20260427-转发-我用chatgpt一个下午把word文档根据不同重要程.txt)

---
*由 auto_ingest.py 自动生成于 2026-04-24*
