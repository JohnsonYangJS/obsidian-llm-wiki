#!/usr/bin/env python3
"""
auto_ingest.py — 自动扫描 raw/ 新文件，生成 Wiki 页面骨架。

Usage:
    python3 auto_ingest.py <vault-root> [--dry-run] [--verbose] [--llm]

Options:
    --llm   用 MiniMax LLM 生成 summary（比 TF-IDF 更智能）
"""

import argparse
import datetime as _dt
import hashlib
import json
import math
import os
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional

# ── MiniMax LLM ───────────────────────────────────────────────────────────

import urllib.request
import urllib.error

MINIMAX_API_KEY = "sk-cp-SUjytMlOmz-9qX73aXQbhNog3hEQmYoLxVff1IkOVFCJ_pia4t0ykTJSgp3bQ3aWvmIyIu-HJvNRCZEXHRTL_rFGARGtSpURNHNunmm5yXTucUaLJDH1uaE"
MINIMAX_BASE = "https://api.minimax.chat/v1"


def generate_summary_llm(text: str, title: str,
                         max_chars: int = 600) -> tuple[str, list[str]]:
    """Generate summary + concepts using MiniMax LLM. Returns (summary, concepts)."""
    truncated = text[:3000]

    prompt = f"""你是一个专业的知识整理助手。请为以下文章生成摘要，并提炼核心知识点。

文章标题：{title}

文章内容：
{truncated}

请按以下 JSON 格式输出（只输出 JSON，不要其他内容）：
{{"summary": "一段200-400字的中文摘要，涵盖文章的核心观点和关键信息", "concepts": ["概念1", "概念2", "概念3", "概念4", "概念5"]}}"""

    payload = {
        "model": "MiniMax-M2.5",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,
        "temperature": 0.3,
        "thinking": {"type": "off"},
    }

    req = urllib.request.Request(
        f"{MINIMAX_BASE}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {MINIMAX_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"]
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

            # Parse JSON
            data = json.loads(content)
            summary = data.get("summary", "")[:max_chars]
            concepts = data.get("concepts", [])
            return summary, concepts

    except Exception as e:
        print(f"    [LLM] API 调用失败: {e}，降级到 TF-IDF")
        return None, None


# ── Stopwords ──────────────────────────────────────────────────────────────

STOPWORDS = {
    "的", "了", "和", "是", "在", "就", "都", "而", "及", "与",
    "着", "或", "一个", "没有", "我们", "你们", "他们", "这个",
    "那个", "因为", "所以", "但是", "如果", "虽然", "还是",
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would",
    "can", "could", "should", "may", "might", "must", "shall",
    "and", "or", "but", "if", "then", "when", "this", "that",
    "these", "those", "it", "its", "they", "them", "their",
    "not", "no", "nor", "for", "so", "as", "at", "by", "from",
    "in", "of", "on", "to", "with", "about", "into", "through",
    "during", "before", "after", "above", "below", "up", "down",
    "out", "off", "over", "under", "again", "further", "once",
}

NGRAM_RE = re.compile(r"[\u4e00-\u9fff]{2,}|[\w]{4,}")


def tokenize(text: str) -> list[str]:
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)
    tokens = NGRAM_RE.findall(text.lower())
    return [t for t in tokens if t.lower() not in STOPWORDS and len(t) > 1]


def build_tfidf(corpus: list[str]) -> dict[str, float]:
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
    """Extract top concept keywords using TF-IDF (strips frontmatter)."""
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

    # Frontmatter first
    fm_match = re.search(r"^---\n(.*?)\n---", text, re.DOTALL)
    if fm_match:
        fm = fm_match.group(1)
        # Match: 2026-04-23  or  2026年4月23日  or  2026-04
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

    # Body
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


def extract_summary(text: str, max_chars: int = 500) -> str:
    """Extract lead paragraph + key sentences as a summary."""
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)
    text = clean_ocr_text(text)
    lines = [l.strip() for l in text.split("\n") if l.strip() and len(l.strip()) > 15]
    skip_pattern = re.compile(r"^[A-Z\s]{5,}$|^[─=\s]+$|^ORANGE\s*BOOK|^PUBLISHED|^更新时间")
    summary_lines, chars = [], 0
    for line in lines:
        if skip_pattern.match(line):
            continue
        if chars + len(line) > max_chars:
            break
        summary_lines.append(line)
        chars += len(line)
    return "\n\n".join(summary_lines) if summary_lines else text[:max_chars]


def detect_category(filepath: Path) -> str:
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


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text)
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-").lower()[:60]


def file_hash(filepath: Path) -> str:
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


def make_summary_page(vault: Path, category: str, title: str,
                      text_content: str, source_url: str, date: str,
                      concepts: list[str], dry_run: bool = False,
                      llm_summary: str = None, llm_concepts: list[str] = None) -> Path:
    slug = slugify(title)
    target_dir = vault / "wiki" / category / "summaries"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{slug}.md"

    # LLM takes full priority if available
    if llm_summary:
        summary_text = llm_summary
        generation_method = "LLM (MiniMax)"
        if llm_concepts:
            concepts = llm_concepts   # LLM concepts override TF-IDF
    else:
        summary_text = extract_summary(text_content)
        generation_method = "TF-IDF"
    tags = concepts[:4]

    page = f"""---
title: summaries/{slug}
type: summary
source_type: article
date: {date}
ingested: {_dt.date.today().isoformat()}
tags: [{", ".join(tags)}]
generation: {generation_method}
---

# {title}

**Source**: {source_url} · {date}

## Key takeaways

- {" · ".join(concepts[:5])}

## Summary

{summary_text}

## Concepts introduced / referenced

{" · ".join(f"[[{c}]]" for c in concepts[:5])}
"""
    if dry_run:
        print(f"  [DRY-RUN] Would create: {target_path}")
        return target_path
    target_path.write_text(page, encoding="utf-8")
    return target_path


def update_index_md(vault: Path, category: str, title: str, slug: str, dry_run: bool = False):
    index_path = vault / "wiki" / "index.md"
    if not index_path.exists():
        return
    content = index_path.read_text(encoding="utf-8")
    anchor = f"- [[summaries/{slug}|{title}]]"
    if f"summaries/{slug}" in content:
        return
    marker = "## Open Questions"
    if marker in content:
        content = content.replace(marker, f"{anchor}\n\n{marker}")
    else:
        content += f"\n- [[summaries/{slug}|{title}]] — {_dt.date.today().isoformat()}"
    if not dry_run:
        index_path.write_text(content, encoding="utf-8")


def append_log(vault: Path, msg: str):
    today = _dt.date.today().strftime("%Y%m%d")
    log_dir = vault / "log"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"{today}.md"
    now = _dt.datetime.now().strftime("%H:%M")
    entry = f"\n## [{now}] ingest | {msg}"
    if log_path.exists():
        log_path.write_text(log_path.read_text(encoding="utf-8") + entry, encoding="utf-8")
    else:
        log_path.write_text(f"# {today}\n\n## Daily Log\n{entry}\n", encoding="utf-8")


def scan_raw(vault: Path) -> list[tuple[Path, str]]:
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("vault", type=Path, nargs="?", default=Path("."))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--llm", action="store_true",
                        help="用 MiniMax LLM 生成 summary（更智能）")
    args = parser.parse_args()

    vault = args.vault.resolve()
    if not vault.exists():
        print(f"ERROR: Vault not found: {vault}", file=sys.stderr)
        sys.exit(2)

    manifest = load_manifest(vault)
    new_files = [(f, t) for f, t in scan_raw(vault) if is_new_file(vault, manifest, f)]

    if not new_files:
        print("No new files to ingest.")
        sys.exit(1)

    created = []
    for filepath, text in new_files:
        if args.verbose or args.dry_run:
            print(f"Processing: {filepath.name}")

        title = filepath.stem.replace("-", " ").replace("_", " ")
        category = detect_category(filepath)
        concepts = extract_top_concepts(text)
        slug = slugify(title)
        date = extract_date(text)
        source_url = f"file://{filepath}"

        # LLM summary generation (if --llm flag)
        llm_summary = None
        llm_concepts = None
        if args.llm:
            if args.verbose or args.dry_run:
                print(f"  [LLM] Generating summary + concepts with MiniMax...")
            llm_summary, llm_concepts = generate_summary_llm(text, title)

        make_summary_page(vault, category, title, text, source_url, date,
                        concepts, dry_run=args.dry_run,
                        llm_summary=llm_summary, llm_concepts=llm_concepts)
        update_index_md(vault, category, title, slug, dry_run=args.dry_run)

        h = file_hash(filepath)
        manifest["ingested"][str(filepath)] = h

        method_tag = "LLM" if llm_summary else "TF-IDF"
        if not args.dry_run:
            append_log(vault, f"Ingested [{method_tag}] {filepath.name} → wiki/{category}/summaries/{slug}.md | concepts: {', '.join(concepts[:5])}")
        created.append((category, title, slug))

    if not args.dry_run:
        manifest["last_run"] = _dt.datetime.now(_dt.timezone.utc).isoformat()
        save_manifest(vault, manifest)

    print(f"\nDone. {'[DRY-RUN] ' if args.dry_run else ''}Processed {len(new_files)} new file(s), created {len(created)} page(s).")
    for cat, title, slug in created:
        print(f"  → wiki/{cat}/summaries/{slug}.md")


if __name__ == "__main__":
    main()
