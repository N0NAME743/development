"""STEP1(投稿候補判定) → STEP2(YAKUMO変換) → STEP3(最終レビュー) のオーケストレーション。

指示書1章のフロー・8章の状態遷移に対応する。
ログに元投稿の要約全文を出さない（セキュリティ要件13章）。
"""

from app.ai.base import AIProvider
from app.common.models import AIJudgement, PostCandidate, ReviewResult
from app.common.state import PostState
from app.database.db import Database, content_hash
from app.notify.base import Notifier
from app.source.base import EntrySource


def _log(event: str, **fields: object) -> None:
    """source_text/APIキーを含めない、安全なログ出力（指示書13章）。"""

    detail = " ".join(f"{k}={v}" for k, v in fields.items())
    print(f"[pipeline] {event} {detail}")


class PipelineRunner:
    def __init__(
        self,
        source: EntrySource,
        ai: AIProvider,
        notifier: Notifier,
        db: Database,
        max_recent_posts: int = 5,
    ):
        self.source = source
        self.ai = ai
        self.notifier = notifier
        self.db = db
        self.max_recent_posts = max_recent_posts

    def run_once(self) -> list[PostCandidate]:
        """新規エントリーを取得し、承認待ちまで処理する。承認・却下・修正・投稿は別途扱う。"""

        entries = self.source.fetch_new_entries()
        results: list[PostCandidate] = []

        for entry in entries:
            # 重複防止（指示書7章）: 同じsource_entry_idは二度処理しない
            if self.db.already_processed(entry.entry_id):
                continue

            self.db.create_new(entry.entry_id, entry.text, entry.source_url)
            _log("NEW", source_entry_id=entry.entry_id)

            candidate = PostCandidate(
                source_entry_id=entry.entry_id,
                content_hash=content_hash(entry.text),
                source_url=entry.source_url,
                source={"summary": entry.text[:60]},
            )

            try:
                candidate = self._analyze(entry.entry_id, entry.text, candidate)
            except Exception as e:
                self.db.transition(
                    entry.entry_id, PostState.FAILED, error_message=str(e)
                )
                _log("FAILED", source_entry_id=entry.entry_id, stage="analyze")
                continue

            if candidate.ai_judgement and not candidate.ai_judgement.publishable:
                results.append(candidate)
                continue

            try:
                candidate = self._draft_and_review(entry.entry_id, entry.text, candidate)
            except Exception as e:
                self.db.transition(
                    entry.entry_id, PostState.FAILED, error_message=str(e)
                )
                _log("FAILED", source_entry_id=entry.entry_id, stage="draft")
                continue

            message_id = self.notifier.post_for_review(candidate)

            self.db.transition(
                entry.entry_id,
                PostState.WAITING_APPROVAL,
                discord_message_id=message_id,
            )
            _log(
                "WAITING_APPROVAL",
                source_entry_id=entry.entry_id,
                discord_message_id=message_id,
            )

            results.append(candidate)

        return results

    def _analyze(
        self, entry_id: str, text: str, candidate: PostCandidate
    ) -> PostCandidate:
        judgement: AIJudgement = self.ai.select_content(text)
        candidate.ai_judgement = judgement

        if judgement.publishable:
            self.db.transition(entry_id, PostState.ANALYZED)
            _log("ANALYZED", source_entry_id=entry_id, topic=judgement.topic)
        else:
            self.db.transition(entry_id, PostState.ANALYZED)
            self.db.transition(
                entry_id, PostState.REJECTED_BY_AI, error_message=judgement.reason
            )
            _log("REJECTED_BY_AI", source_entry_id=entry_id, reason=judgement.reason)

        return candidate

    def _draft_and_review(
        self, entry_id: str, text: str, candidate: PostCandidate
    ) -> PostCandidate:
        recent = self._recent_post_texts()

        drafts = self.ai.transform_to_yakumo(
            text, candidate.ai_judgement.topic, recent
        )
        candidate.draft_candidates = drafts

        # 通常運用ではDiscordで複数案から選ぶ想定だが、Phase2 Mockでは先頭案を採用する
        selected = drafts[0]

        review: ReviewResult = self.ai.final_review(text, selected)
        candidate.review = review
        candidate.text = review.revised_text

        self.db.transition(
            entry_id,
            PostState.DRAFTED,
            draft_text=candidate.text,
            draft_generated_at=_now(),
        )
        _log("DRAFTED", source_entry_id=entry_id, issues=len(review.issues))

        return candidate

    def _recent_post_texts(self) -> list[str]:
        # Phase2 Mockでは簡易実装。Phase3でDBから直近のPOSTED投稿を引くよう拡張する。
        return []


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()
