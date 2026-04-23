---
title: 所有摘要列表
tags: dataview, query
---

## 所有 Summary 摘要页

```dataview
TABLE title, date, ingested, tags
FROM "wiki/articles/summaries"
SORT ingested DESC
```

## 所有概念页

```dataview
TABLE title, type
FROM "wiki"
WHERE type = "concept" OR (type = "overview")
SORT file.ctime DESC
```

## 最近入库的文章

```dataview
TABLE title, date, source_type
FROM "wiki/articles/summaries"
WHERE ingested
SORT ingested DESC
LIMIT 10
```

## 按标签统计

```dataview
TABLE length(rows) as Count
FROM "wiki/articles/summaries"
GROUP BY tags
SORT Count DESC
```
