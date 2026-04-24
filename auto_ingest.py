#!/usr/bin/env python3
"""
auto_ingest.py — LLM 驱动的知识库摄入脚本（Karpathy 方案）

核心变更：
- 不再使用 TF-IDF 生成 summary，改为调用 MiniMax-M2.7-highspeed 生成结构化 Wiki 页面
- 生成位置：wiki/concepts/、wiki/entities/、wiki/summaries/
- 更新 wiki/index.md（增量添加链接）
- 追加 log/YYYYMMDD.md

用法：
    python3 auto_ingest.py <vault-root> [--dry-run] [-v]
"""

import argparse
import datetime as _dt
import hashlib
import json
import math
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

# ── MiniMax 配置 ─────────────────────────────────────────────────────────────
MINIMAX_API_KEY = "sk-cp-SUjytMlOmz-9qX73aXQbhNog3hEQmYoLxVff1IkOVFCJ_pia4t0ykTJSgp3bQ3aWvmIyIu-HJvNRCZEXHRTL_rFGARGtSpURNHNunmm5yXTucUaLJDH1uaE"
MINIMAX_BASE = "https://api.minimax.chat/v1"
MODEL = "MiniMax-M2.7-highspeed"

# ── Stopwords（仅用于关键词提取辅助，LLM 生成不再是它）─────────────────────────
STOPWORDS = {
    "的", "了", "和", "是", "在", "就", "都", "而", "及", "与",
    "着", "或", "一个", "没有", "我们", "你们", "他们", "这个",
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would",
    "can", "could", "should", "may", "might", "must",
    "and", "or", "but", "if", "then", "when", "this", "that",
    "not", "no", "for", "so", "as", "at", "by", "from",
    "in", "of", "on", "to", "with", "about", "into",
}

NGRAM_RE = re.compile(r"[\u4e00-\u9fff]{2,}|[\w]{4,}")


def tokenize(text: str) -> list[str]:
    """Strip frontmatter and tokenize."""
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)
    tokens = NGRAM_RE.findall(text.lower())
    return [t for t in tokens if t.lower() not in STOPWORDS and len(t) > 1]


def build_tfidf(corpus: list[str]) -> dict[str, float]:
    """Build TF-IDF map from list of texts. Used only for keyword hints."""
    docs = [tokenize(d) for d in corpus]
    df = defaultdict(int)
    for doc in docs:
        for tok in set(doc):
            df[tok] += 1
    n = len(docs)
    tfidf = defaultdict(float)
    for doc in docs:
        freq = defaultdict(int)
        for tok in doc:
            freq[tok] += 1
        for tok, cnt in freq.items():
            idf = math.log((n + 1) / (df[tok] + 1))
            tfidf[tok] = max(tfidf[tok], cnt * idf)
    return tfidf


def extract_top_concepts(text: str, top_n: int = 8) -> list[str]:
    """Extract top concept keywords using TF-IDF (only as hints for LLM)."""
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)
    sentences = re.split(r"[。！？\n]+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    if not sentences:
        return []
    tfidf = build_tfidf(sentences)
    ranked = sorted(tfidf.items(), key=lambda x: -x[1])
    concepts = []
    seen = set()
    for word, score in ranked:
        if len(word) >= 2 and score > 0 and word not in seen:
            concepts.append(word)
            seen.add(word)
            if len(concepts) >= top_n:
                break
    return concepts


def clean_ocr_text(text: str) -> str:
    """Normalise OCR artefacts: 'H e l l o' → 'Hello'."""
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        words = line.split()
        if words and sum(1 for w in words if len(w) == 1 and w.isalpha()) / max(len(words), 1) > 0.4:
            line = re.sub(r"(?<=[a-zA-Z])\s(?=[a-zA-Z])", "", line)
        line = re.sub(r" {3,}", " ", line)
        cleaned.append(line)
    return "\n".join(cleaned)


def extract_date(text: str) -> str:
    """Extract date from frontmatter or body, return YYYY-MM-DD."""
    today = _dt.date.today().isoformat()
    fm_match = re.search(r"^---\n(.*?)\n---", text, re.DOTALL)
    if fm_match:
        fm = fm_match.group(1)
        for pattern in [
            r"20\d{2}[-年](\d{1,2})[-月](\d{1,2})",
            r"20\d{2}[-年](\d{1,2})",
        ]:
            m = re.search(pattern, fm)
            if m:
                y_str = re.search(r"20\d{2}", m.group(0))
                if not y_str:
                    continue
                try:
                    y, mo = int(y_str.group(0)), int(m.group(1))
                    d = int(m.group(2)) if m.lastindex >= 2 else None
                    if 1 <= mo <= 12 and (d is None or (1 <= d <= 31)):
                        if d:
                            return _dt.date(y, mo, d).isoformat()
                        return f"{y}-{mo:02d}"
                except (ValueError, OverflowError):
                    pass

    body = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)
    for pattern in [
        r"(20\d{2})[-年](\d{1,2})[-月](\d{1,2})",
        r"(20\d{2})-(\d{1,2})-(\d{1,2})",
    ]:
        m = re.search(pattern, body)
        if m:
            try:
                return _dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
            except ValueError:
                pass
    return today


def slugify(text: str) -> str:
    """Convert title to filename-safe slug."""
    s = re.sub(r"[^\w\s-]", "", text)
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-").lower()[:60]


def file_hash(filepath: Path) -> str:
    """Hash based on path + mtime + size."""
    stat = filepath.stat()
    key = f"{filepath}:{stat.st_mtime:.0f}:{stat.st_size}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


MANIFEST_PATH = ".ingest-manifest.json"


def load_manifest(vault: Path) -> dict:
    p = vault / MANIFEST_PATH
    if p.exists():
        return json.loads(p.read_text())
    return {"ingested": {}, "last_run": None}


def save_manifest(vault: Path, manifest: dict):
    (vault / MANIFEST_PATH).write_text(json.dumps(manifest, indent=2, ensure_ascii=False))


def is_new_file(vault: Path, manifest: dict, filepath: Path) -> bool:
    h = file_hash(filepath)
    return manifest.get("ingested", {}).get(str(filepath)) != h


# ── LLM Summary Generation ────────────────────────────────────────────────────

def extract_json(raw: str) -> dict:
    """Extract JSON from LLM response, handling <thinking> tags."""
    text = raw.strip()

    # Strip thinking tags
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
    raise ValueError(f"No parseable JSON found in: {repr(raw[:200])}")


def llm_generate_wiki_page(title: str, source_text: str, existing_wiki: list[str],
                           tfidf_concepts: list[str]) -> dict:
    """
    调用 MiniMax 生成结构化 Wiki 页面。

    返回 dict：
    {
        "title": str,          # 英文 slug 风格标题
        "summary": str,         # 200-400 字摘要
        "concepts": list[str], # 3-8 个关键概念
        "type": str,           # concept | entity | summary
        "related": list[str],  # 相关页面标题列表
        "content": str,        # 页面正文（markdown）
        "sources": str,        # 来源
        "action": str,         # "create" | "update"
        "update_target": str,  # 当 action=update 时，为已有页面标题
    }
    """
    # 读取现有 wiki 页面标题，用于判断是新建还是更新
    existing_list = "\n".join(f"- {t}" for t in existing_wiki[:20])

    prompt = f"""你是一个 LLM Wiki 知识库维护 Agent。请根据以下原文内容，生成一个结构化 Wiki 页面。

## 原文标题
{title}

## 原文内容（部分）
{source_text[: 8000]}

## 已有的 Wiki 页面标题（用于判断是否已存在相关页面）
{existing_list if existing_list else "(暂无)"}

## TF-IDF 关键词提示（仅供参考）
{", ".join(tfidf_concepts[:10])}

## 增量更新逻辑

请判断是新建页面还是更新已有页面：
- 如果原文内容与某个已有页面主题高度相关（同一概念、同一工具等）→ action="update"，update_target 填该已有页面标题
- 如果原文是全新主题 → action="create"

## 输出要求

请直接输出 JSON，包含以下字段：
- "title": 页面标题，使用英文 slug 风格（如 llm-wiki-pattern）
- "summary": 200-400 字摘要，概括文章核心内容
- "concepts": 3-8 个关键概念列表（用于双向链接）
- "type": 页面类型，选择其一：concept（概念页）| entity（实体页）| summary（摘要页）
  - concept：方法论、理念、模式
  - entity：人物、工具、论文、产品
  - summary：文章/文档的摘要
- "related": 相关页面标题列表（从已有 Wiki 页面中匹配，或留空）
- "content": 页面正文 markdown，使用 ## 章节结构，不要超过 800 字
- "sources": 原始文件路径或 URL
- "action": "create" 或 "update"
- "update_target": 当 action="update" 时，填写已有页面标题；action="create" 时填 ""

只输出 JSON，不要其他内容。"""

    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 3000,
        "temperature": 0.2,
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
            # Validate required fields
            for field in ("title", "summary", "type"):
                if field not in result:
                    raise ValueError(f"Missing field: {field}")
            return result
        except (ValueError, json.JSONDecodeError) as e:
            if attempt < 2:
                time.sleep(1)
                continue
            raise RuntimeError(f"LLM response parse failed after 3 attempts: {e}\nRaw: {raw[:500]}")

    raise RuntimeError("unreachable")


# ── File Scanning ─────────────────────────────────────────────────────────────

def scan_raw(vault: Path) -> list[tuple[Path, str]]:
    """Scan raw/ for processable text files."""
    raw_dir = vault / "raw"
    results = []
    SKIP_NAMES = {"all_notes", "readme", "index", "tmp", "draft"}
    SKIP_PREFIXES = {".", "_"}
    for ext in ["*.txt", "*.md"]:
        for f in raw_dir.rglob(ext):
            name_lower = f.stem.lower()
            if name_lower in SKIP_NAMES:
                continue
            if any(name_lower.startswith(p) for p in SKIP_PREFIXES):
                continue
            rel = f.relative_to(raw_dir)
            if rel.parts[0] == "refs":
                continue
            if len(rel.parts) > 2:
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                text = ""
            if len(text.strip()) < 100:
                continue
            results.append((f, text))
    return results


def get_existing_wiki_titles(vault: Path) -> list[str]:
    """Read all existing wiki page titles for context."""
    wiki_dir = vault / "wiki"
    titles = []
    if not wiki_dir.exists():
        return titles
    for md_file in wiki_dir.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8", errors="ignore")
        # Extract title from frontmatter or first H1
        fm_match = re.search(r"^---\n.*?\ntitle:\s*(.+?)\n", text, re.DOTALL)
        if fm_match:
            titles.append(fm_match.group(1).strip())
        else:
            h1_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
            if h1_match:
                titles.append(h1_match.group(1).strip())
    return titles


def detect_category(filepath: Path) -> str:
    """Detect category based on path and filename."""
    path_str, name = str(filepath).lower(), filepath.stem.lower()
    if "paper" in path_str or "arxiv" in path_str or "pdf" in path_str:
        return "papers"
    if "article" in path_str or "blog" in path_str or "post" in path_str:
        return "articles"
    if "note" in path_str or "memo" in path_str or "thinking" in path_str:
        return "notes"
    if "ref" in path_str or "book" in path_str:
        return "refs"
    if any(k in name for k in ["guide", "tutorial", "how", "使用", "教程", "入门"]):
        return "articles"
    return "articles"


def make_wiki_page(vault: Path, llm_result: dict, category: str,
                   title: str, source_url: str, date: str,
                   dry_run: bool = False) -> tuple[Path, str]:
    """
    Write a wiki page from LLM result.
    - action="create": normal creation
    - action="update": merge into existing page (keep frontmatter, append related/concepts/sections/sources)
    Returns (path, page_type)
    """
    page_type = llm_result.get("type", "concept")
    page_slug = slugify(llm_result.get("title", title))

    # Determine target directory based on type
    if page_type == "summary":
        target_dir = vault / "wiki" / "summaries"
    elif page_type == "entity":
        target_dir = vault / "wiki" / "entities"
    else:
        target_dir = vault / "wiki" / "concepts"

    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{page_slug}.md"

    action = llm_result.get("action", "create")

    # ── Incremental update logic ───────────────────────────────────────────
    if action == "update" and target_path.exists():
        if dry_run:
            print(f"  [DRY-RUN] Would UPDATE existing: {target_path}")
            return target_path, page_type

        existing_text = target_path.read_text(encoding="utf-8")

        # Parse existing frontmatter
        fm_match = re.search(r"^---\n(.*?)\n---\n(.*)$", existing_text, re.DOTALL)
        if fm_match:
            fm_block = fm_match.group(1)
            existing_body = fm_match.group(2)
        else:
            fm_block = ""
            existing_body = existing_text

        # Extract existing frontmatter fields
        def get_fm(field: str, default="") -> str:
            m = re.search(rf"^{field}:\s*(.+)$", fm_block, re.MULTILINE)
            return m.group(1).strip() if m else default

        existing_created = get_fm("created", date)
        existing_related_raw = get_fm("related", "")
        existing_sources_raw = get_fm("sources", "")

        # Parse existing sources list
        existing_sources = []
        src_m = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", existing_sources_raw)
        for lbl, url in src_m:
            existing_sources.append((lbl.strip(), url.strip()))
        # Also handle bare sources like "[label]" without URL
        for bare in re.findall(r"\[([^\]]+)\](?!\()", existing_sources_raw):
            if bare.strip() and (bare.strip(), "") not in existing_sources:
                existing_sources.append((bare.strip(), ""))

        # Append new source if not already present
        new_source = (title, source_url)
        if new_source not in existing_sources:
            existing_sources.append(new_source)

        # Merge related concepts (deduplicate)
        existing_related = []
        for r in re.findall(r"\[\[([^\]]+)\]\]", existing_related_raw):
            existing_related.append(r.strip())
        new_related = llm_result.get("related", [])
        for r in new_related:
            if r not in existing_related:
                existing_related.append(r)

        # Build updated related
        related_str = ", ".join(f"[[{r}]]" for r in existing_related[:5])
        related_md = "\n".join(f"- [[{r}]]" for r in existing_related[:5])

        # Merge sections from new content into existing body
        # Find existing h2 sections in body
        existing_sections = re.findall(r"(^## .+)$", existing_body, re.MULTILINE)
        new_content = llm_result.get("content", llm_result.get("summary", ""))
        new_sections = re.findall(r"(^## .+)$", new_content, re.MULTILINE)

        # Append new sections that don't already exist
        appended_sections = ""
        for sec_title in new_sections:
            if sec_title not in existing_sections:
                # Extract section content
                sec_pattern = re.escape(sec_title) + r"\n(.*?)(?=^## |\Z)"
                sec_m = re.search(sec_pattern, new_content, re.MULTILINE | re.DOTALL)
                sec_body = sec_m.group(1).strip() if sec_m else ""
                appended_sections += f"\n{sec_title}\n{sec_body}\n"

        # If no new sections to add, append a summary section
        if not appended_sections:
            appended_sections = f"\n## Summary from {title}\n\n> {llm_result.get('summary', '')[:200]}\n\n{llm_result.get('content', '')}\n"

        merged_body = existing_body + appended_sections

        # Build updated frontmatter
        tags = llm_result.get("concepts", [])[:4]
        sources_str = ", ".join(f"[{lbl}]({url})" if url else f"[{lbl}]" for lbl, url in existing_sources)

        page = f"""---
title: {llm_result.get("title", title)}
type: {page_type}
category: {category}
tags: [{", ".join(tags)}]
created: {existing_created}
updated: {date}
related: [{related_str}]
sources: [{sources_str}]
generation: LLM (MiniMax-M2.7-highspeed)
---

{merged_body}
"""

        target_path.write_text(page, encoding="utf-8")
        print(f"  [MERGED] {target_path} (updated related, sections, sources)")
        return target_path, page_type

    # ── Normal create ───────────────────────────────────────────────────────
    # Build related wikilinks
    related = llm_result.get("related", [])
    if related:
        related_md = "\n".join(f"- [[{r}]]" for r in related[:5])
        related_frontmatter = ", ".join(f"[[{r}]]" for r in related[:5])
    else:
        related_md = "- (待补充)"
        related_frontmatter = ""

    tags = llm_result.get("concepts", [])[:4]
    content_body = llm_result.get("content", llm_result.get("summary", ""))

    page = f"""---
title: {llm_result.get("title", title)}
type: {page_type}
category: {category}
tags: [{", ".join(tags)}]
created: {date}
updated: {date}
related: [{related_frontmatter}]
sources: [{source_url}]
generation: LLM (MiniMax-M2.7-highspeed)
---

# {llm_result.get("title", title)}

> {llm_result.get("summary", "")[:200]}

{content_body}

## Related

{related_md}

## Sources

- [{title}]({source_url})

---
*由 auto_ingest.py 自动生成于 {date}*
"""

    if dry_run:
        print(f"  [DRY-RUN] Would create: {target_path}")
        return target_path, page_type

    target_path.write_text(page, encoding="utf-8")
    return target_path, page_type


def update_index_md(vault: Path, page_slug: str, title: str, page_type: str, date: str,
                    dry_run: bool = False) -> bool:
    """
    Add entry to wiki/index.md if not already present.
    Returns True if successful (entry added or already exists), False if index.md missing.
    Creates index.md with template if it doesn't exist.
    """
    wiki_dir = vault / "wiki"
    wiki_dir.mkdir(parents=True, exist_ok=True)
    index_path = wiki_dir / "index.md"

    if not index_path.exists():
        # Auto-create template index
        template = """# Wiki Index

> 内容导向索引，LLM 查询时第一个读此文件定位相关页面。

## Concepts

## Entities

## Summaries

"""
        if not dry_run:
            index_path.write_text(template, encoding="utf-8")
        content = template
    else:
        content = index_path.read_text(encoding="utf-8")

    # Determine section based on type
    if page_type == "summary":
        section = "## Summaries"
        link = f"- [[summaries/{page_slug}|{title}]]"
    elif page_type == "entity":
        section = "## Entities"
        link = f"- [[entities/{page_slug}|{title}]]"
    else:
        section = "## Concepts"
        link = f"- [[concepts/{page_slug}|{title}]]"

    if page_slug in content:
        return True

    if section in content:
        content = content.replace(section, f"{link}\n\n{section}")
    else:
        content += f"\n\n{link} — {date}"

    if not dry_run:
        index_path.write_text(content, encoding="utf-8")
    return True


def append_log(vault: Path, operation: str, msg: str):
    """
    Append entry to log/YYYYMMDD.md in SCHEMA.md prescribed format.
    Format: [HH:MM] OPERATION - description
    """
    today = _dt.date.today().strftime("%Y%m%d")
    log_dir = vault / "log"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"{today}.md"
    now = _dt.datetime.now().strftime("%H:%M")
    entry = f"\n[{now}] {operation} - {msg}"
    if log_path.exists():
        log_path.write_text(log_path.read_text(encoding="utf-8") + entry, encoding="utf-8")
    else:
        log_path.write_text(f"# {today}\n\n{entry}\n", encoding="utf-8")


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("vault", type=Path, nargs="?", default=Path("."))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    vault = args.vault.resolve()
    if not vault.exists():
        print(f"ERROR: Vault not found: {vault}", file=sys.stderr)
        sys.exit(2)

    manifest = load_manifest(vault)
    new_files = [(f, t) for f, t in scan_raw(vault) if is_new_file(vault, manifest, f)]

    if not new_files:
        print("No new files to ingest.")
        sys.exit(0)

    existing_titles = get_existing_wiki_titles(vault)

    created = []
    for filepath, text in new_files:
        if args.verbose or args.dry_run:
            print(f"Processing: {filepath.name}")

        title = filepath.stem.replace("-", " ").replace("_", " ")
        category = detect_category(filepath)
        tfidf_concepts = extract_top_concepts(text)
        date = extract_date(text)
        source_url = f"file://{filepath}"

        if args.verbose or args.dry_run:
            print(f"  [LLM] Generating wiki page with MiniMax-M2.7-highspeed...")

        try:
            llm_result = llm_generate_wiki_page(
                title=title,
                source_text=text,
                existing_wiki=existing_titles,
                tfidf_concepts=tfidf_concepts,
            )
        except Exception as e:
            print(f"  [ERROR] LLM generation failed: {e}", file=sys.stderr)
            if not args.dry_run:
                append_log(vault, "INGEST", f"FAILED {filepath.name}: {e}")
            continue

        page_slug = slugify(llm_result.get("title", title))
        page_type = llm_result.get("type", "concept")

        # Karpathy rule: MUST update index.md before creating page
        index_ok = update_index_md(vault, page_slug, llm_result.get("title", title),
                          page_type, date, dry_run=args.dry_run)
        if not index_ok and not args.dry_run:
            print(f"  [WARN] index.md update failed, skipping page write: {page_slug}")
            continue

        target_path, _ = make_wiki_page(
            vault, llm_result, category, title, source_url, date,
            dry_run=args.dry_run,
        )

        h = file_hash(filepath)
        manifest["ingested"][str(filepath)] = h

        log_msg = (f"Ingested [LLM] {filepath.name} → wiki/{page_type}s/{page_slug}.md "
                   f"| concepts: {', '.join(llm_result.get('concepts', [])[:5])}")
        if not args.dry_run:
            append_log(vault, "INGEST", log_msg)
        created.append((category, page_type, page_slug))

    if not args.dry_run:
        manifest["last_run"] = _dt.datetime.now(_dt.timezone.utc).isoformat()
        save_manifest(vault, manifest)

    print(f"\nDone. {'[DRY-RUN] ' if args.dry_run else ''}"
          f"Processed {len(new_files)} new file(s), created {len(created)} page(s).")
    for cat, ptype, slug in created:
        print(f"  → wiki/{ptype}s/{slug}.md")


if __name__ == "__main__":
    main()
