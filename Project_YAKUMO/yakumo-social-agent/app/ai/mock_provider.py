"""実API不要のダミー実装。Phase 2のパイプライン疎通確認専用。

出力は本物のYAKUMOらしさを再現するものではない
（それはPhase 3で実AI + config/prompts/*.mdを使って行う）。
[MOCK] で明示し、実際の投稿文と混同しないようにする。
"""

import re

from app.ai.base import AIProvider
from app.common.models import AIJudgement, ReviewResult
from app.common.text_budget import REACTION_TEXT_BUDGET

_SENSITIVE_PATTERNS = [
    re.compile(r"株式会社|有限会社|合同会社"),
    re.compile(r"\d+万円|\d+円"),
    re.compile(r"契約|予算|取引先"),
]

_BUSINESS_LOG_PATTERN = re.compile(r"スケジュール|出席者|一覧の共有|議事録|連絡事項")
_REFLECTIVE_WORDS = ["驚", "面白", "悔し", "感じ", "思っ", "楽し", "すごい", "すごく", "気になる"]


class MockProvider(AIProvider):
    def select_content(self, entry_text: str) -> AIJudgement:
        if any(p.search(entry_text) for p in _SENSITIVE_PATTERNS):
            return AIJudgement(
                publishable=False,
                reason="[MOCK] 会社名・金額・契約に関する記述が含まれるため",
                topic="不明",
                sensitivity="high",
            )

        has_reflection = any(w in entry_text for w in _REFLECTIVE_WORDS)

        if _BUSINESS_LOG_PATTERN.search(entry_text) and not has_reflection:
            return AIJudgement(
                publishable=False,
                reason="[MOCK] 感想の種が無く、単なる業務連絡に見えるため",
                topic="業務連絡",
                sensitivity="low",
            )

        topic = "AI・テクノロジー" if ("AI" in entry_text or "コード" in entry_text) else (
            "ゲーム" if "ゲーム" in entry_text else "日常"
        )

        return AIJudgement(
            publishable=True,
            reason="[MOCK] YAKUMOが反応できそうな内容が含まれるため",
            topic=topic,
            sensitivity="low",
        )

    def transform_to_yakumo(
        self, entry_text: str, topic: str, recent_posts: list[str]
    ) -> list[str]:
        gist = entry_text.strip().splitlines()[0][:40]

        return [
            f"[MOCK-A] {gist}……ってことがあった。ちょっと面白かったかも。",
            f"[MOCK-B] えっ、{gist} ってなに。……ちょっと気になる。ヤクモも触ってみたい！",
            f"[MOCK-C] {gist}……ふふっ、これは電脳世界的にも見逃せないやつ ω",
        ]

    def final_review(self, entry_text: str, draft: str) -> ReviewResult:
        issues = []
        revised = draft

        if len(draft) > REACTION_TEXT_BUDGET:
            issues.append(f"[MOCK] {REACTION_TEXT_BUDGET}文字を超えています")
            revised = draft[:REACTION_TEXT_BUDGET]

        return ReviewResult(ok=len(issues) == 0, issues=issues, revised_text=revised)
