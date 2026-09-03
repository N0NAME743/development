"""Phase 2用: 実DB不要でパイプライン全体を試せるサンプルデータ源。

「記録_Research INBOX」に貯まった、Xでいいねした投稿の要約を想定したサンプル。
YAKUMOはこれらを日記としてではなく、電脳観測（X Prompt §14 ジャンルA）として
リアクションする。
"""

from app.common.models import SourceEntry
from app.source.base import EntrySource

SAMPLE_ENTRIES = [
    SourceEntry(
        entry_id="mock-inbox-0001",
        text=(
            "AIエージェントにコードレビューをさせたところ、人間が見逃していた重複ロジックを"
            "一発で指摘した、という投稿。ツールを実際に触ってみた感想として好評だった。"
        ),
        created_at="2026-09-04T09:15:00Z",
        source_url="https://x.com/example_user/status/1000000000000000001",
    ),
    SourceEntry(
        entry_id="mock-inbox-0002",
        text="本日の会議スケジュールと出席者一覧の共有。",
        created_at="2026-09-04T21:00:00Z",
        source_url="https://x.com/example_corp/status/1000000000000000002",
    ),
    SourceEntry(
        entry_id="mock-inbox-0003",
        text=(
            "新しいゲームのボス攻略が5連敗中というプレイヤーの投稿。負けるたびに敵の行動パターンが"
            "少しずつ読めてきているとのこと。"
        ),
        created_at="2026-09-05T02:40:00Z",
        source_url="https://x.com/example_gamer/status/1000000000000000003",
    ),
    SourceEntry(
        entry_id="mock-inbox-0004",
        text="株式会社アルファ商事との来月の契約金額について、担当者間で調整中という内部連絡の内容。",
        created_at="2026-09-05T14:00:00Z",
        source_url="https://x.com/example_biz/status/1000000000000000004",
    ),
]


class MockEntrySource(EntrySource):
    def fetch_new_entries(self) -> list[SourceEntry]:
        return list(SAMPLE_ENTRIES)
