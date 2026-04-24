#!/usr/bin/env python3
"""
auto_query.py — 定时将 session 历史中有价值的问答写入 wiki。
"""
import argparse, datetime as _dt, json, os, re, subprocess, sys
from pathlib import Path

MINIMAX_API_KEY = "sk-cp-SUjytMlOmz-9qX73aXQbhNog3hEQmYoLxVff1IkOVFCJ_pia4t0ykTJSgp3bQ3aWvmIyIu-HJvNRCZEXHRTL_rFGARGtSpURNHNunmm5yXTucUaLJDH1uaE"
MINIMAX_BASE = "https://api.minimax.chat/v1"
SESSIONS_DIR = Path.home() / ".openclaw/agents/main/sessions"
VAULT_ROOT = Path("/Users/txyjs/Documents/Obsidian Vault")
MANIFEST_PATH = VAULT_ROOT / ".query-manifest.json"


def llm_generate(text: str) -> dict:
    """Call MiniMax LLM to generate summary+title+concepts from Q&A text."""
    prompt = f"""你是一个知识库整理助手。请根据以下问答内容，生成一段中文摘要。
问答内容：
{text}
请输出 JSON 格式（只输出 JSON，不要其他内容）：
{{"summary": "100-200字中文摘要", "title": "适合做页面标题的一句话（不超过30字）", "concepts": ["概念1", "概念2", "概念3"]}}"""
    payload = json.dumps({
        "model": "MiniMax-M2.7-highspeed",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 600,
        "temperature": 0.3,
    })
    proc = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{MINIMAX_BASE}/chat/completions",
         "-H", f"Authorization: Bearer {MINIMAX_API_KEY}",
         "-H", "Content-Type: application/json",
         "-d", payload, "--noproxy", "*", "--max-time", "30"],
        capture_output=True, text=True, timeout=35,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"curl rc={proc.returncode}: {proc.stderr}")
    result = json.loads(proc.stdout)
    raw = result["choices"][0]["message"]["content"]

    # Find first { and extract balanced JSON
    start = raw.find("{")
    if start == -1:
        raise ValueError(f"No JSON found in response: {repr(raw[:100])}")
    json_str = raw[start:]
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
    if end_pos == 0:
        raise ValueError(f"Unbalanced braces in: {repr(raw[start:start+80])}")
    return json.loads(json_str[:end_pos])


def get_substantive_msgs(filepath: Path, min_len: int = 80) -> list:
    messages = []
    try:
        with open(filepath) as f:
            for line in f:
                try:
                    msg = json.loads(line.strip())
                except (json.JSONDecodeError, ValueError):
                    continue
                role = msg.get("role", "")
                content = msg.get("content", "") or ""
                if isinstance(content, list):
                    content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
                if role in ("user", "assistant") and len(content) >= min_len:
                    messages.append({"role": role, "content": content})
    except Exception:
        pass
    return messages


def extract_qa_pairs(messages: list, max_pairs: int = 5) -> list:
    pairs = []
    for i in range(len(messages) - 1):
        if messages[i]["role"] == "user" and messages[i + 1]["role"] == "assistant":
            q, a = messages[i]["content"].strip(), messages[i + 1]["content"].strip()
            if len(q) >= 20 and len(a) >= 40:
                pairs.append((q, a))
                if len(pairs) >= max_pairs:
                    break
    return pairs


def slugify(title: str) -> str:
    s = re.sub(r"[^\w\s\u4e00-\u9fff-]", "", title)
    s = re.sub(r"[\s]+", "-", s).strip("-")
    return s[:60] or "untitled"


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH) as f:
            return json.load(f)
    return {}


def save_manifest(manifest: dict):
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def write_wiki_page(title: str, summary: str, concepts: list, qa_pairs: list, out_dir: Path) -> str:
    date = _dt.datetime.now().strftime("%Y-%m-%d")
    filename = f"{date}-{slugify(title)}.md"
    filepath = out_dir / filename
    qa_md = "".join(f"**Q:** {q}\n\n**A:** {a}\n\n---\n\n" for q, a in qa_pairs[:3])
    concepts_md = ", ".join(f"[[{c}]]" for c in concepts)
    content = f"""---
type: query-summary
title: {title}
date: {date}
concepts: {concepts_md}
generation: LLM (MiniMax)
---

# {title}

{summary}

## 相关问答

{qa_md}## 相关概念

{concepts_md}

---
*由 auto_query.py 自动生成于 {date}*
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    index_path = out_dir / "index.md"
    entry = f"- [{title}]({filename}) — {date}"
    if index_path.exists():
        existing = index_path.read_text()
        if filename not in existing:
            with open(index_path, "a") as f:
                f.write(entry + "\n")
    else:
        with open(index_path, "w") as f:
            f.write("# 问答摘要索引\n\n" + entry + "\n")
    return filename


def main():
    args = argparse.ArgumentParser().parse_args()
    cutoff = _dt.datetime.now() - _dt.timedelta(hours=48)
    recent_files = [f for f in SESSIONS_DIR.iterdir() if f.is_file() and f.stat().st_mtime > cutoff.timestamp()]
    print(f"Found {len(recent_files)} recent session files")
    manifest = load_manifest()
    written = 0
    for filepath in sorted(recent_files):
        messages = get_substantive_msgs(filepath)
        qa_pairs = extract_qa_pairs(messages)
        for q, a in qa_pairs:
            key = f"{filepath.stem}:{hash(q) % 100000}"
            if key in manifest:
                continue
            try:
                result = llm_generate(f"问题：{q}\n\n回答：{a}")
                out_dir = VAULT_ROOT / "wiki" / "queries"
                out_dir.mkdir(parents=True, exist_ok=True)
                filename = write_wiki_page(result["title"], result["summary"], result.get("concepts", []), [(q, a)], out_dir)
                manifest[key] = {"title": result["title"], "file": filename}
                written += 1
                print(f"  Wrote: {filename}")
            except Exception as ex:
                print(f"  ERROR: {q[:40]}... → {ex}")
    save_manifest(manifest)
    print(f"Done. Written: {written} new Q&A pages.")


if __name__ == "__main__":
    main()
