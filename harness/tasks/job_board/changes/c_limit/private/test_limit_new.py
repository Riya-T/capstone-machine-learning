"""Hidden tests for the c_limit change (application limits). Never shown to
the writer or the editor.

Usage (with board.py importable, e.g. in the sandbox):
    python -m pytest changes/c_limit/private/test_limit_new.py
"""

import pytest
from board import BoardError, JobBoard, LimitReached

BAD_LIMITS = [0, -1, 2.5, "2", True]
NAMES = ["ann", "bob", "cat"]


@pytest.fixture
def board():
    jb = JobBoard(max_applications=2)
    jb.post_job("j1", "Data Engineer", 90000, max_applicants=2)
    jb.post_job("j2", "Designer", 70000)
    jb.post_job("j3", "Analyst", 60000)
    for name in NAMES:
        jb.add_applicant(name)
    return jb


def state(jb):
    jobs = {j: (jb.get_job(j), jb.get_applicants(j)) for j in jb.get_jobs()}
    return jobs, {n: jb.get_applications(n) for n in NAMES}


def test_limits_can_be_read_back(board):
    assert board.get_max_applicants("j1") == 2
    assert board.get_max_applicants("j2") is None


def test_without_limits_any_number_of_applications_is_fine():
    jb = JobBoard()
    for job_id in ["j1", "j2", "j3", "j4"]:
        jb.post_job(job_id, "Role", 50000)
    jb.add_applicant("ann")
    for job_id in ["j1", "j2", "j3", "j4"]:
        jb.apply("ann", job_id)
    assert jb.get_applications("ann") == ["j1", "j2", "j3", "j4"]


def test_the_board_limit_counts_each_applicant_separately(board):
    board.apply("ann", "j1")
    board.apply("ann", "j2")
    board.apply("bob", "j2")
    board.apply("bob", "j3")
    before = state(board)
    with pytest.raises(LimitReached):
        board.apply("ann", "j3")
    with pytest.raises(LimitReached):
        board.apply("bob", "j1")
    assert state(board) == before
    board.apply("cat", "j3")
    assert board.get_applicants("j3") == ["bob", "cat"]


def test_the_job_limit_counts_its_applicants(board):
    board.apply("ann", "j1")
    board.apply("bob", "j1")
    before = state(board)
    with pytest.raises(LimitReached):
        board.apply("cat", "j1")
    assert state(board) == before
    board.apply("cat", "j2")
    assert board.get_applications("cat") == ["j2"]


def test_a_limit_of_one_allows_exactly_one():
    jb = JobBoard(max_applications=1)
    jb.post_job("j1", "Role", 50000, max_applicants=1)
    jb.post_job("j2", "Role", 50000, max_applicants=1)
    jb.add_applicant("ann")
    jb.add_applicant("bob")
    jb.apply("ann", "j1")
    with pytest.raises(LimitReached):
        jb.apply("bob", "j1")
    with pytest.raises(LimitReached):
        jb.apply("ann", "j2")
    jb.apply("bob", "j2")
    assert jb.get_applicants("j2") == ["bob"]


@pytest.mark.parametrize("limit", BAD_LIMITS)
def test_invalid_board_limits_are_rejected(limit):
    with pytest.raises(ValueError):
        JobBoard(max_applications=limit)


@pytest.mark.parametrize("limit", BAD_LIMITS)
def test_invalid_job_limits_are_rejected(board, limit):
    before = state(board)
    with pytest.raises(ValueError):
        board.post_job("j4", "Role", 50000, max_applicants=limit)
    assert state(board) == before


@pytest.mark.parametrize("job_id", ["j9", None, 1])
def test_get_max_applicants_of_an_unknown_job_raises_key_error(board, job_id):
    with pytest.raises(KeyError):
        board.get_max_applicants(job_id)


def test_limit_reached_is_a_board_error():
    assert issubclass(LimitReached, BoardError)


def test_a_bad_job_limit_is_reported_after_other_post_job_errors(board):
    with pytest.raises(BoardError):
        board.post_job("j1", "Role", 50000, max_applicants=0)
    with pytest.raises(ValueError):
        board.post_job("j4", "", 50000, max_applicants=0)
    with pytest.raises(ValueError):
        board.post_job("j4", "Role", -5, max_applicants=0)
    assert board.get_jobs() == ["j1", "j2", "j3"]


def test_limit_reached_is_reported_after_every_other_apply_error(board):
    board.apply("ann", "j1")
    board.apply("ann", "j2")
    board.apply("bob", "j1")
    with pytest.raises(KeyError):
        board.apply("dan", "j1")
    with pytest.raises(KeyError):
        board.apply("ann", "j9")
    with pytest.raises(BoardError) as info:
        board.apply("ann", "j1")  # repeated, and both limits are reached
    assert not isinstance(info.value, LimitReached)
    assert board.get_applicants("j1") == ["ann", "bob"]
