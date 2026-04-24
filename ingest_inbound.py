#!/usr/bin/env python3
"""
ingest_inbound.py — 多渠道内容入库脚本

支持 5 个渠道：
  1. 飞书文件下载        --channel feishu [--chat-id ID] [--since MINUTES]
  2. 飞书云文档抓取       --channel feishu-doc --url URL
  3. URL 内容抓取         --channel url --url URL [--title TITLE]
  4. raw/ 目录监控       --channel watcher [--watch-dir DIR]
  5. 邮件入库            --channel email --account --folder --password

Usage:
  python3 ingest_inbound.py --channel feishu --chat-id oc_xxx
  python3 ingest_inbound.py --channel feishu-doc --url "https://xxx.feishu.cn/docx/xxx"
  python3 ingest_inbound.py --channel url --url "https://example.com/article" --title "Article Title"
  python3 ingest_inbound.py --channel watcher --watch-dir /path/to/raw

Exit codes:
  0 — success
  1 — no new content
  2 — error
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

# ── Config ──────────────────────────────────────────────────────────────────

VAULT_ROOT = Path("/Users/txyjs/Documents/Obsidian Vault")
RAW_DIR = VAULT_ROOT / "raw"
LOG_DIR = VAULT_ROOT / "log"
MANIFEST_PATH = VAULT_ROOT / ".ingest-manifest.json"
FEISHU_COOKIE_PATH = Path.home() / ".openclaw" / "extensions" / "feishu-openclaw-plugin" / "state" / "user_auth_state.json"

# ── Helpers ────────────────────────────────────────────────────────────────

def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M')}] {msg}", flush=True)


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text)
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-").lower()[:60]


def load_manifest():
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return {"feishu_files": {}, "urls": {}, "last_run": None}


def save_manifest(m):
    MANIFEST_PATH.write_text(json.dumps(m, indent=2, ensure_ascii=False))


def append_log(msg: str):
    today = datetime.now().strftime("%Y%m%d")
    log_path = LOG_DIR / f"{today}.md"
    ts = datetime.now().strftime("%H:%M")
    entry = f"\n## [{ts}] ingest | {msg}"
    if log_path.exists():
        log_path.write_text(log_path.read_text(encoding="utf-8") + entry, encoding="utf-8")
    else:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_path.write_text(f"# {today}\n\n## Daily Log\n{entry}\n", encoding="utf-8")


# ── Channel 1: 飞书文件下载 ─────────────────────────────────────────────────

FEISHU_API_BASE = "https://open.feishu.cn/open-apis"


def get_feishu_token() -> str:
    """从飞书插件状态文件获取用户 token。"""
    if not FEISHU_COOKIE_PATH.exists():
        return os.environ.get("FEISHU_USER_TOKEN", "")
    try:
        state = json.loads(FEISHU_COOKIE_PATH.read_text())
        # 尝试多个可能的 token 字段
        for key in ["user_access_token", "access_token", "token"]:
            if key in state:
                return state[key]
    except Exception:
        pass
    return os.environ.get("FEISHU_USER_TOKEN", "")


def feishu_api(path: str, token: str, params: dict = None) -> dict:
    """调用飞书 API。"""
    import urllib.request
    url = FEISHU_API_BASE + path
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def download_file(url: str, token: str, output_path: Path) -> bool:
    """下载飞书文件到本地。"""
    try:
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=30) as r:
            content = r.read()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(content)
        return True
    except Exception as e:
        log(f"下载失败: {e}")
        return False


def channel_feishu(chat_id: str = None, since_minutes: int = 30, dry_run: bool = False):
    """
    检查飞书群/私聊的新文件，下载到 raw/。
    通过 feishu_im_user_get_messages API（以用户身份）。
    """
    token = get_feishu_token()
    if not token:
        log("⚠️  未找到飞书 token，跳过飞书渠道")
        log("   提示：在飞书给机器人发文件时，AI 会自动处理，无需 Cron")
        return

    manifest = load_manifest()
    since_time = datetime.now().timestamp() - since_minutes * 60
    downloaded = []

    try:
        # 获取消息列表
        params = {"container_id_type": "chat", "container_id": chat_id,
                  "start_time": str(int(since_time)), "page_size": "50"}
        result = feishu_api("/im/v1/messages", token, params)
        messages = result.get("data", {}).get("items", [])
    except Exception as e:
        log(f"获取飞书消息失败: {e}")
        return

    for msg in messages:
        msg_id = msg.get("message_id", "")
        msg_type = msg.get("msg_type", "")
        create_time = int(msg.get("create_time", 0))
        if create_time < int(since_time):
            continue

        # 只处理文件类型
        if msg_type != "file":
            continue

        # 检查是否已处理
        ingested = manifest.get("feishu_files", {})
        if ingested.get(msg_id):
            continue

        # 提取文件信息
        try:
            content = json.loads(msg.get("body", {}).get("content", "{}"))
        except Exception:
            continue

        file_key = content.get("file_key", "")
        file_name = content.get("file_name", f"feishu-{msg_id}.bin")
        file_size = content.get("file_size", 0)

        # 跳过超大文件
        if file_size > 50 * 1024 * 1024:
            log(f"跳过超大文件: {file_name} ({file_size//1024//1024}MB)")
            continue

        # 生成保存路径
        date_prefix = datetime.now().strftime("%Y%m%d")
        stem = slugify(Path(file_name).stem)
        target = RAW_DIR / f"{date_prefix}-{stem}{Path(file_name).suffix}"

        if dry_run:
            log(f"[DRY-RUN] 下载文件: {file_name} → {target}")
            continue

        # 下载文件
        download_url = f"{FEISHU_API_BASE}/im/v1/files/{file_key}"
        if download_file(download_url, token, target):
            log(f"✅ 飞书文件入库: {file_name} → {target.relative_to(VAULT_ROOT)}")
            manifest["feishu_files"][msg_id] = str(target)
            downloaded.append(str(target.relative_to(VAULT_ROOT)))

    save_manifest(manifest)

    if downloaded:
        append_log(f"飞书入库 {len(downloaded)} 个文件: {', '.join(downloaded)}")
        # 触发 auto_ingest
        subprocess.Popen(
            [sys.executable, str(VAULT_ROOT / "auto_ingest.py"), str(VAULT_ROOT)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        log(f"触发 auto_ingest 处理 {len(downloaded)} 个新文件")
    else:
        log("飞书: 无新文件")


# ── Channel 2: 飞书云文档抓取 ───────────────────────────────────────────────

def channel_feishu_doc(url: str, dry_run: bool = False):
    """
    抓取飞书云文档/多维表格内容，保存为 .md 到 raw/
    使用飞书 API 直接读取文档内容（无需用户 OAuth）。
    """
    # 解析文档 token
    # https://xxx.feishu.cn/docx/xxx  或  https://xxx.feishu.cn/wiki/xxx
    token_match = re.search(r"(?:docx|wiki|sheets|bitable)/([a-zA-Z0-9]+)", url)
    if not token_match:
        log(f"无法从 URL 解析文档 token: {url}")
        return

    doc_token = token_match.group(1)
    if "wiki" in url:
        doc_type = "wiki"
    elif "sheets" in url:
        doc_type = "sheet"
    elif "bitable" in url:
        doc_type = "bitable"
    else:
        doc_type = "docx"

    app_token = get_feishu_app_token()
    if not app_token:
        log("⚠️  未找到飞书 App Token，请确保应用已配置正确")
        return

    if doc_type in ("docx", "wiki"):
        content = fetch_feishu_docx(app_token, doc_token)
    elif doc_type == "sheet":
        content = fetch_feishu_sheet(app_token, doc_token)
    else:
        content = fetch_feishu_bitabl(app_token, doc_token)

    if not content:
        log(f"飞书文档抓取失败: {url}")
        return

    title = content.get("title", slugify(url))
    body = content.get("content", "")
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    slug = slugify(title)
    target = RAW_DIR / "articles" / f"feishu-{slug}.md"
    target.parent.mkdir(parents=True, exist_ok=True)

    page = f"""---
title: {title}
type: article
source_type: feishu-doc
source_url: "{url}"
date: {date}
ingested: {date}
tags: [feishu]
---

# {title}

**Source**: [飞书文档]({url}) · {date}

{body}
"""

    if dry_run:
        log(f"[DRY-RUN] 保存飞书文档: {title} → {target}")
        return

    target.write_text(page, encoding="utf-8")
    log(f"✅ 飞书文档入库: {title} → {target.relative_to(VAULT_ROOT)}")
    append_log(f"飞书云文档入库: {title} → raw/articles/feishu-{slug}.md")
    subprocess.Popen(
        [sys.executable, str(VAULT_ROOT / "auto_ingest.py"), str(VAULT_ROOT)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


def get_feishu_app_token() -> str:
    """获取飞书应用 Access Token（App ID + App Secret）。"""
    config_path = Path("/Users/txyjs/.openclaw/openclaw.json")
    if not config_path.exists():
        return ""
    try:
        cfg = json.loads(config_path.read_text())
        app_id = cfg.get("channels", {}).get("feishu", {}).get("appId", "")
        app_secret = cfg.get("channels", {}).get("feishu", {}).get("appSecret", "")
        if not app_id or not app_secret:
            return ""
        req = urllib.request.Request(
            f"{FEISHU_API_BASE}/auth/v3/tenant_access_token/internal",
            data=json.dumps({"app_id": app_id, "app_secret": app_secret}).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
            return result.get("tenant_access_token", "")
    except Exception:
        return ""


def fetch_feishu_docx(app_token: str, doc_token: str) -> dict:
    """获取飞书云文档正文（纯文本提取）。"""
    try:
        req = urllib.request.Request(
            f"{FEISHU_API_BASE}/docx/v1/documents/{doc_token}",
            headers={"Authorization": f"Bearer {app_token}"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            meta = json.loads(r.read())
            title = meta.get("data", {}).get("document", {}).get("title", "")

        req2 = urllib.request.Request(
            f"{FEISHU_API_BASE}/docx/v1/documents/{doc_token}/raw_content",
            headers={"Authorization": f"Bearer {app_token}"}
        )
        with urllib.request.urlopen(req2, timeout=15) as r:
            raw = json.loads(r.read())
            content = raw.get("data", {}).get("raw_text", "")

        return {"title": title, "content": content}
    except Exception as e:
        log(f"飞书文档 API 失败: {e}")
        return {}


def fetch_feishu_sheet(app_token: str, doc_token: str) -> dict:
    """获取飞书电子表格内容。"""
    try:
        req = urllib.request.Request(
            f"{FEISHU_API_BASE}/sheets/v3/spreadsheets/{doc_token}/sheets/query",
            headers={"Authorization": f"Bearer {app_token}"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            sheets = json.loads(r.read()).get("data", {}).get("sheets", [])

        all_content = []
        for sheet in sheets[:3]:  # 只取前3个 sheet
            sheet_id = sheet.get("sheet_id", "")
            req2 = urllib.request.Request(
                f"{FEISHU_API_BASE}/sheets/v3/spreadsheets/{doc_token}/values/{sheet_id}!A1:Z100",
                headers={"Authorization": f"Bearer {app_token}"}
            )
            with urllib.request.urlopen(req2, timeout=10) as r2:
                data = json.loads(r2.read()).get("data", {}).get("valueRange", {}).get("values", [])
            for row in data[:50]:  # 每 sheet 取前50行
                row_text = " | ".join(str(c or "") for c in row)
                if row_text.strip():
                    all_content.append(row_text)

        return {"title": doc_token, "content": "\n".join(all_content)}
    except Exception as e:
        return {}


def fetch_feishu_bitabl(app_token: str, doc_token: str) -> dict:
    """获取飞书多维表格数据。"""
    try:
        req = urllib.request.Request(
            f"{FEISHU_API_BASE}/bitable/v1/apps/{doc_token}/tables",
            headers={"Authorization": f"Bearer {app_token}"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            tables = json.loads(r.read()).get("data", {}).get("items", [])

        all_content = []
        for tbl in tables[:5]:  # 前5个表
            tbl_id = tbl.get("table_id", "")
            tbl_name = tbl.get("name", "")
            all_content.append(f"\n## {tbl_name}\n")

            req2 = urllib.request.Request(
                f"{FEISHU_API_BASE}/bitable/v1/apps/{doc_token}/tables/{tbl_id}/records?page_size=20",
                headers={"Authorization": f"Bearer {app_token}"}
            )
            try:
                with urllib.request.urlopen(req2, timeout=10) as r2:
                    records = json.loads(r2.read()).get("data", {}).get("items", [])
                for rec in records[:20]:
                    fields = rec.get("fields", {})
                    row = " | ".join(f"{k}: {v}" for k, v in fields.items() if v)
                    if row:
                        all_content.append(f"- {row}")
            except Exception:
                pass

        return {"title": doc_token, "content": "\n".join(all_content)}
    except Exception as e:
        return {}


# ── Channel 3: URL 内容抓取 ─────────────────────────────────────────────────

def channel_url(url: str, title: str = None, dry_run: bool = False):
    """
    抓取任意 URL 内容，保存到 raw/
    """
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="ignore")

        # 简单 HTML → 文本提取
        import re
        # 移除 script/style
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)
        # 换行处理
        html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
        # 移除标签
        text = re.sub(r"<[^>]+>", "", html)
        # 清理空白
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()[:3000]  # 限制长度

        if not title:
            m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
            title = m.group(1).strip() if m else slugify(url)

        slug = slugify(title)
        target = RAW_DIR / "articles" / f"url-{slug}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        page = f"""---
title: {title}
type: article
source_type: url
source_url: "{url}"
date: {date}
ingested: {date}
tags: [web]
---

# {title}

**Source**: [{url}]({url}) · {date}

{text}
"""

        if dry_run:
            log(f"[DRY-RUN] 保存 URL: {title} → {target}")
            return

        target.write_text(page, encoding="utf-8")
        log(f"✅ URL 入库: {title} → {target.relative_to(VAULT_ROOT)}")
        append_log(f"URL 入库: {title} → raw/articles/url-{slug}.md")
        subprocess.Popen(
            [sys.executable, str(VAULT_ROOT / "auto_ingest.py"), str(VAULT_ROOT)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception as e:
        log(f"URL 抓取失败: {e}")


# ── Channel 4: raw/ 目录监控 ─────────────────────────────────────────────────

def channel_watcher(watch_dir: str = None, dry_run: bool = False):
    """
    监控 raw/ 和 Clippings/ 目录新增文件，触发 auto_ingest
    基于 mtime 检测上次运行后新增的文件
    """
    watch_dirs = [Path(watch_dir)] if watch_dir else [RAW_DIR, RAW_DIR.parent / "Clippings"]
    manifest = load_manifest()
    last_mtime = float(manifest.get("watcher_mtime", 0))

    new_files = []
    for wd in watch_dirs:
        if not wd.exists():
            continue
        for f in wd.rglob("*"):
            if f.is_file() and f.suffix in (".md", ".txt") and f.stat().st_mtime > last_mtime:
                new_files.append(f)

    if not new_files:
        log("watcher: 无新文件")
        return

    # Move Clippings files to raw/articles/
    clippings_dir = RAW_DIR.parent / "Clippings"
    for f in list(new_files):
        if f.parent == clippings_dir:
            target = RAW_DIR / "articles" / f.name
            if not dry_run:
                import shutil
                shutil.copy2(f, target)
                log(f"  从 Clippings 迁移: {f.name} → raw/articles/")
            else:
                log(f"  [DRY-RUN] 迁移: {f.name}")
            new_files = [target if x == f else x for x in new_files]

    manifest["watcher_mtime"] = datetime.now().timestamp()
    save_manifest(manifest)

    log(f"watcher: 检测到 {len(new_files)} 个新/变更文件")
    if not dry_run:
        result = subprocess.run(
            [sys.executable, str(VAULT_ROOT / "auto_ingest.py"), str(VAULT_ROOT)],
            capture_output=True, text=True
        )
        log(f"auto_ingest: {result.stdout.strip().splitlines()[-1] if result.stdout else 'done'}")

    return new_files


# ── Channel 5: 邮件入库 ────────────────────────────────────────────────────

def channel_email(account: str, password: str, folder: str = "AI",
                  senders: list = None, subject_keywords: list = None,
                  dry_run: bool = False):
    """
    从 IMAP 邮箱抓取 AI 摘要邮件，写入 raw/
    """
    import email, email.header, imaplib, re
    from html import parser as html_parser

    if senders is None:
        senders = ["Superlinear Academy", "Team Memo"]
    if subject_keywords is None:
        subject_keywords = []

    log(f"📧 邮件入库: {account} / {folder}")

    # ── HTML 提取器 ────────────────────────────────────────────────────────
    class HTMLTextExtractor(html_parser.HTMLParser):
        def __init__(self):
            super().__init__()
            self.text_parts = []
            self.skip_tags = {'script', 'style', 'head', 'meta', 'link'}
            self.in_skip = False

        def handle_starttag(self, tag, attrs):
            if tag in self.skip_tags:
                self.in_skip = True
        def handle_endtag(self, tag):
            if tag in self.skip_tags:
                self.in_skip = False
            if tag == 'br':
                self.text_parts.append('\n')
            if tag == 'p':
                self.text_parts.append('\n\n')
        def handle_data(self, data):
            if not self.in_skip:
                self.text_parts.append(data)
        def get_text(self):
            return re.sub(r'\n{3,}', '\n\n', "".join(self.text_parts)).strip()

    def decode_header_value(value):
        parts = email.header.decode_header(value)
        result = []
        for part, charset in parts:
            if isinstance(part, bytes):
                result.append(part.decode(charset or "utf-8", errors="replace"))
            else:
                result.append(part)
        return "".join(result)

    def extract_body(msg) -> str:
        body_text, body_html = None, None
        if msg.is_multipart():
            for part in msg.walk():
                ct = part.get_content_type()
                cd = part.get_contentDisposition()
                if cd and "attachment" in cd:
                    continue
                charset = part.get_content_charset() or "utf-8"
                payload = part.get_payload(decode=True)
                if not payload:
                    continue
                text = payload.decode(charset, errors="replace")
                if ct == "text/plain" and body_text is None:
                    body_text = text
                elif ct == "text/html" and body_html is None:
                    body_html = text
        else:
            charset = msg.get_content_charset() or "utf-8"
            payload = msg.get_payload(decode=True)
            if payload:
                text = payload.decode(charset, errors="replace")
                if msg.get_content_type() == "text/html":
                    body_html = text
                else:
                    body_text = text
        if body_text:
            return body_text.strip()
        elif body_html:
            ex = HTMLTextExtractor()
            ex.feed(body_html)
            return ex.get_text()
        return ""

    # ── IMAP 连接 ──────────────────────────────────────────────────────────
    domain = account.split("@")[-1].lower()
    if "outlook" in domain or "hotmail" in domain or "live" in domain:
        server, port = "outlook.office365.com", 993
    elif "gmail" in domain:
        server, port = "imap.gmail.com", 993
    else:
        server, port = "outlook.office365.com", 993

    try:
        mail = imaplib.IMAP4_SSL(server, port)
        mail.login(account, password)
        log(f"✅ 登录成功: {account}")
    except Exception as e:
        log(f"❌ IMAP 登录失败: {e}")
        return []

    try:
        status, _ = mail.select(f'"{folder}"')
        if status != "OK":
            status, _ = mail.select("INBOX")
            if status != "OK":
                log("❌ 无法打开文件夹")
                mail.logout()
                return []
            log(f"文件夹 '{folder}' 不存在，已切换到 INBOX")
    except Exception as e:
        log(f"❌ 选择文件夹失败: {e}")
        mail.logout()
        return []

    status, messages = mail.search(None, "ALL")
    if status != "OK":
        log("❌ 搜索失败")
        mail.logout()
        return []

    email_ids = messages[0].split()
    if not email_ids:
        log("📭 文件夹为空")
        mail.logout()
        return []

    manifest = load_manifest()
    new_count = 0

    for eid in email_ids:
        try:
            status, raw = mail.fetch(eid, "(RFC822)")
            if status != "OK" or not raw:
                continue
            msg = email.message_from_bytes(raw[0][1])
            subject = decode_header_value(msg.get("Subject", ""))
            sender = decode_header_value(msg.get("From", ""))
            msg_id = msg.get("Message-ID", "") or str(eid)
            key = f"{account}:{msg_id}"

            if key in manifest.get("emails", {}):
                continue

            sender_match = any(s.lower() in sender.lower() for s in senders)
            subject_match = any(kw.lower() in subject.lower() for kw in subject_keywords)
            if not (sender_match or subject_match):
                continue

            log(f"  ✅ 匹配: {subject[:50]}")

            if dry_run:
                new_count += 1
                continue

            body = extract_body(msg)
            if not body:
                log(f"  ⚠️ 正文为空: {subject[:30]}")
                continue

            date_str = datetime.now().strftime("%Y%m%d")
            safe_subject = re.sub(r"[^\w\s-]", "", subject)
            safe_subject = re.sub(r"[\s_]+", "-", safe_subject).strip("-").lower()[:30]
            filename = f"email-{date_str}-{safe_subject}.txt"
            filepath = RAW_DIR / filename
            counter = 1
            while filepath.exists():
                filename = f"email-{date_str}-{safe_subject}-{counter}.txt"
                filepath = RAW_DIR / filename
                counter += 1

            content = f"""# {subject}

> **发件人:** {sender}
> **收件时间:** {msg.get("Date", "Unknown")}
> **邮件ID:** {key}

---

{body}
"""
            filepath.write_text(content, encoding="utf-8")
            log(f"  📄 已保存: {filename}")

            if "emails" not in manifest:
                manifest["emails"] = {}
            manifest["emails"][key] = {
                "subject": subject, "sender": sender,
                "filename": filename, "saved_at": datetime.now().isoformat(),
            }
            new_count += 1

        except Exception as e:
            log(f"  ⚠️ 处理失败: {e}")
            continue

    manifest["last_run"] = datetime.now().isoformat()
    save_manifest(manifest)
    mail.logout()

    if dry_run:
        log(f"🔍 干跑: 匹配到 {new_count} 封新邮件")
    else:
        log(f"✅ 入库完成: {new_count} 封新邮件 → raw/")
        append_log(f"邮件入库 {new_count} 封")

    # 触发 auto_ingest
    if new_count > 0 and not dry_run:
        subprocess.Popen(
            [sys.executable, str(VAULT_ROOT / "auto_ingest.py"), str(VAULT_ROOT)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    return new_count


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="多渠道内容入库")
    parser.add_argument("--channel", choices=["feishu", "feishu-doc", "url", "watcher", "email"],
                        required=True, help="入库渠道")
    parser.add_argument("--chat-id", help="飞书 chat_id (feishu 渠道)")
    parser.add_argument("--since", type=int, default=30, help="回查分钟数 (feishu 渠道)")
    parser.add_argument("--url", help="目标 URL (feishu-doc / url 渠道)")
    parser.add_argument("--title", help="文章标题 (url 渠道)")
    parser.add_argument("--watch-dir", help="监控目录 (watcher 渠道)")
    parser.add_argument("--account", help="邮箱地址 (email 渠道)")
    parser.add_argument("--password", help="邮箱密码或 App Password (email 渠道)")
    parser.add_argument("--folder", default="AI", help="邮件文件夹 (email 渠道，默认: AI)")
    parser.add_argument("--senders", nargs="+", help="匹配发件人 (email 渠道)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.channel == "feishu":
        channel_feishu(chat_id=args.chat_id, since_minutes=args.since, dry_run=args.dry_run)
    elif args.channel == "feishu-doc":
        if not args.url:
            print("ERROR: --url required for feishu-doc channel", file=sys.stderr)
            sys.exit(2)
        channel_feishu_doc(args.url, dry_run=args.dry_run)
    elif args.channel == "url":
        if not args.url:
            print("ERROR: --url required for url channel", file=sys.stderr)
            sys.exit(2)
        channel_url(args.url, title=args.title, dry_run=args.dry_run)
    elif args.channel == "watcher":
        channel_watcher(watch_dir=args.watch_dir, dry_run=args.dry_run)
    elif args.channel == "email":
        if not args.account or not args.password:
            print("ERROR: --account and --password required for email channel", file=sys.stderr)
            sys.exit(2)
        channel_email(
            account=args.account, password=args.password,
            folder=args.folder, senders=args.senders or None,
            dry_run=args.dry_run,
        )


if __name__ == "__main__":
    main()
