#!/usr/bin/env python3
"""
email_auth.py — Microsoft OAuth2 IMAP 认证（设备码流程）

用户只需打开一个链接、输入代码，就能完成认证。
认证结果缓存到 ~/.email_token_cache.json，后续脚本直接读取。

Usage:
  python3 email_auth.py --account txyjs@hotmail.com
"""

import json, msal, os, sys, time, webbrowser
from pathlib import Path

CACHE_PATH = Path.home() / ".email_token_cache.json"
CLIENT_ID = "4f261cf0-4ee0-4e7c-a849-8e02b81a2d2c"  # 通用 IMAP 客户端（微软官方示例）
SCOPES = [
    "https://outlook.office.com/IMAP.AccessAsUser.All",
    "offline_access",
]

def load_cache():
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text())
    return {}

def save_cache(cache):
    CACHE_PATH.write_text(json.dumps(cache))

def get_token(account: str):
    cache = load_cache()
    app = msal.SerializableTokenCache()
    if cache:
        app.deserialize(cache)

    client = msal.PublicClientApplication(
        CLIENT_ID,
        token_cache=app,
    )

    # 先尝试从缓存获取（检查过期）
    accounts = client.get_accounts(account)
    if accounts:
        result = client.acquire_token_silent(SCOPES, account=accounts[0])
        if result:
            save_cache(app.serialize())
            return result["access_token"]

    # 需要重新认证：设备码流程
    print("\n📋 需要一次性认证，操作如下：\n")
    flow = client.initiate_device_flow(scopes=SCOPES)
    print(f"🔗 打开此链接：{flow['verification_uri']}")
    print(f"🔑 输入此代码：{flow['user_code']}")
    webbrowser.open(flow["verification_uri"])

    result = client.acquire_token_by_device_flow(flow)
    if "access_token" in result:
        save_cache(app.serialize())
        print(f"\n✅ 认证成功！token 已缓存到 {CACHE_PATH}")
        return result["access_token"]
    else:
        print(f"\n❌ 认证失败：{result.get('error_description', result)}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--account", required=True)
    args = parser.parse_args()

    token = get_token(args.account)
    print(f"\nToken 获取成功！长度：{len(token)} 字符")
