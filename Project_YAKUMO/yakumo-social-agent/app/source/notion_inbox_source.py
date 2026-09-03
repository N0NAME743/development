"""現在のデフォルト情報源: 「記録_Research INBOX」データベース（既存のX→Notionパイプラインが
書き込んでいるものと同じデータベース）を情報源とする。

Day Oneには新規エントリー取得用の公式APIが存在しなかったため（docs/architecture.md 2章）、
既に自分たちで運用しているこのデータベースを情報源にする方針へ切り替えた。

抽出方針:
- `AI査定` プロパティが指定値（既定「🟢 IDEA BOXへ」）の行だけを対象にする
  （既存パイプラインの一次選別をそのまま活用する）
- ページ本文の「📝 AI整理メモ」見出し直後の段落を、YAKUMOがリアクションする元ネタとして使う
  （原文全文ではなく、既にGeminiが要約した短い日本語テキストを使うことで、
  STEP2のプロンプトが安定しやすくなる）
- `URL` プロパティを、Xへの最終投稿に付けるリンクとして保持する
"""

import requests

from app.common.models import SourceEntry
from app.source.base import EntrySource

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2026-03-11"


class NotionInboxSource(EntrySource):
    def __init__(
        self,
        token: str,
        data_source_id: str,
        ai_hantei_value: str = "🟢 IDEA BOXへ",
    ):
        self.data_source_id = data_source_id
        self.ai_hantei_value = ai_hantei_value
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

    def fetch_new_entries(self) -> list[SourceEntry]:
        entries: list[SourceEntry] = []

        for page in self._query_inbox():
            entry = self._page_to_entry(page)

            if entry is not None:
                entries.append(entry)

        return entries

    def _query_inbox(self) -> list[dict]:
        url = f"{NOTION_API_BASE}/data_sources/{self.data_source_id}/query"

        payload = {
            "filter": {
                "property": "AI査定",
                "select": {"equals": self.ai_hantei_value},
            },
            "sorts": [{"timestamp": "created_time", "direction": "ascending"}],
            "page_size": 50,
        }

        response = requests.post(url, headers=self._headers, json=payload, timeout=30)
        response.raise_for_status()

        return response.json().get("results", [])

    def _page_to_entry(self, page: dict) -> SourceEntry | None:
        props = page.get("properties", {})

        title_rich_text = props.get("Name", {}).get("title", [])
        title = title_rich_text[0]["plain_text"] if title_rich_text else ""

        source_url = props.get("URL", {}).get("url")

        text = self._extract_ai_summary(page["id"]) or title

        if not text:
            return None

        return SourceEntry(
            entry_id=page["id"],
            text=text,
            created_at=page.get("created_time", ""),
            source_url=source_url,
        )

    def _extract_ai_summary(self, page_id: str) -> str:
        """ページ本文の「📝 AI整理メモ」見出し直後の段落を抜き出す。

        既存パイプライン（save_to_notion.sh / x_likes_to_notion.py）が作る
        ページ構成（heading_3 "📝 AI整理メモ" → paragraph）に依存している。
        ページ構成が変わった場合はここを直す。
        """

        url = f"{NOTION_API_BASE}/blocks/{page_id}/children"

        response = requests.get(
            url, headers=self._headers, params={"page_size": 20}, timeout=30
        )
        response.raise_for_status()

        blocks = response.json().get("results", [])
        capture_next = False

        for block in blocks:
            block_type = block.get("type")

            if block_type == "heading_3":
                heading_text = "".join(
                    rt.get("plain_text", "")
                    for rt in block["heading_3"].get("rich_text", [])
                )
                capture_next = "AI整理メモ" in heading_text
                continue

            if capture_next and block_type == "paragraph":
                return "".join(
                    rt.get("plain_text", "")
                    for rt in block["paragraph"].get("rich_text", [])
                )

        return ""
