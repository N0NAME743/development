"""[現在未使用の代替実装] Day OneアプリからユーザーがJSONエクスポートしたファイルを
置くフォルダを監視し、entries[]を読み取る（docs/architecture.md 2章 案A）。

現在のデフォルトはNotionInboxSource（notion_inbox_source.py）に切り替え済み。
将来Day Oneを情報源に戻したくなった場合のために残してある。

Day One JSON export format（公式ドキュメントには存在しないため、Day One公式ブログ・
フォーラム記載のフィールド名を基に実装。将来Day One側の形式が変わった場合は
このファイルだけを直せばよい）:

{
  "metadata": {"version": "1.0"},
  "entries": [
    {
      "uuid": "...",
      "creationDate": "2026-09-04T03:14:00Z",
      "text": "本文（Markdown）",
      ...
    }
  ]
}
"""

import glob
import json
import os

from app.common.models import SourceEntry
from app.source.base import EntrySource


class JSONExportSource(EntrySource):
    def __init__(self, export_dir: str):
        self.export_dir = export_dir

    def fetch_new_entries(self) -> list[SourceEntry]:
        """export_dir以下の全*.jsonを読み、entries[]をまとめて返す。

        「新規」の判定はここでは行わない（同じファイルを毎回読んでも、
        DB側のsource_entry_id重複チェックで安全に弾かれる設計）。
        """

        entries: list[SourceEntry] = []

        for path in sorted(glob.glob(os.path.join(self.export_dir, "*.json"))):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for raw in data.get("entries", []):
                text = (raw.get("text") or "").strip()

                if not text:
                    continue

                entries.append(
                    SourceEntry(
                        entry_id=raw["uuid"],
                        text=text,
                        created_at=raw.get("creationDate", ""),
                    )
                )

        return entries
