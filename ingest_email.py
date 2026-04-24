#!/usr/bin/env python3
"""
ingest_email.py — 邮件入库脚本

从 IMAP 邮箱抓取 AI 摘要邮件（Superlinear Academy / Team Memo），
提取正文写入 raw/，然后被 auto_ingest.py 处理。

Usage:
  python3 ingest_email.py --account txyjs@hotmail.com --password "APP密码"

Cron 示例（每小时运行）：
  /opt/homebrew/bin/python3 ~/Documents/Obsidian Vault/ingest_email.py \
    --account txyjs@hotmail.com \
    --password "xxxx" \
    --folder AI \
    2>&1

Exit codes:
  0 — success
  1 — no new emails
  2 — error
"""

import argparse
import email
import email.header
import imaplib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from html import parser as html_parser

# ── Config ──────────────────────────────────────────────────────────────────

VAULT_ROOT = Path("/Users/txyjs/Documents/Obsidian Vault")
RAW_DIR = VAULT_ROOT / "raw"
MANIFEST_PATH = VAULT_ROOT / ".ingest-manifest.json"
LOG_DIR = VAULT_ROOT / "log"


# ── Helpers ──────────────────────────────────────────────────────────────────

def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M')}] {msg}", flush=True)


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text)
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-").lower()[:60]


def load_manifest():
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return {"emails": {}, "last_run": None}


def save_manifest(m):
    MANIFEST_PATH.write_text(json.dumps(m, indent=2, ensure_ascii=False))


def append_log(msg: str):
    today = datetime.now().strftime("%Y%m%d")
    log_path = LOG_DIR / f"{today}.md"
    ts = datetime.now().strftime("%H:%M")
    entry = f"\n## [{ts}] email ingest | {msg}"
    if log_path.exists():
        log_path.write_text(log_path.read_text(encoding="utf-8") + entry, encoding="utf-8")
    else:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_path.write_text(f"# {today}\n\n## Daily Log\n{entry}\n", encoding="utf-8")


def decode_header_value(value):
    """解码 email header 编码字符串"""
    parts = email.header.decode_header(value)
    result = []
    for part, charset in parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)


class HTMLTextExtractor(html_parser.HTMLParser):
    """从 HTML 中提取纯文本"""
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip_tags = {'script', 'style', 'head', 'meta', 'link'}
        self.current_tag = None
        self.in_skip = False

    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self.in_skip = True
        self.current_tag = tag

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
        text = "".join(self.text_parts)
        # 清理多余空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()


def extract_email_body(msg) -> str:
    """从 email.message 提取正文"""
    body_text = None
    body_html = None

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = part.get_contentDisposition()

            # 跳过附件
            if content_disposition and "attachment" in content_disposition:
                continue

            if content_type == "text/plain" and body_text is None:
                charset = part.get_content_charset() or "utf-8"
                try:
                    body_text = part.get_payload(decode=True).decode(charset, errors="replace")
                except Exception:
                    pass

            elif content_type == "text/html" and body_html is None:
                charset = part.get_content_charset() or "utf-8"
                try:
                    body_html = part.get_payload(decode=True).decode(charset, errors="replace")
                except Exception:
                    pass
    else:
        content_type = msg.get_content_type()
        charset = msg.get_content_charset() or "utf-8"
        payload = msg.get_payload(decode=True)
        if payload:
            text = payload.decode(charset, errors="replace")
            if content_type == "text/html":
                body_html = text
            else:
                body_text = text

    # 优先用纯文本，fallback 到 HTML
    if body_text:
        return body_text.strip()
    elif body_html:
        extractor = HTMLTextExtractor()
        extractor.feed(body_html)
        return extractor.get_text()
    else:
        return ""


# ── IMAP 连接与拉取 ───────────────────────────────────────────────────────

IMAP_SERVERS = {
    "outlook": ("outlook.office365.com", 993),
    "gmail": ("imap.gmail.com", 993),
    "qq": ("imap.qq.com", 993),
    "163": ("imap.163.com", 993),
}


def get_imap_config(account: str):
    """根据邮箱域名自动选择 IMAP 服务器"""
    domain = account.split("@")[-1].lower()
    if "outlook" in domain or "hotmail" in domain or "live" in domain:
        return IMAP_SERVERS["outlook"]
    elif "gmail" in domain:
        return IMAP_SERVERS["gmail"]
    elif "qq" in domain:
        return IMAP_SERVERS["qq"]
    elif "163" in domain:
        return IMAP_SERVERS["163"]
    else:
        # 默认用 outlook
        return IMAP_SERVERS["outlook"]


def fetch_emails(account: str, password: str, folder: str,
                 senders: list[str], subject_keywords: list[str],
                 dry_run: bool = False):
    """
    连接 IMAP，抓取匹配的邮件
    """
    server, port = get_imap_config(account)
    log(f"Connecting to {server}:{port} ...")

    try:
        mail = imaplib.IMAP4_SSL(server, port)
        mail.login(account, password)
        log(f"Logged in as {account}")
    except Exception as e:
        log(f"❌ IMAP 登录失败: {e}")
        return []

    # 选择文件夹
    try:
        status, _ = mail.select(f'"{folder}"')
        if status != "OK":
            log(f"❌ 无法打开文件夹: {folder}")
            # 尝试 INBOX
            status, _ = mail.select("INBOX")
            if status != "OK":
                log("❌ 无法打开 INBOX")
                mail.logout()
                return []
            log(f"文件夹 '{folder}' 不存在，已切换到 INBOX")
    except Exception as e:
        log(f"❌ 选择文件夹失败: {e}")
        mail.logout()
        return []

    # 搜索邮件（ALL 或 UNSEEN）
    status, messages = mail.search(None, "ALL")
    if status != "OK":
        log("❌ 搜索邮件失败")
        mail.logout()
        return []

    email_ids = messages[0].split()
    if not email_ids:
        log("📭 文件夹为空")
        mail.logout()
        return []

    log(f"共 {len(email_ids)} 封邮件，开始筛选...")

    manifest = load_manifest()
    saved = []
    new_count = 0

    for eid in email_ids:
        try:
            status, raw = mail.fetch(eid, "(RFC822)")
            if status != "OK" or not raw:
                continue

            raw_msg = raw[0][1]
            msg = email.message_from_bytes(raw_msg)

            # 解码主题
            subject_raw = msg.get("Subject", "")
            subject = decode_header_value(subject_raw)

            # 发件人
            sender_raw = msg.get("From", "")
            sender = decode_header_value(sender_raw)

            # 邮件 ID（唯一标识）
            msg_id = msg.get("Message-ID", "") or str(eid)
            message_id_key = f"{account}:{msg_id}"

            # 检查是否已入库
            if message_id_key in manifest.get("emails", {}):
                continue

            # 匹配条件：发件人或主题关键词
            sender_match = any(s.lower() in sender.lower() for s in senders)
            subject_match = any(kw.lower() in subject.lower() for kw in subject_keywords)

            if not (sender_match or subject_match):
                continue

            log(f"  ✅ 匹配: {subject[:50]} | 发件人: {sender[:40]}")

            if dry_run:
                new_count += 1
                continue

            # 提取正文
            body = extract_email_body(msg)
            if not body:
                log(f"  ⚠️ 正文为空，跳过: {subject}")
                continue

            # 生成文件名
            date_str = datetime.now().strftime("%Y%m%d")
            # 用主题前30字做文件名
            safe_subject = slugify(subject)[:30]
            filename = f"email-{date_str}-{safe_subject}.txt"
            filepath = RAW_DIR / filename

            # 防重名
            counter = 1
            while filepath.exists():
                filename = f"email-{date_str}-{safe_subject}-{counter}.txt"
                filepath = RAW_DIR / filename
                counter += 1

            # 写入文件
            raw_content = f"""# {subject}

> **发件人:** {sender}
> **收件时间:** {msg.get("Date", "Unknown")}
> **邮件ID:** {message_id_key}

---

{body}
"""
            filepath.write_text(raw_content, encoding="utf-8")
            log(f"  📄 已保存: {filename}")

            # 记录 manifest
            if "emails" not in manifest:
                manifest["emails"] = {}
            manifest["emails"][message_id_key] = {
                "subject": subject,
                "sender": sender,
                "date": msg.get("Date", ""),
                "filename": filename,
                "saved_at": datetime.now().isoformat(),
            }
            new_count += 1
            saved.append(filename)

        except Exception as e:
            log(f"  ⚠️ 处理邮件失败: {e}")
            continue

    manifest["last_run"] = datetime.now().isoformat()
    save_manifest(manifest)
    mail.logout()

    if dry_run:
        log(f"🔍 干跑模式：匹配到 {new_count} 封新邮件")
    else:
        log(f"✅ 入库完成：{new_count} 封新邮件 → raw/")

    append_log(f"邮箱入库 {new_count} 封新邮件")
    return saved


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="邮件入库脚本")
    parser.add_argument("--account", required=True, help="邮箱地址")
    parser.add_argument("--password", required=True, help="邮箱密码或 App Password")
    parser.add_argument("--folder", default="AI", help="监听的文件夹（默认: AI）")
    parser.add_argument("--senders", nargs="+", default=["Superlinear Academy", "Team Memo"],
                        help="匹配的发件人关键词")
    parser.add_argument("--subject-keywords", nargs="+", default=[],
                        help="额外的主题关键词匹配")
    parser.add_argument("--dry-run", action="store_true", help="干跑模式，不写入文件")
    args = parser.parse_args()

    # 确保 raw 存在
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # 默认关键词
    subject_kws = args.subject_keywords if args.subject_keywords else []

    saved = fetch_emails(
        account=args.account,
        password=args.password,
        folder=args.folder,
        senders=args.senders,
        subject_keywords=subject_kws,
        dry_run=args.dry_run,
    )

    if not saved and not args.dry_run:
        sys.exit(1)  # no new content
    elif not saved and args.dry_run:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
