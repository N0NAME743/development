"""AIProvider抽象化。指示書14章のとおり、特定のAI APIへ強く依存しない。"""

import json
from abc import ABC, abstractmethod

from app.common.models import AIJudgement, ReviewResult


def extract_json_response(raw: str) -> dict:
    """AIがMarkdownコードブロック付きでJSONを返した場合に備えた共通パーサー。"""

    text = raw.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

        if text.lower().startswith("json"):
            text = text[4:].strip()

    return json.loads(text)


class AIProvider(ABC):
    @abstractmethod
    def select_content(self, entry_text: str) -> AIJudgement:
        raise NotImplementedError

    @abstractmethod
    def transform_to_yakumo(
        self, entry_text: str, topic: str, recent_posts: list[str]
    ) -> list[str]:
        """3案の投稿文候補を返す。"""

        raise NotImplementedError

    @abstractmethod
    def final_review(self, entry_text: str, draft: str) -> ReviewResult:
        raise NotImplementedError

    @abstractmethod
    def revise(self, entry_text: str, previous_draft: str, instruction: str) -> str:
        """Discordでの「修正」指示を踏まえて、投稿案を1つ作り直す。"""

        raise NotImplementedError
