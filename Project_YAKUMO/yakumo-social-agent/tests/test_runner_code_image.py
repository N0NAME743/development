import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.common.models import AIJudgement, ReviewResult, SourceEntry
from app.database.db import Database
from app.notify.base import Notifier
from app.pipeline.runner import PipelineRunner
from app.source.base import EntrySource


class _OneEntrySource(EntrySource):
    def fetch_new_entries(self):
        return [
            SourceEntry(entry_id="e1", text="なんか見つけた", created_at="", source_url=None)
        ]


class _CodeDraftAI:
    """複数行コードブロックを含む投稿案を返すテスト用AIProvider。"""

    def select_content(self, entry_text):
        return AIJudgement(publishable=True, reason="テスト", topic="コード", sensitivity="low")

    def transform_to_yakumo(self, entry_text, topic, recent_posts):
        return ["```python\ndef hi():\n    print('hi')\n```\n見つけちゃった"]

    def final_review(self, entry_text, draft):
        return ReviewResult(ok=True, issues=[], revised_text=draft)

    def revise(self, entry_text, previous_draft, instruction):
        raise NotImplementedError


class _RecordingNotifier(Notifier):
    def __init__(self):
        self.candidates = []

    def post_for_review(self, candidate):
        self.candidates.append(candidate)
        return "msg-1"

    def notify_posted(self, text):
        pass


def test_code_block_in_draft_is_extracted_into_media_before_notifying():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "t.db")
        db = Database(db_path)
        notifier = _RecordingNotifier()

        runner = PipelineRunner(
            source=_OneEntrySource(), ai=_CodeDraftAI(), notifier=notifier, db=db
        )
        runner.run_once()

        assert len(notifier.candidates) == 1
        candidate = notifier.candidates[0]

        assert "```" not in candidate.text
        assert "見つけちゃった" in candidate.text
        assert candidate.media == [
            {"type": "code_image", "language": "python", "code": "def hi():\n    print('hi')"}
        ]

        row = db.get("e1")
        assert row["media_json"] is not None
