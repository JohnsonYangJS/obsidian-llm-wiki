#!/usr/bin/env python3
"""auto_query.py — 定时将 session 历史中有价值的问答写入 wiki。"""
import argparse, datetime as _dt, json, os, re, subprocess, sys, time
from pathlib import Path

MINIMAX_API_KEY = "sk-cp-SUjytMlOmz-9qX73aXQbhNog3hEQmYoLxVff1IkOVFCJ_pia4t0ykTJSgp3bQ3aWvmIyIu-HJvNRCZEXHRTL_rFGARGtSpURNHNunmm5yXTucUaLJDH1uaE"
MINIMAX_BASE = "https://api.minimax.chat/v1"
SESSIONS_DIR = Path.home() / ".openclaw/agents/main/sessions"
VAULT_ROOT = Path("/Users/txyjs/Documents/Obsidian Vault")
MANIFEST_PATH = VAULT_ROOT / ".query-manifest.json"


def extract_json(raw: str) -> dict:
    """Try multiple strategies to extract JSON from raw LLM response.
    
    Handles:
    - Case A: clean JSON (no thinking) → find { and balance braces
    - Case B: with  thinking tags → strip content before the closing tag
    - Case C: with 「 Christensen... Christensen」 thinking tags (fullwidth quotes)
      → extract from after the LAST closing marker
    """
    text = raw.strip()
    
    # Case B/C: strip thinking tags
    # Standard XML-style:  ... 
    # Also handle fullwidth Japanese quote variant: 「 Christensen... Christensen」
    
    # Strategy: find the last  Christensen or the last  Christensen
    # and extract content after it
    # Strip thinking tags: standard XML-style  ... 
    # Find the last  Christensen (closing tag) and extract content after it
    last_thinking_close = text.rfind(" Christensen")
    if last_thinking_close != -1:
        text = text[last_thinking_close + len(" Christensen"):].lstrip()
    else:
        # Fallback: fullwidth quote variant: 「 Christensen... Christensen」
        last_marker_pos = text.rfind(" Christensen")
        if last_marker_pos != -1:
            text = text[last_marker_pos + len(" Christensen"):].lstrip()
    
    # Case A: find first { and balance braces
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


def llm_generate(text: str) -> dict:
    prompt = (
        "你是一个知识库整理助手。请根据以下问答内容，生成一段中文摘要。\n"
        f"问答内容：\n{text}\n"
        "请直接输出 JSON，包含三个字段：summary（100-200字中文摘要）、title（不超过30字的中文标题）、concepts（包含3个概念的列表）。只输出 JSON，不要其他内容。"
    )
    payload = json.dumps({
        "model": "MiniMax-M2.7-highspeed",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1200,
        "temperature": 0.1,
    })

    for attempt in range(3):
        proc = subprocess.run(
            ["curl", "-s", "-X", "POST", f"{MINIMAX_BASE}/chat/completions",
             "-H", f"Authorization: Bearer {MINIMAX_API_KEY}",
             "-H", "Content-Type: application/json",
             "-d", payload, "--noproxy", "*", "--max-time", "30"],
            capture_output=True, text=True, timeout=35,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"curl rc={proc.returncode}: {proc.stderr}")
        raw = json.loads(proc.stdout)["choices"][0]["message"]["content"]
        try:
            return extract_json(raw)
        except ValueError:
            if attempt < 2:
                time.sleep(1)
                continue
            raise


def get_substantive_msgs(filepath: Path, min_len: int = 80) -> list:
    """从 session JSONL 提取 user/assistant 消息（新版格式）。"""
    messages = []
    try:
        with open(filepath) as f:
            for line in f:
                try:
                    msg = json.loads(line.strip())
                except (json.JSONDecodeError, ValueError):
                    continue
                # 新版格式: role/content 在 msg["message"] 里
                inner = msg.get("message", {})
                if not inner:
                    continue
                role = inner.get("role", "")
                if role not in ("user", "assistant"):
                    continue
                raw_content = inner.get("content", "") or ""
                # content 可能是 JSON 字符串列表
                if isinstance(raw_content, str):
                    try:
                        blocks = json.loads(raw_content)
                    except (json.JSONDecodeError, ValueError):
                        blocks = [{"type": "text", "text": raw_content}]
                elif isinstance(raw_content, list):
                    blocks = raw_content
                else:
                    blocks = []
                content = " ".join(
                    b.get("text", "") for b in blocks
                    if isinstance(b, dict) and b.get("type") == "text" and b.get("text")
                )
                # Skip system/Cron/heartbeat messages
                if content.startswith("System:") or content.startswith("[cron:") or                    content.startswith("[media attached:") or                    content.startswith("HEARTBEAT"):
                    continue
                if len(content) >= min_len:
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    # 只扫最后一个 session 文件（当前对话），避免被噪音淹没
    all_files = sorted([f for f in SESSIONS_DIR.iterdir() if f.is_file()],
                        key=lambda f: f.stat().st_mtime, reverse=True)
    recent_files = [all_files[0]] if all_files else []
    print(f"Scanning last session: {recent_files[0].name if recent_files else 'none'}")
    manifest = load_manifest()
    written = 0
    for filepath in sorted(recent_files):
        messages = get_substantive_msgs(filepath)
        qa_pairs = extract_qa_pairs(messages)
        for q, a in qa_pairs:
            key = f"{filepath.stem}:{hash(q) % 100000}"
            if key in manifest:
                continue
            if args.dry_run:
                print(f"  [dry-run] would process: {q[:50]}...")
                manifest[key] = True
                continue
            try:
                result = llm_generate(f"问题：{q}\n\n回答：{a}")
                # Skip placeholder responses
                title = result.get("title", "")
                summary = result.get("summary", "")
                if not summary or len(summary) < 15:
                    print(f"  SKIP (placeholder): summary={repr(summary[:50])}")
                    print(f"  SKIP (placeholder): title={repr(title)}")
                    manifest[key] = True
                    continue
                out_dir = VAULT_ROOT / "wiki" / "queries"
                out_dir.mkdir(parents=True, exist_ok=True)
                filename = write_wiki_page(result["title"], result["summary"],
                                        result.get("concepts", []), [(q, a)], out_dir)
                manifest[key] = {"title": result["title"], "file": filename}
                written += 1
                print(f"  Wrote: {filename}")
            except Exception as ex:
                print(f"  ERROR: {q[:40]}... → {ex}")
    save_manifest(manifest)
    print(f"Done. Written: {written} new Q&A pages.")


if __name__ == "__main__":
    main()
