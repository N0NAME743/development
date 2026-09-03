import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from app.common.state import PostState, InvalidTransition, validate_transition


def test_new_to_analyzed_allowed():
    validate_transition(PostState.NEW, PostState.ANALYZED)


def test_analyzed_to_rejected_by_ai_allowed():
    validate_transition(PostState.ANALYZED, PostState.REJECTED_BY_AI)


def test_waiting_approval_to_revision_requested_allowed():
    validate_transition(PostState.WAITING_APPROVAL, PostState.REVISION_REQUESTED)


def test_revision_requested_loops_back_to_drafted():
    validate_transition(PostState.REVISION_REQUESTED, PostState.DRAFTED)


def test_posted_is_terminal():
    with pytest.raises(InvalidTransition):
        validate_transition(PostState.POSTED, PostState.DRAFTED)


def test_cannot_skip_from_new_to_posted():
    with pytest.raises(InvalidTransition):
        validate_transition(PostState.NEW, PostState.POSTED)


def test_rejected_by_user_is_terminal():
    with pytest.raises(InvalidTransition):
        validate_transition(PostState.REJECTED_BY_USER, PostState.WAITING_APPROVAL)
