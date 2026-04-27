---
title: ai-assisted-personal-website-setup
type: summary
category: articles
tags: [AI辅助编程, 个人网站, 静态站点托管, 域名注册]
created: 2026-04-24
updated: 2026-04-24
related: [[[Claude Code 指南]], [[OpenClaw 指南]]]
sources: [file:///Users/txyjs/Documents/Obsidian Vault/raw/email-20260427-转发-个人网页ai-辅助编程的第一次尝试.txt]
generation: LLM (MiniMax-M2.7-highspeed)
---

# ai-assisted-personal-website-setup

> 本文记录了使用AI辅助编程搭建个人网站的全过程。作者Dahui Xu在约两小时内完成了www.dahui.ai网站的上线，涵盖域名注册（.ai后缀）、Cloudflare Pages托管、GitHub仓库管理、静态站点构建及双语i18n支持等环节。教程详细说明了如何通过Git集成实现自动化部署，以及如何通过集中式myinfo.md管理个人信息，保持中英文内容一致性。对于希望快速搭建个人作品集或简历

## 概述

本文记录了使用AI辅助编程搭建个人网站的完整流程。作者Dahui Xu在约两小时内完成了www.dahui.ai的上线，涵盖从域名注册到网站发布的全链路。

## 域名注册与配置

选择.dhui.ai或dahui.ai作为域名。.ai是安圭拉国家/地区顶级域，全球多个注册商（如Namecheap、GoDaddy、Porkbun、Cloudflare Registrar）均有售。注册流程与普通域名类似，需注意首年与续费价格差异。

域名不等于商标，若做公开品牌需注意商标冲突。注册费用用于在全局DNS中登记使用权，属于按年续租而非一次性购买。

## 网站托管方案

采用Cloudflare Pages进行托管，可上传zip文件或通过npx wrangler pages deploy命令部署。注册域名与托管服务可分开管理。

### 静态站+Git持续部署

将Git仓库连接至Cloudflare Pages：
1. 在Workers与Pages中连接Git仓库
2. 设置构建命令（纯静态可留空）
3. 指定构建输出目录（通常为/或public/）
4. 在自定义域名中添加dahui.ai

每次推送至绑定分支会自动重新部署。

## GitHub仓库管理

创建仓库时注意：
- 用户站点根域可用<用户名>.github.io
- 私有仓库Pages规则以GitHub当前说明为准
- 若本地已有目录，创建仓库时不要勾选README、.gitignore或许可证，避免首次推送冲突

首次推送命令：
```bash
git remote add origin https://github.com/<user>/<repo>.git
git branch -M main
git push -u origin main
```

## 个人信息管理

建立集中式myinfo.md源文件存放事实信息：
- 姓名与简介
- 工作经历与教育背景
- 技能列表
- 邮箱与社交链接

该文件作为内容参考，站点在i18n字符串与链接中与之对齐。

## 国际化(i18n)实现

页眉提供EN/中文切换。整页内容通过行内i18n（data-i18n/data-i18n-attr）与STR字典中的en、zh键值切换，并写入localStorage保持语言偏好。

双语正文需同时修改STR.en与STR.zh中同一键，HTML中留占位由JS加载时替换。

## 关键要点

1. AI辅助可显著提升建站效率（两小时完成）
2. 静态站点+Git实现自动化部署
3. 集中式信息管理便于维护一致性
4. 双语支持提升网站可访问性

## Related

- [[Claude Code 指南]]
- [[OpenClaw 指南]]

## Sources

- [email 20260427 转发 个人网页ai 辅助编程的第一次尝试](file:///Users/txyjs/Documents/Obsidian Vault/raw/email-20260427-转发-个人网页ai-辅助编程的第一次尝试.txt)

---
*由 auto_ingest.py 自动生成于 2026-04-24*
