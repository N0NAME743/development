import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.common.text_budget import REACTION_TEXT_BUDGET, X_POST_MAX_CHARS


def test_reaction_budget_equals_post_max_chars():
    # 元投稿へのリンクを付けない方針のため、本文はXの投稿上限をそのまま使える。
    assert REACTION_TEXT_BUDGET == X_POST_MAX_CHARS
