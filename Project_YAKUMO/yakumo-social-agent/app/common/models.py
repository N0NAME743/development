"""パイプライン全体で使うデータモデル。指示書17章の拡張余地（media/character）を最初から持たせる。"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SourceEntry:
    """情報源（現在は記録_Research INBOX）から取得した1件。

    source_url: 元投稿のURL。ツイート本文には含めない
    （X APIのリンク付き投稿の従量課金を避けるため）が、
    Discordでの承認レビュー時に参照用として表示する。
    """

    entry_id: str
    text: str
    created_at: str
    source_url: Optional[str] = None


@dataclass
class AIJudgement:
    publishable: bool
    reason: str
    topic: str
    sensitivity: str  # "low" | "medium" | "high"


@dataclass
class ReviewResult:
    ok: bool
    issues: list[str]
    revised_text: str


@dataclass
class PostCandidate:
    """指示書17章のデータモデルを拡張したもの。将来のmedia/複数プラットフォーム対応を見込む。"""

    source_entry_id: str
    content_hash: str
    text: str = ""
    source_url: Optional[str] = None
    media: list[dict] = field(default_factory=list)
    source: dict = field(default_factory=dict)
    character: str = "YAKUMO"
    ai_judgement: Optional[AIJudgement] = None
    draft_candidates: list[str] = field(default_factory=list)
    review: Optional[ReviewResult] = None
