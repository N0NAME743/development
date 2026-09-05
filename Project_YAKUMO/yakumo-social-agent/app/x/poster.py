"""Phase 5: X投稿。

安全装置（指示書15章・12章）:
- DRY_RUN=true が既定。この間は絶対に実際の投稿を行わない
- app.pipeline.queue.PostingQueue はAPPROVED状態の投稿だけをここへ渡す。
  投稿後はPOSTEDへ遷移し、get_next_approved()の対象から外れるため、
  状態遷移の仕組み自体が二重投稿を構造的に防いでいる

X_ACCESS_TOKENの自動更新（OAuth2 Refresh Token）は、既存のRaspberry Pi上の
x_likes_to_notion.pyと同じ方式・同じ認証情報（.envのX_CLIENT_ID等）を使う。
"""

import os

import requests

from app.common.models import PostCandidate

# app/x/poster.py から見て2つ上（yakumo-social-agent/）にある.envを直接更新する。
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")

X_API_BASE = "https://api.x.com/2"


def _update_env_value(key: str, value: str) -> None:
    """.env の指定キーだけを書き換える（x_likes_to_notion.pyと同じ方式）。"""

    if not os.path.exists(ENV_PATH):
        return

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


class XPoster:
    def __init__(self):
        self.dry_run = os.getenv("DRY_RUN", "true").lower() != "false"

        self._client_id = os.getenv("X_CLIENT_ID")
        self._client_secret = os.getenv("X_CLIENT_SECRET")
        self._access_token = os.getenv("X_ACCESS_TOKEN")
        self._refresh_token = os.getenv("X_REFRESH_TOKEN")

    def _refresh_access_token(self) -> None:
        response = requests.post(
            f"{X_API_BASE}/oauth2/token",
            auth=(self._client_id, self._client_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
            },
            timeout=30,
        )
        response.raise_for_status()

        token_data = response.json()

        self._access_token = token_data["access_token"]
        self._refresh_token = token_data.get("refresh_token", self._refresh_token)

        _update_env_value("X_ACCESS_TOKEN", self._access_token)
        _update_env_value("X_REFRESH_TOKEN", self._refresh_token)

    def _post_tweet(self, text: str) -> str:
        def _request() -> requests.Response:
            return requests.post(
                f"{X_API_BASE}/tweets",
                headers={
                    "Authorization": f"Bearer {self._access_token}",
                    "Content-Type": "application/json",
                },
                json={"text": text},
                timeout=30,
            )

        response = _request()

        if response.status_code == 401:
            self._refresh_access_token()
            response = _request()

        response.raise_for_status()

        return response.json()["data"]["id"]

    def post(self, candidate: PostCandidate) -> str:
        if self.dry_run:
            print(f"[DRY_RUN] Xへは投稿しません: {candidate.text[:40]}...")
            return "dry-run-no-post"

        for key, value in (
            ("X_CLIENT_ID", self._client_id),
            ("X_CLIENT_SECRET", self._client_secret),
            ("X_ACCESS_TOKEN", self._access_token),
            ("X_REFRESH_TOKEN", self._refresh_token),
        ):
            if not value:
                raise RuntimeError(
                    f"{key} not set. "
                    "USER ACTION REQUIRED: see docs/credentials.md section 3."
                )

        # 元投稿へのリンクは付与しない（X APIの従量課金がリンク付きだと
        # 大幅に高くなるため。docs/credentials.md 3章参照）。
        return self._post_tweet(candidate.text)
