#!/usr/bin/env python3
"""
lint_wiki.py — Health check for an LLM Wiki (Karpathy 方案增强版)

核心变更：
- 新增语义矛盾检测：调用 MiniMax 读取多个相关页面，检测内容矛盾
- 保留现有检查：死链、孤儿页、索引同步
- 生成 output/lint-report-YYYY-MM-DD.md

用法：
    python3 lint_wiki.py <vault-root> [--llm] [--dry-run] [-v]

Checks:
  1. Dead wikilinks — [[Target]] where Target.md doesn't exist
  2. Orphan pages — wiki pages with no inbound links
  3. Missing index entries — wiki pages not listed in wiki/index.md
  4. Unlinked concepts — terms mentioned 3+ times but lacking their own page
  5. log/ shape — every file matches YYYYMMDD.md and has the right H1
  6. audit/ shape — every audit/*.md parses as a valid AuditEntry
  7. Audit targets — every open audit's `target` file must exist
  8. [NEW] Semantic contradictions — LLM reads related pages and detects conflicts

Exit codes:
  0 — no issues found
  1 — issues found (printed to stdout)
"""

import argparse
import datetime as _dt
import json
import os
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

# ── Regex ─────────────────────────────────────────────────────────────────────
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")
LOG_FILENAME_RE = re.compile(r"^(\d{4})(\d{2})(\d{2})\.md$")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

# Required audit frontmatter fields
AUDIT_REQUIRED_FIELDS = {
    "id", "target", "target_lines", "anchor_before", "anchor_text",
    "anchor_after", "severity", "author", "source", "created", "status",
}
VALID_SEVERITIES = {"info", "suggest", "warn", "error"}
VALID_STATUSES = {"open", "resolved"}
VALID_SOURCES = {"obsidian-plugin", "web-viewer", "manual"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_pages(wiki_dir: Path) -> dict[str, Path]:
    pages: dict[str, Path] = {}
    for p in wiki_dir.rglob("*.md"):
        pages[p.stem] = p
        rel = p.relative_to(wiki_dir)
        pages[str(rel.with_suffix(""))] = p
    return pages


def extract_wikilinks(text: str) -> list[str]:
    return WIKILINK_RE.findall(text)


def parse_frontmatter(text: str) -> dict | None:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    body = m.group(1)
    result: dict = {}
    lines = body.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue
        key, _, rest = line.partition(":")
        key = key.strip()
        val = rest.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            if not inner:
                result[key] = []
            else:
                parts = [p.strip() for p in inner.split(",")]
                parsed: list = []
                for p in parts:
                    if p.isdigit() or (p.startswith("-") and p[1:].isdigit()):
                        parsed.append(int(p))
                    else:
                        parsed.append(p.strip('"').strip("'"))
                result[key] = parsed
        elif val.startswith('"') and val.endswith('"'):
            result[key] = val[1:-1].replace("\\n", "\n").replace('\\"', '"')
        elif val.startswith("'") and val.endswith("'"):
            result[key] = val[1:-1]
        else:
            result[key] = val
        i += 1
    return result


# ── LLM Semantic Contradiction Detection ─────────────────────────────────────

def extract_json_llm(raw: str) -> dict:
    """Extract JSON from LLM contradiction-check response."""
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


def check_semantic_contradictions(vault: Path, pages: dict[str, Path],
                                  dry_run: bool = False, verbose: bool = False) -> list[dict]:
    """
    对同主题的相关页面调用 LLM 检测语义矛盾。
    返回矛盾列表：[{"page_a": str, "page_b": str, "conflict": str, "severity": str}]
    """
    if len(pages) < 2:
        return []

    wiki_dir = vault / "wiki"
    all_files = list(wiki_dir.rglob("*.md"))
    all_texts: dict[str, str] = {}

    for f in all_files:
        if f.name in (".gitkeep",):
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        # Strip frontmatter
        text = FRONTMATTER_RE.sub("", text)
        # Get title
        fm = parse_frontmatter(f.read_text(encoding="utf-8"))
        title = fm.get("title", f.stem) if fm else f.stem
        all_texts[title] = text[:2000]  # Limit to first 2000 chars

    if len(all_texts) < 2:
        return []

    # Group pages by tag similarity to find potentially related pages
    # Then check pairs for contradictions
    contradictions = []
    titles = list(all_texts.keys())

    # Check pairs (limit to avoid too many API calls)
    max_pairs = 20
    pair_count = 0

    for i, title_a in enumerate(titles):
        for title_b in titles[i+1:]:
            if pair_count >= max_pairs:
                break

            # Skip summaries vs summaries (not meaningful to compare)
            type_a = "summary" in title_a.lower() or "summary" in all_texts.get(title_a, "")[:500].lower()
            type_b = "summary" in title_b.lower() or "summary" in all_texts.get(title_b, "")[:500].lower()
            if type_a and type_b:
                continue

            pair_count += 1

            if verbose:
                print(f"  Checking: [[{title_a}]] vs [[{title_b}]]...")

            content_a = all_texts[title_a]
            content_b = all_texts[title_b]

            prompt = f"""你是一个知识库质量检查员。请检查以下两个 Wiki 页面，判断它们在核心表述上是否存在语义矛盾。

## 页面 A: {title_a}
{content_a[:1500]}

## 页面 B: {title_b}
{content_b[:1500]}

## 检查要求

1. 如果两个页面讨论的是完全不相关的主题 → `contradiction: false`
2. 如果两个页面讨论相关主题但表述一致或互补 → `contradiction: false`
3. 如果两个页面讨论相关主题但核心观点矛盾（如：一个说X，另一个说非X）→ `contradiction: true`

请直接输出 JSON：
{{
  "contradiction": true或false,
  "conflict_description": "如果矛盾，描述矛盾的具体内容（100字内）；否则留空",
  "severity": "error或warn（error=严重矛盾，warn=轻微不一致）",
  "recommendation": "修复建议（50字内）"
}}

只输出 JSON，不要其他内容。"""

            payload = json.dumps({
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
                "temperature": 0.1,
            })

            try:
                proc = subprocess.run(
                    ["curl", "-s", "-X", "POST", f"{MINIMAX_BASE}/chat/completions",
                     "-H", f"Authorization: Bearer {MINIMAX_API_KEY}",
                     "-H", "Content-Type: application/json",
                     "-d", payload, "--noproxy", "*", "--max-time", "45"],
                    capture_output=True, text=True, timeout=50,
                )
                if proc.returncode != 0:
                    continue
                raw = json.loads(proc.stdout)["choices"][0]["message"]["content"]
                result = extract_json_llm(raw)

                if result.get("contradiction", False):
                    contradictions.append({
                        "page_a": title_a,
                        "page_b": title_b,
                        "conflict": result.get("conflict_description", ""),
                        "severity": result.get("severity", "warn"),
                        "recommendation": result.get("recommendation", ""),
                    })
            except Exception:
                continue

        if pair_count >= max_pairs:
            break

    return contradictions


# ── Lint Core ─────────────────────────────────────────────────────────────────

def lint(root: str, use_llm: bool = False, dry_run: bool = False,
         verbose: bool = False) -> int:
    root_path = Path(root)
    wiki_path = root_path / "wiki"
    log_path = root_path / "log"
    audit_path = root_path / "audit"
    output_path = root_path / "output"

    if not wiki_path.exists():
        print(f"ERROR: wiki/ directory not found at {wiki_path}", file=sys.stderr)
        return 1

    pages = load_pages(wiki_path)
    all_wiki_files = list(wiki_path.rglob("*.md"))
    index_path = wiki_path / "index.md"

    issues = 0
    inbound: dict[str, list[str]] = defaultdict(list)
    report_lines = []

    # ── Pass 1: dead wikilinks ──────────────────────────────────────────────
    dead_links: list[tuple[str, str]] = []
    for md_file in all_wiki_files:
        text = md_file.read_text(encoding="utf-8")
        for link in extract_wikilinks(text):
            link = link.strip()
            if link not in pages and Path(link).stem not in pages:
                dead_links.append((str(md_file.relative_to(root_path)), link))
            else:
                target = pages.get(link) or pages.get(Path(link).stem)
                if target:
                    inbound[target.stem].append(md_file.stem)

    if dead_links:
        print(f"\n🔴 Dead wikilinks ({len(dead_links)}):")
        for source, link in dead_links:
            print(f"   {source} → [[{link}]]")
            report_lines.append(f"- 🔴 Dead link: {source} → [[{link}]]")
        issues += len(dead_links)
    else:
        print("✅ No dead wikilinks")

    # ── Pass 2: orphan pages ────────────────────────────────────────────────
    skip_orphan = {"index"}
    orphans = [
        p for p in all_wiki_files
        if p.stem not in inbound and p.stem not in skip_orphan
        and p.parent != wiki_path
    ]
    if orphans:
        print(f"\n🟡 Orphan pages ({len(orphans)}) — no inbound wikilinks:")
        for p in orphans:
            print(f"   {p.relative_to(root_path)}")
            report_lines.append(f"- 🟡 Orphan page: {p.relative_to(root_path)}")
        issues += len(orphans)
    else:
        print("✅ No orphan pages")

    # ── Pass 3: missing index entries ───────────────────────────────────────
    if index_path.exists():
        index_text = index_path.read_text(encoding="utf-8")
        not_in_index = [
            p for p in all_wiki_files
            if p != index_path
            and f"[[{p.stem}]]" not in index_text
            and str(p.relative_to(wiki_path).with_suffix("")) not in index_text
        ]
        if not_in_index:
            print(f"\n🟡 Pages missing from index.md ({len(not_in_index)}):")
            for p in not_in_index:
                print(f"   {p.relative_to(root_path)}")
                report_lines.append(f"- 🟡 Not in index: {p.relative_to(root_path)}")
            issues += len(not_in_index)
        else:
            print("✅ All pages in index.md")
    else:
        print("⚠️  wiki/index.md not found — skipping index check")

    # ── Pass 4: unlinked concepts ───────────────────────────────────────────
    all_text = " ".join(p.read_text(encoding="utf-8") for p in all_wiki_files)
    all_links = WIKILINK_RE.findall(all_text)
    link_counts: dict[str, int] = defaultdict(int)
    for link in all_links:
        link_counts[link.strip()] += 1

    missing_pages = [
        (link, count) for link, count in link_counts.items()
        if count >= 3 and link not in pages and Path(link).stem not in pages
    ]
    if missing_pages:
        print(f"\n🟡 Frequently linked but no page ({len(missing_pages)}):")
        for link, count in sorted(missing_pages, key=lambda x: -x[1]):
            print(f"   [[{link}]] — mentioned {count}x")
            report_lines.append(f"- 🟡 Missing page but linked often: [[{link}]] ({count}x)")
        issues += len(missing_pages)
    else:
        print("✅ No frequently-linked missing pages")

    # ── Pass 5: log/ shape ───────────────────────────────────────────────────
    if log_path.exists() and log_path.is_dir():
        log_issues: list[str] = []
        for p in sorted(log_path.iterdir()):
            if p.is_dir():
                continue
            if p.name == ".gitkeep":
                continue
            m = LOG_FILENAME_RE.match(p.name)
            if not m:
                log_issues.append(f"   {p.relative_to(root_path)} — filename doesn't match YYYYMMDD.md")
                continue
            y, mo, d = m.groups()
            iso = f"{y}-{mo}-{d}"
            first_line = p.read_text(encoding="utf-8").splitlines()[:1]
            if not first_line or first_line[0].strip() != f"# {iso}":
                log_issues.append(f"   {p.relative_to(root_path)} — expected H1 '# {iso}'")
        if log_issues:
            print(f"\n🟡 log/ shape issues ({len(log_issues)}):")
            for s in log_issues:
                print(s)
                report_lines.append(f"- 🟡 log/ issue: {s.strip()}")
            issues += len(log_issues)
        else:
            print("✅ log/ shape OK")
    else:
        print("⚠️  log/ directory not found — skipping log shape check")

    # ── Pass 6: audit/ shape ─────────────────────────────────────────────────
    audit_targets_to_check: list[tuple[str, str]] = []
    if audit_path.exists() and audit_path.is_dir():
        audit_files = [
            p for p in audit_path.rglob("*.md") if p.name != ".gitkeep"
        ]
        audit_issues: list[str] = []
        for p in audit_files:
            text = p.read_text(encoding="utf-8")
            fm = parse_frontmatter(text)
            rel = p.relative_to(root_path)
            if fm is None:
                audit_issues.append(f"   {rel} — missing YAML frontmatter")
                continue
            missing = AUDIT_REQUIRED_FIELDS - set(fm.keys())
            if missing:
                audit_issues.append(f"   {rel} — missing fields: {', '.join(sorted(missing))}")
                continue
            if fm["severity"] not in VALID_SEVERITIES:
                audit_issues.append(f"   {rel} — invalid severity '{fm['severity']}'")
            if fm["source"] not in VALID_SOURCES:
                audit_issues.append(f"   {rel} — invalid source '{fm['source']}'")
            expected_status = "resolved" if "resolved" in p.parts else "open"
            if fm["status"] != expected_status:
                audit_issues.append(f"   {rel} — status '{fm['status']}' doesn't match directory")
            if fm["status"] == "open":
                audit_targets_to_check.append((fm["id"], fm["target"]))

        if audit_issues:
            print(f"\n🔴 audit/ shape issues ({len(audit_issues)}):")
            for s in audit_issues:
                print(s)
                report_lines.append(f"- 🔴 audit/ issue: {s.strip()}")
            issues += len(audit_issues)
        else:
            print(f"✅ audit/ shape OK ({len(audit_files)} files)")
    else:
        print("⚠️  audit/ directory not found — skipping audit shape check")

    # ── Pass 7: audit targets exist ──────────────────────────────────────────
    missing_targets: list[tuple[str, str]] = []
    for audit_id, target in audit_targets_to_check:
        target_path = root_path / target
        if not target_path.exists():
            alt = wiki_path / target
            if not alt.exists():
                missing_targets.append((audit_id, target))
    if missing_targets:
        print(f"\n🔴 Open audits with missing target files ({len(missing_targets)}):")
        for audit_id, target in missing_targets:
            print(f"   {audit_id} → {target}")
            report_lines.append(f"- 🔴 Audit target missing: {audit_id} → {target}")
        issues += len(missing_targets)
    elif audit_targets_to_check:
        print("✅ All open-audit targets exist")

    # ── Pass 8: [NEW] Semantic Contradiction Detection ───────────────────────
    if use_llm:
        print("\n[LLM] Checking semantic contradictions...")
        contradictions = check_semantic_contradictions(
            root_path, pages, dry_run=dry_run, verbose=verbose
        )
        if contradictions:
            print(f"\n🔴 Semantic contradictions ({len(contradictions)}):")
            for c in contradictions:
                severity_icon = "🔴" if c["severity"] == "error" else "🟡"
                print(f"   {severity_icon} [[{c['page_a']}]] vs [[{c['page_b']}]]: {c['conflict']}")
                print(f"      → {c['recommendation']}")
                report_lines.append(
                    f"- {severity_icon} Contradiction: [[{c['page_a']}]] vs [[{c['page_b']}]]: "
                    f"{c['conflict']} (severity: {c['severity']})"
                )
                report_lines.append(f"  → Recommendation: {c['recommendation']}")
            issues += len(contradictions)
        else:
            print("✅ No semantic contradictions detected")

    # ── Summary ─────────────────────────────────────────────────────────────
    print(f"\n{'─'*40}")
    if issues == 0:
        print("✅ Wiki is healthy — no issues found")
    else:
        print(f"⚠️  {issues} issue(s) found — review above")

    # ── Write Report ─────────────────────────────────────────────────────────
    if report_lines:
        output_path.mkdir(exist_ok=True)
        today = _dt.date.today().isoformat()
        report_path = output_path / f"lint-report-{today}.md"
        report_content = f"""# Lint Report — {today}

## Summary
- Total issues: {issues}
- Dead links: {len(dead_links)}
- Orphan pages: {len(orphans)}
- Missing index entries: {len(not_in_index) if index_path.exists() else 'N/A'}
- Frequently linked but missing: {len(missing_pages)}
- Semantic contradictions: {len(contradictions) if use_llm and 'contradictions' in dir() else 'N/A'}

## Details

"""
        report_content += "\n".join(report_lines)
        report_content += f"\n\n---\n*Generated by lint_wiki.py at {_dt.datetime.now().isoformat()}*"

        if dry_run:
            print(f"\n[DRY-RUN] Would write report to: {report_path}")
        else:
            report_path.write_text(report_content, encoding="utf-8")
            print(f"\nReport written to: {report_path}")

        # Also create audit entries for contradictions
        if use_llm and contradictions:
            audit_dir = audit_path / "open"
            audit_dir.mkdir(parents=True, exist_ok=True)
            for c in contradictions:
                audit_id = f"contradiction-{slugify(c['page_a'])}-{slugify(c['page_b'])}"
                audit_path_file = audit_dir / f"{audit_id}.md"
                audit_content = f"""---
id: {audit_id}
target: wiki/concepts/{slugify(c['page_a'])}.md
target_lines: []
anchor_before: ""
anchor_text: "{c['conflict'][:50]}"
anchor_after: ""
severity: {c['severity']}
author: lint_wiki.py
source: auto
created: {_dt.date.today().isoformat()}
status: open
---

## Contradiction Report

**Page A:** [[{c['page_a']}]]
**Page B:** [[{c['page_b']}]]

**Conflict:** {c['conflict']}

**Recommendation:** {c['recommendation']}

---
*Auto-generated by lint_wiki.py --llm*
"""
                if dry_run:
                    print(f"  [DRY-RUN] Would create audit: {audit_path_file}")
                else:
                    audit_path_file.write_text(audit_content, encoding="utf-8")
                    print(f"  Created audit entry: {audit_path_file.relative_to(root_path)}")

    return 0 if issues == 0 else 1


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text)
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-").lower()[:60]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("vault", type=Path, nargs="?", default=Path("."))
    parser.add_argument("--llm", action="store_true", help="启用 LLM 语义矛盾检测")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    vault = args.vault.resolve()
    if not vault.exists():
        print(f"ERROR: Vault not found: {vault}", file=sys.stderr)
        sys.exit(1)

    sys.exit(lint(str(vault), use_llm=args.llm, dry_run=args.dry_run, verbose=args.verbose))
