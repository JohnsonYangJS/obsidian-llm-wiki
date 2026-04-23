---
title: "我用OpenClaw，把flomo、Obsidian、Get笔记和ima知识库串起来了！"
source: "https://mp.weixin.qq.com/s/B1HniYffwJiZLKpW-njXsg"
author:
  - "[[澍登]]"
published:
created: 2026-04-23
description: "书是音符，谈话才是歌，这里是澍登说。"
tags:
  - "clippings"
---
澍登 *2026年3月28日 17:11*

*书是音符，谈话才是歌，这里是澍登说。*

这是本公众号的第428篇原创文章

今天又搞定一件事：

把 flomo 里的闪念笔记，经过 AI 整理，

最终推送到 Obsidian、ima、Get笔记三个地方。

记录一下，顺便给想搞同款工作流伙伴参考，

此前已完成OpenClaw同步文件至ima知识库和Get笔记。

[「三虾协同」，多Agent，一部手机搞定！](https://mp.weixin.qq.com/s?__biz=MzkyNzY3NjExMQ==&mid=2247489357&idx=1&sn=b92ce4542af13ed615eb5593ea91f4af&scene=21#wechat_redirect)

[用OpenClaw一周，我却坐回了电脑前](https://mp.weixin.qq.com/s?__biz=MzkyNzY3NjExMQ==&mid=2247489364&idx=1&sn=7764b3015ad119a2ee4aef3a8d7a3b1d&scene=21#wechat_redirect)

[给4只龙虾建立“共同记忆”，方法可复制！](https://mp.weixin.qq.com/s?__biz=MzkyNzY3NjExMQ==&mid=2247489368&idx=1&sn=183bb9b289d1d83831df70da8115b742&scene=21#wechat_redirect)

---

## 一、先说我想解决的问题

我的笔记现在分散在四个地方：

- **flomo：碎片想法、随手闪念**
- **Obsidian：本地结构化知识库**
- **ima：AI知识库，在线知识沉淀**
- **Get笔记：数据入口，多态解析内容汇集在这里**

问题是：这四个地方基本不互通。

flomo 里有好东西，但它就躺在那里，跟 Obsidian 是两个孤岛。

今天想打通的核心路径就一条：

**flomo 的闪念 → 经过 AI 整理 → 同步到其他三端** 。

---

## 二、方案选型：

## 先踩了一个假设的坑

一开始以为 flomo 有"读取笔记API"，毕竟很多工具都有。

查了文档才发现：

**flomo 的官方 API 是单向写入的** ——只能往 flomo 里写，

不能从 flomo 读出来。

而MCP 方案倒是可以双向，但要求：

- MAX会员(付费)
- 去后台生成 MCP Token
- 配置到 AI 工具里

不是说麻烦，是说 **今天想跑通不等会员到位** ，需要一个备选方案。

**备选方案：导出 HTML 文件，让AI解析**

flomo 支持导出全量或部分数据，格式是 HTML。

“导出 → 扔给AI → 解析 → 写入”

步骤多了一步手动操作，但今天能跑通。

先跑通，再优化，符合「最小原则」。

---

## 三、整个工作流最终长这样

```
今天的实际效果：
```
```
flomo 导出 → HTML 压缩包（手动操作）
     ↓
OpenClaw 分析：按主题归类 + 提炼选题（自动）
     ↓
生成结构化 .md 文件 → 写入 Obsidian（自动）
     ↓
同时推送至 IMA + Get笔记（API 自动）
```
![图片](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)
- 增量8条flomo闪念 → 整理成3个主题模块+10个可用选题，
- 一份文档落地 Obsidian，并同步到 ima知识库和Get 笔记，
- 而手动操作只有一个：从 flomo 导出 ZIP 文件。

·······END·······

![图片](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)

限免写作&编程交流群，扫码领AI资料。

![图片](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)

欢迎来到我的免费星球，每日原创内容及思考 https://t.zsxq.com/LhEbJ

![图片](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)

**往期推荐：**

**【一人企业商业化】**

**[一人企业商业化，1套中期管理组合打法](http://mp.weixin.qq.com/s?__biz=MzkyNzY3NjExMQ==&mid=2247484449&idx=1&sn=dae9e407d4f4980eb7dd3f459d2f654d&chksm=c2252781f552ae976db8044af13016b244ee42fc53c55e9a1a0d9b0f7a7e787af91d2c1cedae&scene=21#wechat_redirect)  
**

**[一人企业商业化，你为什么不赚钱](http://mp.weixin.qq.com/s?__biz=MzkyNzY3NjExMQ==&mid=2247484386&idx=1&sn=f7f46eaa069b2422315a66ae3de00a2a&chksm=c2252042f552a9543dbbb7d8e71f2c15dc864a8cdbfd7753221941b2d1e41824864206659333&scene=21#wechat_redirect)  
**

**[一人企业商业化，2点实践总结](http://mp.weixin.qq.com/s?__biz=MzkyNzY3NjExMQ==&mid=2247484292&idx=1&sn=23574ef3c2fbcca1a25e5127c3fe801b&chksm=c2252024f552a9322c2b0dfee16681c21474b7498a7a14277e0314f7634a7fa207d812111f56&scene=21#wechat_redirect)**

**【自由职业】**

**[80后，自由职业3个月，自媒体变现破局之道](http://mp.weixin.qq.com/s?__biz=MzkyNzY3NjExMQ==&mid=2247485068&idx=1&sn=b563f340a28a490ef0bebd3a632a5292&chksm=c225252cf552ac3a81c4e03e110bc613379ffd4226cf42e0e161645eac721b2243035a27e96a&scene=21#wechat_redirect)  
**

**[中年自由职业者，做好“跟随”很重要](http://mp.weixin.qq.com/s?__biz=MzkyNzY3NjExMQ==&mid=2247485031&idx=1&sn=4a2091ed6987513f0698eafec7361acb&chksm=c22525c7f552acd11e187ceab700ce95701e541534780bf134994893064db76956a76735dd67&scene=21#wechat_redirect)  
**

**[自由职业者，该如何赚钱](http://mp.weixin.qq.com/s?__biz=MzkyNzY3NjExMQ==&mid=2247484979&idx=1&sn=c00f14505b137999164f93a5eaca1c44&chksm=c2252593f552ac8542061055773b407dacd035cc58d4abb94f1a68f129f23e53967d86a69f83&scene=21#wechat_redirect)**

**【个人IP】**

**[从零开始，个人品牌如何定位](http://mp.weixin.qq.com/s?__biz=MzkyNzY3NjExMQ==&mid=2247485530&idx=1&sn=c267742a3564b9c3c01afaeaaa20b453&chksm=c2252bfaf552a2ece7aabeeabc9ed0155cf32a8077278b3d73a23d3210a56de5bef152b6e9ff&scene=21#wechat_redirect)**

**[公众号写作，打造个人IP，让自己成为案例！](http://mp.weixin.qq.com/s?__biz=MzkyNzY3NjExMQ==&mid=2247485510&idx=1&sn=b41aeee93d7efbdcc77d9d180c2fa823&chksm=c2252be6f552a2f00cf4d38656a434ca044ad8af9166f2a307279bec7fd0434906bbfd4b9251&scene=21#wechat_redirect)**

**[1024，打造个人IP定位: "产品思维"与"项目思维"](http://mp.weixin.qq.com/s?__biz=MzkyNzY3NjExMQ==&mid=2247485164&idx=1&sn=368e185d6e3dc586d036ae729481dd28&chksm=c225254cf552ac5a0315f7800010bd252b1044c6e329b0a452e4d77a780e263d4fb31baac0ca&scene=21#wechat_redirect)**

**【自我介绍】**

**[这是澍登的自我介绍（第1版）](http://mp.weixin.qq.com/s?__biz=MzkyNzY3NjExMQ==&mid=2247483929&idx=1&sn=819fca0e6a6f73699bf07d9026fb61d1&chksm=c22521b9f552a8af2905c4bdd4a10a5a7aad1ba054a3ee2e0fea99c5b818d76b4b13136bd965&scene=21#wechat_redirect)**

**点击👇🏻👇🏻卡片"澍登说"，关注公众号，随时与作者交流，道是“树灯千光照，明月逐人来”！**

一人企业复利商业化 · 目录

作者提示: 个人观点，仅供参考

继续滑动看下一个

澍登说

向上滑动看下一个

解释