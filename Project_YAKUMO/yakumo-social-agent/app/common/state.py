"""投稿の状態遷移。実装指示書 8章 + セキュリティ要件13章（FAILEDの追加）に対応。"""

from enum import Enum


class PostState(str, Enum):
    NEW = "NEW"
    ANALYZED = "ANALYZED"
    REJECTED_BY_AI = "REJECTED_BY_AI"
    DRAFTED = "DRAFTED"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    APPROVED = "APPROVED"
    POSTED = "POSTED"
    REJECTED_BY_USER = "REJECTED_BY_USER"
    REVISION_REQUESTED = "REVISION_REQUESTED"
    FAILED = "FAILED"


# 許可された遷移のみを列挙する。ここに無い遷移は ALLOWED_TRANSITIONS でエラーになる。
ALLOWED_TRANSITIONS = {
    PostState.NEW: {PostState.ANALYZED, PostState.FAILED},
    PostState.ANALYZED: {PostState.REJECTED_BY_AI, PostState.DRAFTED, PostState.FAILED},
    PostState.DRAFTED: {PostState.WAITING_APPROVAL, PostState.FAILED},
    PostState.WAITING_APPROVAL: {
        PostState.APPROVED,
        PostState.REJECTED_BY_USER,
        PostState.REVISION_REQUESTED,
    },
    PostState.REVISION_REQUESTED: {PostState.DRAFTED, PostState.FAILED},
    PostState.APPROVED: {PostState.POSTED, PostState.FAILED},
    # 終端状態
    PostState.POSTED: set(),
    PostState.REJECTED_BY_AI: set(),
    PostState.REJECTED_BY_USER: set(),
    PostState.FAILED: set(),
}


class InvalidTransition(Exception):
    pass


def validate_transition(current: PostState, next_state: PostState) -> None:
    allowed = ALLOWED_TRANSITIONS.get(current, set())

    if next_state not in allowed:
        raise InvalidTransition(
            f"{current.value} -> {next_state.value} is not an allowed transition"
        )
