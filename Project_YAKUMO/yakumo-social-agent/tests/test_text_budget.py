import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.common.models import PostCandidate
from app.common.text_budget import (
    REACTION_TEXT_BUDGET,
    X_LINK_CHARS,
    X_POST_MAX_CHARS,
    fits_with_link,
)


def test_reaction_budget_leaves_room_for_link_and_newline():
    assert REACTION_TEXT_BUDGET == X_POST_MAX_CHARS - X_LINK_CHARS - 1


def test_fits_with_link_boundary():
    assert fits_with_link("a" * REACTION_TEXT_BUDGET) is True
    assert fits_with_link("a" * (REACTION_TEXT_BUDGET + 1)) is False


def test_full_post_text_appends_link_on_new_line():
    candidate = PostCandidate(
        source_entry_id="e1",
        content_hash="h",
        text="えっ、なにこれ面白そう。",
        source_url="https://x.com/example/status/123",
    )

    assert candidate.full_post_text() == (
        "えっ、なにこれ面白そう。\nhttps://x.com/example/status/123"
    )


def test_full_post_text_without_link():
    candidate = PostCandidate(source_entry_id="e1", content_hash="h", text="今日は眠い。")

    assert candidate.full_post_text() == "今日は眠い。"
