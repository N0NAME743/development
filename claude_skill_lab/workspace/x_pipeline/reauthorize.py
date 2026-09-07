#!/usr/bin/env python3
"""X (Twitter) OAuth2 Authorization Code + PKCE 再認可ヘルパー。

x_likes_to_notion.py用のAccess/Refresh Tokenが失効した場合に実行し、
.envのX_ACCESS_TOKEN / X_REFRESH_TOKENだけを新しい値に書き換える
（X_CLIENT_ID / X_CLIENT_SECRETは既存の値をそのまま使う。アプリの
再登録は不要）。

前提: X Developer PortalのこのアプリのUser authentication settingsで
Callback URI / Redirect URLに http://127.0.0.1:8080/callback が
登録されていること。

使い方:
  Pi上でブラウザが使えるなら、Pi上でこのまま実行してURLを開く。
  使えない場合は、手元のPCから

    ssh -L 8080:localhost:8080 <user>@<pi-host>

  でこのポートをフォワードした上で、手元のブラウザで表示されたURLを開く
  （コールバックはこのポート経由でPi側のこのスクリプトへ届く）。

  1. python3 reauthorize.py
  2. 表示されたURLをブラウザで開き、Xでログイン・アプリを承認
  3. 承認後、自動的にコールバックを受け取り、.envを更新して終了する
"""

import base64
import hashlib
import os
import secrets
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

REDIRECT_URI = "http://127.0.0.1:8080/callback"
CALLBACK_HOST = "127.0.0.1"
CALLBACK_PORT = 8080

# x_likes_to_notion.pyが必要とする範囲のみ（読み取り専用）。
# offline.accessが無いとrefresh_tokenが発行されない。
SCOPES = "tweet.read users.read like.read offline.access"

load_dotenv(ENV_PATH)

X_CLIENT_ID = os.getenv("X_CLIENT_ID")
X_CLIENT_SECRET = os.getenv("X_CLIENT_SECRET")

if not X_CLIENT_ID or not X_CLIENT_SECRET:
    sys.exit("X_CLIENT_ID / X_CLIENT_SECRET が.envに見つかりません。先に設定してください。")


def update_env_value(key: str, value: str) -> None:
    """.env の指定キーだけを書き換える（x_likes_to_notion.pyと同じ方式）。"""

    with open(ENV_PATH, "r+", encoding="utf-8") as f:
        lines = f.readlines()

        new_lines = []
        found = False

        for line in lines:
            if line.startswith(f"{key}="):
                new_lines.append(f"{key}={value}\n")
                found = True
            else:
                new_lines.append(line)

        if not found:
            new_lines.append(f"{key}={value}\n")

        f.seek(0)
        f.writelines(new_lines)
        f.truncate()


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


code_verifier = _b64url(secrets.token_bytes(64))
code_challenge = _b64url(hashlib.sha256(code_verifier.encode("ascii")).digest())
state = secrets.token_urlsafe(16)

result: dict[str, str | None] = {}


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        params = parse_qs(parsed.query)

        result["code"] = params.get("code", [None])[0]
        result["state"] = params.get("state", [None])[0]
        result["error"] = params.get("error", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

        if result["error"]:
            body = f"<h1>認可に失敗しました</h1><p>{result['error']}</p>"
        else:
            body = "<h1>認可が完了しました</h1><p>このタブは閉じて構いません。ターミナルに戻ってください。</p>"

        self.wfile.write(body.encode("utf-8"))

    def log_message(self, format, *args):  # noqa: A002 — BaseHTTPRequestHandlerのシグネチャに合わせる
        pass  # アクセスログを標準エラーへ出さない


def main() -> None:
    authorize_url = "https://x.com/i/oauth2/authorize?" + urlencode(
        {
            "response_type": "code",
            "client_id": X_CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPES,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
    )

    HTTPServer.allow_reuse_address = True
    server = HTTPServer((CALLBACK_HOST, CALLBACK_PORT), _CallbackHandler)

    print("=" * 60)
    print("以下のURLをブラウザで開き、Xでログイン・アプリを承認してください:")
    print()
    print(authorize_url)
    print()
    print(f"({CALLBACK_HOST}:{CALLBACK_PORT} でコールバックを待機中... Ctrl+Cで中断)")
    print("=" * 60)

    # ブラウザが/favicon.ico等の関係ない/callback以外のリクエストを
    # 送ってくる場合があるため、実際にcode/errorを受け取るまでループする。
    while "code" not in result and "error" not in result:
        server.handle_request()

    if result.get("error"):
        sys.exit(f"認可がXによって拒否/失敗しました: {result['error']}")

    if result.get("state") != state:
        sys.exit("state不一致。CSRF対策により中断しました。最初からやり直してください。")

    if not result.get("code"):
        sys.exit("認可コードを受け取れませんでした。")

    print("認可コードを受信しました。トークンを取得します...")

    response = requests.post(
        "https://api.x.com/2/oauth2/token",
        auth=(X_CLIENT_ID, X_CLIENT_SECRET),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "code": result["code"],
            "redirect_uri": REDIRECT_URI,
            "code_verifier": code_verifier,
        },
        timeout=30,
    )

    if response.status_code != 200:
        sys.exit(f"トークン取得に失敗しました: {response.status_code} {response.text}")

    token_data = response.json()

    update_env_value("X_ACCESS_TOKEN", token_data["access_token"])

    if "refresh_token" in token_data:
        update_env_value("X_REFRESH_TOKEN", token_data["refresh_token"])
    else:
        print(
            "警告: レスポンスにrefresh_tokenが含まれていません"
            "（offline.accessスコープが付与されているか確認してください）"
        )

    print("成功: .envのX_ACCESS_TOKEN / X_REFRESH_TOKENを更新しました。")
    print(f"付与されたスコープ: {token_data.get('scope')}")


if __name__ == "__main__":
    main()
