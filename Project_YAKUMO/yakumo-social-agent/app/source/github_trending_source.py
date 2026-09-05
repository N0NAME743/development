"""情報源: GitHubで話題のリポジトリ。

GitHubには公式のTrendingページ（github.com/trending）向けAPIが存在しない
（HTMLスクレイピングが必要になり壊れやすい）。そのため、公式のSearch API
（GET /search/repositories）で「直近1週間に作られ、スター数が多い」
リポジトリを取得し、Trendingの近似として扱う。

認証無しでも動作する（GitHub APIの未認証レート制限は60回/時）。
より高い制限が必要な場合のみ GITHUB_TOKEN を設定する。
"""

import os
from datetime import datetime, timedelta, timezone

import requests

from app.common.models import SourceEntry
from app.source.base import EntrySource

GITHUB_API_BASE = "https://api.github.com"

ENTRY_ID_PREFIX = "github-trending"


class GitHubTrendingSource(EntrySource):
    def __init__(self, lookback_days: int = 7, per_page: int = 10, min_stars: int = 50):
        self.lookback_days = lookback_days
        self.per_page = per_page
        self.min_stars = min_stars

        token = os.getenv("GITHUB_TOKEN")

        self._headers = {"Accept": "application/vnd.github+json"}

        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    def fetch_new_entries(self) -> list[SourceEntry]:
        since = (
            datetime.now(timezone.utc) - timedelta(days=self.lookback_days)
        ).strftime("%Y-%m-%d")

        response = requests.get(
            f"{GITHUB_API_BASE}/search/repositories",
            headers=self._headers,
            params={
                "q": f"created:>{since} stars:>={self.min_stars}",
                "sort": "stars",
                "order": "desc",
                "per_page": self.per_page,
            },
            timeout=30,
        )
        response.raise_for_status()

        items = response.json().get("items", [])

        return [self._repo_to_entry(repo) for repo in items]

    def _repo_to_entry(self, repo: dict) -> SourceEntry:
        full_name = repo["full_name"]
        description = (repo.get("description") or "").strip()
        stars = repo.get("stargazers_count", 0)
        language = repo.get("language")

        parts = [f"GitHubで話題のリポジトリ「{full_name}」（⭐{stars}）"]

        if language:
            parts.append(f"主な言語: {language}")

        if description:
            parts.append(description)

        text = "。".join(parts)

        return SourceEntry(
            entry_id=f"{ENTRY_ID_PREFIX}:{repo['id']}",
            text=text,
            created_at=repo.get("created_at", ""),
            source_url=repo.get("html_url"),
        )
