#!/usr/bin/env python3
"""
auto_ingest.py — 自动扫描 raw/ 新文件，生成 Wiki 页面骨架。

Usage:
    python3 auto_ingest.py <vault-root> [--dry-run] [--verbose]

Logic:
  1. 扫描 raw/ 下新增文件（对比 .ingest-manifest.json）
  2. 纯 TF-IDF 提取关键词 + 句子分割
  3. 按 category 分类到 wiki/ 下
  4. 生成 summary 摘要页 + 可选 concept 概念页骨架
  5. 更新 wiki/index.md
  6. 追加 log/YYYYMMDD.md

Exit codes:
  0 — success
  1 — no new files
  2 — error
"""

import argparse
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── TF-IDF for concept extraction (no LLM needed) ──────────────────────────

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
    tokens = NGRAM_RE.findall(text.lower())
    return [t for t in tokens if t.lower() not in STOPWORDS and len(t) > 1]


def build_tfidf(corpus: list[str]) -> dict[str, float]:
    """Build TF-IDF scores across a corpus of documents."""
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


import math


def extract_top_concepts(text: str, top_n: int = 8) -> list[str]:
    """Extract top concept keywords from text using TF-IDF."""
    sentences = re.split(r"[。！？\n]+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    if not sentences:
        return []
    tfidf = build_tfidf(sentences)
    ranked = sorted(tfidf.items(), key=lambda x: -x[1])
    # Filter multi-char Chinese words and 2+ word English phrases
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
    """Normalise OCR artefacts: 'H e l l o' → 'Hello', collapse multi-spaces."""
    # Collapse sequences of short groups like "T h e" into "The"
    # Pattern: letter-space-letter → collapse space when it looks like spaced-out letters
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        # Detect if line looks like spaced-out letters (majority of words have single-char groups)
        words = line.split()
        if words and sum(1 for w in words if len(w) == 1 and w.isalpha()) / max(len(words), 1) > 0.4:
            # Likely OCR-spaced: collapse single-char tokens back together
            line = re.sub(r"(?<=[a-zA-Z])\s(?=[a-zA-Z])", "", line)
        # Collapse 3+ spaces
        line = re.sub(r" {3,}", " ", line)
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def extract_summary(text: str, max_chars: int = 500) -> str:
    """Extract lead paragraph + key sentences as a summary."""
    text = clean_ocr_text(text)
    lines = [l.strip() for l in text.split("\n") if l.strip() and len(l.strip()) > 15]
    skip_pattern = re.compile(r"^[A-Z\s]{5,}$|^[─=\s]+$|^ORANGE\s*BOOK|^PUBLISHED|^更新时间")
    summary_lines = []
    chars = 0
    for line in lines:
        if skip_pattern.match(line):
            continue
        if chars + len(line) > max_chars:
            break
        summary_lines.append(line)
        chars += len(line)
    return "\n\n".join(summary_lines) if summary_lines else text[:max_chars]


def extract_date_from_text(text: str) -> Optional[str]:
    """Try to extract a date from text content."""
    patterns = [
        r"(20\d{2})[年-](0?[1-9]|1[0-2])[月-](0?[1-9]|[12]\d|3[01])",
        r"(20\d{2})-(0?[1-9]|1[0-2])-(0?[1-9]|[12]\d|3[01])",
        r"发布于[：:]?\s*(20\d{2}[-/年]\d{1,2}[-/月]\d{1,2})",
        r"Published?\s*[:\-]?\s*(\w+\s+\d{1,2},?\s+20\d{2})",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            raw = m.group(0)
            raw = re.sub(r"[年月日]", "-", raw)
            raw = re.sub(r"\s+", "", raw)
            return raw[:10]
    return None
    """Extract lead paragraph + key sentences as a summary."""
    text = clean_ocr_text(text)
    lines = [l.strip() for l in text.split("\n") if l.strip() and len(l.strip()) > 15]
    # Skip cover-page lines (short all-caps, special chars)
    skip_pattern = re.compile(r"^[A-Z\s]{5,}$|^[─=\s]+$|^ORANGE\s*BOOK")
    summary_lines = []
    chars = 0
    for line in lines:
        if skip_pattern.match(line):
            continue
        if chars + len(line) > max_chars:
            break
        summary_lines.append(line)
        chars += len(line)
    return "\n\n".join(summary_lines) if summary_lines else text[:max_chars]


def detect_category(filepath: Path) -> str:
    """Guess wiki category from file path and name."""
    path_str = str(filepath).lower()
    name = filepath.stem.lower()
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


def slugify(title: str) -> str:
    """Convert title to kebab-case slug."""
    s = re.sub(r"[^\w\s-]", "", title)
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-").lower()


def file_hash(filepath: Path) -> str:
    """Quick hash of file path + mtime for change detection."""
    stat = filepath.stat()
    key = f"{filepath}:{stat.st_mtime:.0f}:{stat.st_size}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


# ── Manifest management ───────────────────────────────────────────────────

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
    ingested = manifest.get("ingested", {})
    return ingested.get(str(filepath)) != h


# ── Page generation ────────────────────────────────────────────────────────

def make_summary_frontmatter(title: str, source_url: str, date: str, tags: list[str]) -> str:
    return f"""---
title: summaries/{slugify(title)}
type: summary
source_url: "{source_url}"
source_type: article
date: {date}
ingested: {datetime.now(timezone.utc).strftime("%Y-%m-%d")}
tags: [{", ".join(tags)}]
---

# {title}

**Source**: {source_url} · {date}
"""


def make_summary_page(vault: Path, category: str, title: str,
                      text_content: str, source_url: str, date: str,
                      concepts: list[str], dry_run: bool = False) -> Path:
    """Create a wiki/summaries/<slug>.md summary page."""
    slug = slugify(title)
    target_dir = vault / "wiki" / category / "summaries"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{slug}.md"

    summary_text = extract_summary(text_content)
    tags = concepts[:4]

    frontmatter = f"""---
title: summaries/{slug}
type: summary
source_type: article
date: {date}
ingested: {datetime.now(timezone.utc).strftime("%Y-%m-%d")}
tags: [{", ".join(tags)}]
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
        print(f"  Content preview: {summary_text[:100]}...")
        return target_path

    target_path.write_text(frontmatter, encoding="utf-8")
    return target_path


def update_index_md(vault: Path, category: str, title: str, slug: str, dry_run: bool = False):
    """Add new summary to wiki/index.md."""
    index_path = vault / "wiki" / "index.md"
    if not index_path.exists():
        return

    content = index_path.read_text(encoding="utf-8")
    anchor = f"- [[summaries/{slug}|{title}]]"

    # Check if already exists
    if f"summaries/{slug}" in content:
        return

    # Insert before ## Open Questions or at end
    marker = "## Open Questions"
    if marker in content:
        content = content.replace(marker, f"{anchor}\n\n{marker}")
    else:
        content += f"\n- [[summaries/{slug}|{title}]] — {datetime.now().strftime('%Y-%m-%d')}"

    if not dry_run:
        index_path.write_text(content, encoding="utf-8")
    else:
        print(f"  [DRY-RUN] Would add to index: {anchor}")


def append_log(vault: Path, msg: str):
    """Append entry to log/YYYYMMDD.md."""
    today = datetime.now().strftime("%Y%m%d")
    log_dir = vault / "log"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"{today}.md"
    ts = datetime.now().strftime("%H:%M")
    entry = f"\n## [{ts}] ingest | {msg}"
    if log_path.exists():
        log_path.write_text(log_path.read_text(encoding="utf-8") + entry, encoding="utf-8")
    else:
        log_path.write_text(f"# {today}\n\n## Daily Log\n{entry}\n", encoding="utf-8")


# ── Main ───────────────────────────────────────────────────────────────────

def scan_raw(vault: Path) -> list[tuple[Path, str]]:
    """Return (filepath, text_content) for new/updated files in raw/."""
    raw_dir = vault / "raw"
    results = []
    # Skip patterns
    SKIP_NAMES = {"all_notes", "readme", "index", "tmp", "draft"}
    SKIP_PREFIXES = {".", "_"}

    for ext in ["*.txt", "*.md"]:
        for f in raw_dir.rglob(ext):
            name_lower = f.stem.lower()
            if name_lower in SKIP_NAMES:
                continue
            if any(name_lower.startswith(p) for p in SKIP_PREFIXES):
                continue
            # Skip refs/ subdirectory (pointer files only)
            rel = f.relative_to(raw_dir)
            if rel.parts[0] == "refs":
                continue
            # Skip deep subdirs — files in root or 1 level deep (articles/, papers/)
            if len(rel.parts) > 2:
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                text = ""
            if len(text.strip()) < 100:  # skip near-empty files
                continue
            results.append((f, text))
    return results


def main():
    parser = argparse.ArgumentParser(description="Auto-ingest new raw files into wiki.")
    parser.add_argument("vault", type=Path, nargs="?", default=Path("."))
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    vault = args.vault.resolve()
    if not vault.exists():
        print(f"ERROR: Vault not found: {vault}", file=sys.stderr)
        sys.exit(2)

    manifest = load_manifest(vault)
    new_files = []

    for filepath, text in scan_raw(vault):
        if is_new_file(vault, manifest, filepath):
            new_files.append((filepath, text))

    if not new_files:
        print("No new files to ingest.")
        sys.exit(1)

    created = []
    for filepath, text in new_files:
        if args.verbose or args.dry_run:
            print(f"Processing: {filepath.name}")

        # Extract metadata
        title = filepath.stem.replace("-", " ").replace("_", " ")
        category = detect_category(filepath)
        concepts = extract_top_concepts(text)
        slug = slugify(title)
        date = extract_date_from_text(text) or datetime.fromtimestamp(filepath.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d")
        source_url = f"file://{filepath}"

        # Create summary page
        p = make_summary_page(vault, category, title, text, source_url, date,
                              concepts, dry_run=args.dry_run)
        created.append((category, title, slug))

        # Update index
        update_index_md(vault, category, title, slug, dry_run=args.dry_run)

        # Update manifest
        h = file_hash(filepath)
        manifest["ingested"][str(filepath)] = h

        if not args.dry_run:
            append_log(vault, f"Ingested {filepath.name} → wiki/{category}/summaries/{slug}.md | concepts: {', '.join(concepts[:5])}")

    if not args.dry_run:
        manifest["last_run"] = datetime.now(timezone.utc).isoformat()
        save_manifest(vault, manifest)

    print(f"\nDone. {'[DRY-RUN] ' if args.dry_run else ''}Processed {len(new_files)} new file(s), created {len(created)} page(s).")
    for cat, title, slug in created:
        print(f"  → wiki/{cat}/summaries/{slug}.md")


if __name__ == "__main__":
    main()
