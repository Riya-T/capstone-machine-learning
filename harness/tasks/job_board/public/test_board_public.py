"""Public checks for board.py.

Usage (with board.py importable, e.g. in the sandbox):
    python -m pytest public/test_board_public.py
"""

import pytest
from board import JobBoard


@pytest.fixture
def board():
    jb = JobBoard()
    jb.post_job("j1", "Data Engineer", 90000)
    jb.post_job("j2", "Designer", 70000)
    jb.add_applicant("ann")
    jb.add_applicant("bob")
    return jb


def test_a_posted_job_can_be_read_back(board):
    assert board.get_job("j1") == ("Data Engineer", 90000)
    assert board.get_jobs() == ["j1", "j2"]


def test_applying_is_seen_from_both_sides(board):
    board.apply("ann", "j1")
    board.apply("bob", "j1")
    board.apply("ann", "j2")
    assert board.get_applicants("j1") == ["ann", "bob"]
    assert board.get_applications("ann") == ["j1", "j2"]
    assert board.get_applications("bob") == ["j1"]


def test_a_job_without_applicants_has_an_empty_list(board):
    assert board.get_applicants("j2") == []
    assert board.get_applications("bob") == []


def test_salary_must_be_positive(board):
    with pytest.raises(ValueError):
        board.post_job("j3", "Intern", 0)
    assert board.get_jobs() == ["j1", "j2"]


def test_unknown_job_raises_key_error(board):
    with pytest.raises(KeyError):
        board.get_job("j9")
    with pytest.raises(KeyError):
        board.apply("ann", "j9")
