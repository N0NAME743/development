"""EntrySource抽象クラス。

情報源は当初Day Oneを想定していたが、Day Oneには新規エントリー取得用の公式APIが
存在しないため（docs/architecture.md 2章）、「記録_Research INBOX」Notionデータベースを
一次情報源とする方針に切り替えた（docs/architecture.md 2章 追記参照）。

この抽象化のおかげで、情報源を後から差し替えてもパイプライン本体（app/pipeline）は
変更不要。
"""

from abc import ABC, abstractmethod

from app.common.models import SourceEntry


class EntrySource(ABC):
    @abstractmethod
    def fetch_new_entries(self) -> list[SourceEntry]:
        """未処理の可能性があるエントリーを返す。重複排除はDB側（app/database/db.py）が担当する。"""

        raise NotImplementedError
