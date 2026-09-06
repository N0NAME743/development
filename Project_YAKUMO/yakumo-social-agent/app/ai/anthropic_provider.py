"""Phase 3で使用する実AI接続（Anthropic）。

USER ACTION REQUIRED: 使用するには ANTHROPIC_API_KEY が必要（.env）。
このセッションでは実APIキーが無いため、未検証（Mockでの疎通確認のみ完了）。
"""

import os

from app.ai.base import AIProvider, extract_json_response
from app.common.models import AIJudgement, ReviewResult
from app.common.text_budget import REACTION_TEXT_BUDGET
from app.config_loader import (
    load_character_bible,
    load_content_policy,
    load_prompt_template,
    load_x_prompt,
    render,
)


class AnthropicProvider(AIProvider):
    def __init__(self, model: str = "claude-sonnet-5"):
        api_key = os.getenv("AI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY (or AI_API_KEY) not set. "
                "USER ACTION REQUIRED: obtain an Anthropic API key and add it to .env "
                "before using AnthropicProvider. Use MockProvider until then."
            )

        try:
            import anthropic
        except ImportError as e:
            raise RuntimeError(
                "anthropic package not installed. Run: pip install anthropic"
            ) from e

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def _call(self, prompt: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    def select_content(self, entry_text: str) -> AIJudgement:
        template = load_prompt_template("select_content")

        prompt = render(
            template,
            CONTENT_POLICY=load_content_policy(),
            ENTRY_TEXT=entry_text,
        )

        data = extract_json_response(self._call(prompt))

        return AIJudgement(
            publishable=bool(data["publishable"]),
            reason=str(data.get("reason", "")),
            topic=str(data.get("topic", "")),
            sensitivity=str(data.get("sensitivity", "low")),
        )

    def transform_to_yakumo(
        self, entry_text: str, topic: str, recent_posts: list[str]
    ) -> list[str]:
        template = load_prompt_template("transform_to_yakumo")

        prompt = render(
            template,
            CHARACTER_BIBLE=load_character_bible(),
            X_PROMPT=load_x_prompt(),
            ENTRY_TEXT=entry_text,
            TOPIC=topic,
            RECENT_POSTS="\n".join(f"- {p}" for p in recent_posts) or "（履歴なし）",
            REACTION_TEXT_BUDGET=str(REACTION_TEXT_BUDGET),
        )

        data = extract_json_response(self._call(prompt))

        return list(data["drafts"])

    def final_review(self, entry_text: str, draft: str) -> ReviewResult:
        template = load_prompt_template("final_review")

        prompt = render(
            template,
            X_PROMPT=load_x_prompt(),
            ENTRY_TEXT=entry_text,
            DRAFT=draft,
            REACTION_TEXT_BUDGET=str(REACTION_TEXT_BUDGET),
        )

        data = extract_json_response(self._call(prompt))

        return ReviewResult(
            ok=bool(data.get("ok", True)),
            issues=list(data.get("issues", [])),
            revised_text=str(data.get("revised_text", draft)),
        )

    def revise(self, entry_text: str, previous_draft: str, instruction: str) -> str:
        template = load_prompt_template("revise")

        prompt = render(
            template,
            CHARACTER_BIBLE=load_character_bible(),
            X_PROMPT=load_x_prompt(),
            ENTRY_TEXT=entry_text,
            PREVIOUS_DRAFT=previous_draft,
            INSTRUCTION=instruction,
            REACTION_TEXT_BUDGET=str(REACTION_TEXT_BUDGET),
        )

        data = extract_json_response(self._call(prompt))

        return str(data.get("revised_text", previous_draft))
