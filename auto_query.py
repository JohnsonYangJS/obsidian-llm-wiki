#!/usr/bin/env python3
"""
auto_query.py — 定时将 session 历史中有价值的问答写入 wiki。

每 2 小时运行一次（通过 cron）：
  1. 扫描 ~/.openclaw/agents/main/sessions/ 下最近 2 小时的会话
  2. 解析 user 提问 + assistant 回答，筛选有价值的 Q&A
  3. 用 MiniMax LLM 生成 wiki 摘要页面
  4. 写入 wiki/queries/ 目录

Usage:
    python3 auto_query.py [--dry-run] [--verbose]
"""

import argparse
import datetime as _dt
import json
import os
import re
import sys
import requests
from pathlib import Path

# ── MiniMax LLM ───────────────────────────────────────────────────────────
MINIMAX_API_KEY = "sk-cp-SUjytMlOmz-9qX73aXQbhNog3hEQmYoLxVff1IkOVFCJ_pia4t0ykTJSgp3bQ3aWvmIyIu-HJvNRCZEXHRTL_rFGARGtSpURNHNunmm5yXTucUaLJDH1uaE"
MINIMAX_BASE = "https://api.minimax.chat/v1"

def llm_generate(text: str) -> str:
    prompt = f"""你是一个知识库整理助手。请根据以下问答内容，生成一段中文摘要。

问答内容：
{text}

请输出 JSON 格式（只输出 JSON，不要其他内容）：
{{"summary": "100-200字中文摘要", "title": "适合做页面标题的一句话（不超过30字）", "concepts": ["概念1", "概念2", "概念3"]}}"""

    payload = {
        "model": "MiniMax-M2.7-highspeed",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 600,
        "temperature": 0.3,
        "thinking": {"type": "off"},
    }
    req = urllib.request.Request(
        f"{MINIMAX_BASE}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {MINIMAX_API_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        content = result["choices"][0]["message"]["content"]
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        return json.loads(content)


# ── Session Parser ───────────────────────────────────────────────────────
SESSIONS_DIR = Path.home() / ".openclaw/agents/main/sessions"


def get_substantive_msgs(filepath: Path, min_len: int = 80) -> list[dict]:
    """从 session 文件提取有实质内容的 user→assistant 消息。"""
    messages = []
    try:
        with open(filepath) as f:
            for line in f:
                obj = json.loads(line.strip())
                if obj.get("type") != "message":
                    continue
                msg = obj.get("message", {})
                role = msg.get("role", "")
                content = msg.get("content", "")
                if isinstance(content, list):
                    text = " ".join(
                        c.get("text", "") for c in content
                        if isinstance(c, dict) and c.get("type") == "text"
                    )
                else:
                    text = str(content)
                if role == "assistant" and len(text) >= min_len:
                    # Always keep assistant responses (they contain the actual answers)
                    # Skip image-only messages
                    extra_skip = ("[media attached", "To send an image", "MEDIA:", "/Users/txyjs/.openclaw/media/")
                    if role == "user" and any(k in text[:100] for k in extra_skip):
                        continue
                    messages.append({"role": role, "text": text})
                elif role == "user" and len(text) >= min_len:
                    # Skip system/cron/heartbeat/auto-reply user messages
                    skip_keywords = ("Cron:", "HEARTBEAT", "Heartbeat:", "System:",
                                     "无新文件", "Watch", "[[reply_to", "[cron",
                                     "无待处理", "本次运行", "入库结果")
                    if any(k in text[:200] for k in skip_keywords):
                        continue
                    # Skip image-only messages
                    extra_skip = ("[media attached", "To send an image", "MEDIA:", "/Users/txyjs/.openclaw/media/")
                    if role == "user" and any(k in text[:100] for k in extra_skip):
                        continue
                    messages.append({"role": role, "text": text})
    except (json.JSONDecodeError, OSError):
        pass
    return messages


def extract_qa_pairs(messages: list[dict]) -> list[dict]:
    """从消息流中提取 user→assistant Q&A 对。assistant 回复需要前一条是 user 消息。"""
    pairs = []
    i = 0
    while i < len(messages) - 1:
        if messages[i]['role'] == 'user' and messages[i+1]['role'] == 'assistant':
            q = messages[i]['text'][:500]
            a = messages[i+1]['text'][:2000]
            if len(a) > 80:
                pairs.append({'question': q, 'answer': a})
        i += 1
    return pairs


# ── Wiki Writer ──────────────────────────────────────────────────────────
def slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text)
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-").lower()[:50]


def write_wiki_page(vault: Path, qa: dict, llm_result: dict,
                   dry_run: bool = False) -> Path | None:
    title = llm_result.get("title", qa["question"][:30])
    slug = slugify(title)
    target_dir = vault / "wiki" / "queries"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{slug}.md"

    summary = llm_result.get("summary", "")
    concepts = llm_result.get("concepts", [])

    page = f"""---
title: queries/{slug}
type: query-summary
date: {_dt.date.today().isoformat()}
generation: LLM (MiniMax-M2.7-highspeed)
tags: [{", ".join(concepts[:4])}]
---

# {title}

## 问题

{qa["question"]}

## 回答

{qa["answer"][:1500]}

## AI 摘要

{summary}

## 相关概念

{" · ".join(f"[[{c}]]" for c in concepts[:5])}
"""
    if dry_run:
        print(f"  [DRY-RUN] Would create: {target_path}")
        return None
    target_path.write_text(page, encoding="utf-8")
    return target_path


# ── Main ─────────────────────────────────────────────────────────────────
MANIFEST_PATH = ".query-manifest.json"


def load_manifest(vault: Path) -> dict:
    p = vault / MANIFEST_PATH
    return json.loads(p.read_text()) if p.exists() else {}


def save_manifest(vault: Path, m: dict):
    (vault / MANIFEST_PATH).write_text(json.dumps(m, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("vault", type=Path, nargs="?", default=Path("."))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    vault = args.vault.resolve()

    manifest = load_manifest(vault)
    created = []

    # Scan recent sessions (all files modified in last 48h)
    cutoff = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(hours=48)
    recent_files = []

    if not SESSIONS_DIR.exists():
        print("No sessions directory found.")
        sys.exit(0)

    for f in sorted(SESSIONS_DIR.glob("*.jsonl"), key=lambda x: -x.stat().st_mtime):
        mtime = _dt.datetime.fromtimestamp(f.stat().st_mtime, tz=_dt.timezone.utc)
        if mtime >= cutoff:
            recent_files.append(f)

    if args.verbose:
        print(f"Scanning {len(recent_files)} session file(s) (last 48h)...")

    all_pairs = []
    for sf in recent_files:
        msgs = get_substantive_msgs(sf)
        pairs = extract_qa_pairs(msgs)
        all_pairs.extend(pairs)

    if not all_pairs:
        print("No Q&A pairs found in recent sessions.")
        sys.exit(0)

    if args.verbose:
        print(f"Found {len(all_pairs)} Q&A pair(s).")

    # Deduplicate against manifest
    new_pairs = []
    for qa in all_pairs:
        key = str(hash(qa["question"][:100]))[:16]
        if key not in manifest.get("processed", {}):
            new_pairs.append((key, qa))

    if not new_pairs:
        print("All Q&A already processed.")
        sys.exit(0)

    if args.verbose:
        print(f"Processing {len(new_pairs)} new Q&A...")

    for key, qa in new_pairs:
        text = f"问题：{qa['question']}\n\n回答：{qa['answer']}"
        try:
            llm_result = llm_generate(text)
            path = write_wiki_page(vault, qa, llm_result, dry_run=args.dry_run)
            if path:
                manifest.setdefault("processed", {})[key] = _dt.datetime.now().isoformat()
                created.append(path)
                print(f"  → {path.relative_to(vault)}")
        except Exception as e:
            print(f"  [ERROR] Failed: {e}")

    if not args.dry_run and manifest:
        save_manifest(vault, manifest)

    print(f"\nDone. {'[DRY-RUN] ' if args.dry_run else ''}Created {len(created)} query page(s).")


if __name__ == "__main__":
    main()
