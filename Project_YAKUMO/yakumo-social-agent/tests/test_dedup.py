import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.mock_provider import MockProvider
from app.database.db import Database
from app.source.mock_source import MockEntrySource
from app.notify.base import Notifier
from app.pipeline.runner import PipelineRunner


class _SilentNotifier(Notifier):
    """テスト用: コンソール出力せずmessage_idだけ返す。"""

    def __init__(self):
        self.calls = 0

    def post_for_review(self, candidate):
        self.calls += 1
        return f"test-msg-{self.calls}"

    def notify_posted(self, text):
        pass


def _make_runner(db_path: str) -> tuple[PipelineRunner, _SilentNotifier]:
    notifier = _SilentNotifier()
    runner = PipelineRunner(
        source=MockEntrySource(),
        ai=MockProvider(),
        notifier=notifier,
        db=Database(db_path),
    )
    return runner, notifier


def test_same_dayone_entry_not_processed_twice():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        runner, notifier = _make_runner(db_path)

        first = runner.run_once()
        assert len(first) == 4  # サンプル4件すべてSTEP1を通過（却下含む）

        second = runner.run_once()
        assert len(second) == 0  # 重複防止により再処理されない

        # 却下されなかった2件だけDiscordへ通知される
        assert notifier.calls == 2


def test_rejected_by_ai_entries_are_recorded_but_not_notified():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        runner, notifier = _make_runner(db_path)

        results = runner.run_once()
        rejected = [r for r in results if not r.ai_judgement.publishable]

        assert len(rejected) == 2
        assert notifier.calls == 2  # 却下された2件は通知に含まれない
