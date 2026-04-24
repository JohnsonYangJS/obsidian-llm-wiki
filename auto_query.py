#!/usr/bin/env python3
"""
auto_query.py — Wiki 导航式问答（Karpathy 方案）

核心变更：
- 不再使用向量搜索（移除 qmd/JSONL session 逻辑）
- 改为：读 wiki/index.md → 找到相关页面 → LLM 读相关页面 → 直接回答
- 好答案写回到 wiki（更新相关概念页或生成新概念页）
- 不再生成 wiki/queries/ 页面，改为直接更新 wiki/

用法：
    python3 auto_query.py <vault-root> "<question>" [--dry-run] [-v]
"""

import argparse
import datetime as _dt
import json
import re
import subprocess
import sys
import time
from pathlib import Path

# ── MiniMax 配置 ─────────────────────────────────────────────────────────────
MINIMAX_API_KEY = "sk-cp-SUjytMlOmz-9qX73aXQbhNog3hEQmYoLxVff1IkOVFCJ_pia4t0ykTJSgp3bQ3aWvmIyIu-HJvNRCZEXHRTL_rFGARGtSpURNHNunmm5yXTucUaLJDH1uaE"
MINIMAX_BASE = "https://api.minimax.chat/v1"
MODEL = "MiniMax-M2.7-highspeed"

# ── Manifest ─────────────────────────────────────────────────────────────────
MANIFEST_PATH = ".query-manifest.json"


def load_manifest(vault: Path) -> dict:
    p = vault / MANIFEST_PATH
    if p.exists():
        return json.loads(p.read_text())
    return {}


def save_manifest(manifest: dict, vault: Path):
    (vault / MANIFEST_PATH).write_text(json.dumps(manifest, indent=2, ensure_ascii=False))


# ── LLM ───────────────────────────────────────────────────────────────────────

def extract_json(raw: str) -> dict:
    """Extract JSON from LLM response."""
    text = raw.strip()
    for open_tag in ["<thinking>", " Christensen"]:
        close_tag = " </thinking>" if open_tag == "<thinking>" else " Christensen"
        idx = text.rfind(close_tag)
        if idx != -1:
            text = text[idx + len(close_tag):].lstrip()
    for start in [text.find("{"), text.find("｛")]:
        if start == -1:
            continue
        json_str = text[start:]
        count = 0
        end_pos = 0
        for i, c in enumerate(json_str):
            if c in "{[":
                count += 1
            elif c in "}]":
                count -= 1
            if count == 0:
                end_pos = i + 1
                break
        if end_pos > 0:
            try:
                return json.loads(json_str[:end_pos])
            except json.JSONDecodeError:
                pass
    raise ValueError(f"No parseable JSON: {repr(raw[:200])}")


def llm_answer(question: str, wiki_pages: list[dict]) -> dict:
    """
    调用 MiniMax，基于 wiki 页面内容直接回答问题。

    wiki_pages: list of {"title": str, "content": str, "path": str}

    返回：
    {
        "answer": str,           # 直接回答（中文）
        "sources": list[str],    # 引用的页面标题
        "new_insight": bool,    # 是否包含新洞察
        "insight_content": str, # 新洞察内容（如有）
        "update_target": str,   # 应更新的页面标题（如有）
    }
    """
    # 构建上下文
    context_parts = []
    for i, page in enumerate(wiki_pages):
        context_parts.append(f"--- Wiki 页面 {i+1}: {page['title']} ---\n{page['content'][:3000]}")

    context = "\n\n".join(context_parts)

    prompt = f"""你是一个 LLM Wiki 知识库问答助手。请根据以下 Wiki 页面内容，直接回答用户问题。

## 用户问题
{question}

## Wiki 知识库内容

{context}

## 回答要求

1. 直接回答问题，简洁明了
2. 引用相关 Wiki 页面：`[[页面标题]]`
3. 如果 Wiki 中没有足够信息，说明"知识库暂无相关内容"
4. 如果你有新洞察（知识库未覆盖但与问题相关），在 `new_insight` 中说明

请直接输出 JSON：
{{
  "answer": "直接回答内容（100-500字）",
  "sources": ["[[页面标题1]]", "[[页面标题2]]"],
  "new_insight": true或false,
  "insight_content": "新洞察内容（如有）",
  "update_target": "应更新的页面标题（如知识库已有相关页则填标题，否则填空字符串）"
}}

只输出 JSON，不要其他内容。"""

    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,
        "temperature": 0.3,
    })

    for attempt in range(3):
        proc = subprocess.run(
            ["curl", "-s", "-X", "POST", f"{MINIMAX_BASE}/chat/completions",
             "-H", f"Authorization: Bearer {MINIMAX_API_KEY}",
             "-H", "Content-Type: application/json",
             "-d", payload, "--noproxy", "*", "--max-time", "60"],
            capture_output=True, text=True, timeout=65,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"curl rc={proc.returncode}: {proc.stderr}")

        raw = json.loads(proc.stdout)["choices"][0]["message"]["content"]
        try:
            result = extract_json(raw)
            return result
        except ValueError:
            if attempt < 2:
                time.sleep(1)
                continue
            raise RuntimeError(f"JSON parse failed: {raw[:300]}")

    raise RuntimeError("unreachable")


# ── Wiki Navigation ───────────────────────────────────────────────────────────

def extract_wikilinks(text: str) -> list[str]:
    """Extract [[Target]] links from text."""
    return re.findall(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]", text)


def find_related_pages(vault: Path, question: str, max_pages: int = 5) -> list[dict]:
    """
    通过 wiki/index.md 导航找到与问题相关的页面。
    不使用向量搜索，使用关键词匹配。
    """
    index_path = vault / "wiki" / "index.md"
    if not index_path.exists():
        return []

    index_text = index_path.read_text(encoding="utf-8")
    wiki_dir = vault / "wiki"

    # 提取 index 中的所有 wikilink
    links = extract_wikilinks(index_text)

    # 简单关键词匹配：问题中的词与页面标题匹配
    question_lower = question.lower()
    question_words = set(re.findall(r"[\w]{3,}", question_lower))

    scored_pages = []
    for link in links:
        link_clean = link.strip()

        # Try to find the actual file
        for subdir in ("concepts", "entities", "summaries", ""):
            if subdir:
                candidates = [
                    wiki_dir / subdir / f"{link_clean}.md",
                    wiki_dir / subdir / link_clean / "index.md",
                ]
            else:
                candidates = [wiki_dir / f"{link_clean}.md"]

            for candidate in candidates:
                if candidate.exists():
                    text = candidate.read_text(encoding="utf-8", errors="ignore")
                    # Score by title match
                    title_match = sum(1 for w in question_words
                                     if w in link_clean.lower())
                    # Also check if any question word appears in content
                    content_match = sum(1 for w in question_words
                                       if w in text.lower())
                    score = title_match * 3 + content_match
                    scored_pages.append({
                        "title": link_clean,
                        "path": str(candidate.relative_to(vault)),
                        "content": text,
                        "score": score,
                    })
                    break

    # 去重并按分数排序
    seen = set()
    unique_pages = []
    for p in scored_pages:
        if p["path"] not in seen:
            seen.add(p["path"])
            unique_pages.append(p)

    unique_pages.sort(key=lambda x: -x["score"])

    # 返回 top N（跟随一级链接，最多额外读取2层）
    result = []
    for page in unique_pages[:max_pages]:
        result.append({
            "title": page["title"],
            "content": page["content"],
            "path": page["path"],
        })

    return result


def write_insight_to_wiki(vault: Path, insight: str, target_title: str,
                          question: str, answer: str) -> Path | None:
    """
    将新洞察写回到相关 Wiki 页面。
    如果 target_title 非空，更新对应页面；否则在 concepts/ 下新建页面。
    """
    slug = re.sub(r"[^\w\s-]", "", target_title or insight[:30])
    slug = re.sub(r"[\s]+", "-", slug).strip("-")[:50]

    if target_title:
        # 找到并更新现有页面
        for subdir in ("concepts", "entities", "summaries"):
            candidate = vault / "wiki" / subdir / f"{slugify(target_title)}.md"
            if candidate.exists():
                text = candidate.read_text(encoding="utf-8")
                # 在 "## Related" 或末尾追加洞察
                insight_block = f"\n\n## 新洞察\n\n{insight}\n\n> 来源：{question[:50]}...\n"
                if "## Related" in text:
                    text = text.replace("## Related", insight_block + "\n## Related")
                else:
                    text += insight_block
                candidate.write_text(text, encoding="utf-8")
                return candidate
        # 没找到，更新 index 让用户知道
        return None
    else:
        # 新建概念页
        target_dir = vault / "wiki" / "concepts"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{slug}.md"
        date = _dt.date.today().isoformat()

        page = f"""---
title: {slug}
type: concept
tags: []
created: {date}
updated: {date}
related: []
summary: {insight[:200]}
sources: []
generation: auto_query (MiniMax)
---

# {slug}

> 自动生成的洞察页面

## 洞察内容

{insight}

## 来源问题

**Q:** {question}

**A:** {answer[:300]}

---
*由 auto_query.py 自动生成于 {date}*
"""
        target_path.write_text(page, encoding="utf-8")
        return target_path


def slugify(text: str) -> str:
    """Convert title to filename-safe slug."""
    s = re.sub(r"[^\w\s-]", "", text)
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-").lower()[:60]


def append_log(vault: Path, msg: str):
    """Append entry to log/YYYYMMDD.md."""
    today = _dt.date.today().strftime("%Y%m%d")
    log_dir = vault / "log"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"{today}.md"
    now = _dt.datetime.now().strftime("%H:%M")
    entry = f"\n## [{now}] query | {msg}"
    if log_path.exists():
        log_path.write_text(log_path.read_text(encoding="utf-8") + entry, encoding="utf-8")
    else:
        log_path.write_text(f"# {today}\n\n## Daily Log\n{entry}\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("vault", type=Path, nargs="?", default=Path("."))
    parser.add_argument("question", nargs="?", help="要查询的问题（用引号包裹）")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    vault = args.vault.resolve()
    if not vault.exists():
        print(f"ERROR: Vault not found: {vault}", file=sys.stderr)
        sys.exit(2)

    manifest = load_manifest(vault)

    # Interactive mode if no question provided
    if not args.question:
        print("Wiki Navigation Query — Interactive Mode")
        print("=" * 40)
        question = input("请输入问题: ").strip()
        if not question:
            print("No question, exiting.")
            sys.exit(0)
    else:
        question = args.question

    # Skip if already answered recently
    if question in manifest.get("answered", {}):
        if not args.dry_run:
            print(f"[CACHE] 最近已回答过: {manifest['answered'][question]}")
        sys.exit(0)

    if args.verbose:
        print(f"Question: {question}")

    # Step 1: Navigate wiki/index.md to find related pages
    if args.verbose:
        print("Step 1: Reading wiki/index.md to locate relevant pages...")
    related_pages = find_related_pages(vault, question)

    if not related_pages:
        print("知识库暂无相关内容。请先通过 auto_ingest.py 摄入相关资料。")
        sys.exit(0)

    if args.verbose:
        print(f"Found {len(related_pages)} related pages:")
        for p in related_pages:
            print(f"  - [[{p['title']}]] (score: {p.get('score', 0)})")

    # Step 2: LLM reads related pages and answers
    if args.verbose:
        print("Step 2: Calling MiniMax to answer based on wiki pages...")
    try:
        result = llm_answer(question, related_pages)
    except Exception as e:
        print(f"ERROR: LLM answer failed: {e}", file=sys.stderr)
        sys.exit(1)

    answer = result.get("answer", "")
    sources = result.get("sources", [])
    new_insight = result.get("new_insight", False)
    insight_content = result.get("insight_content", "")
    update_target = result.get("update_target", "")

    print("\n" + "=" * 40)
    print("回答：")
    print(answer)
    if sources:
        print(f"\n来源: {', '.join(sources)}")
    print("=" * 40)

    # Step 3: Write back if good answer with new insight
    if new_insight and insight_content:
        print("\n[发现新洞察，正在写回 Wiki...]")
        if update_target:
            path = write_insight_to_wiki(vault, insight_content, update_target, question, answer)
            if path:
                print(f"  → 已更新: {path.relative_to(vault)}")
            else:
                print(f"  → 目标页面未找到，创建新页面")
                path = write_insight_to_wiki(vault, insight_content, "", question, answer)
                print(f"  → 已创建: {path.relative_to(vault)}")
        else:
            path = write_insight_to_wiki(vault, insight_content, "", question, answer)
            print(f"  → 已创建: {path.relative_to(vault)}")

    # Log
    if not args.dry_run:
        manifest.setdefault("answered", {})[question] = answer[:100]
        save_manifest(manifest, vault)
        append_log(vault, f"QUERY - Q: {question[:50]}... | sources: {', '.join(sources) if sources else 'none'}")


if __name__ == "__main__":
    main()
