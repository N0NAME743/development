"""Notifier抽象化。Discordを「投稿前レビュー画面」として使う（指示書5章）。"""

from abc import ABC, abstractmethod

from app.common.models import PostCandidate


class Notifier(ABC):
    @abstractmethod
    def post_for_review(self, candidate: PostCandidate) -> str:
        """レビュー依頼を送信し、message_idを返す。"""

        raise NotImplementedError

    @abstractmethod
    def notify_posted(self, text: str) -> None:
        """実際にXへ投稿し終えたことを知らせる（承認→process_queue.py経由の自動投稿用）。"""

        raise NotImplementedError
