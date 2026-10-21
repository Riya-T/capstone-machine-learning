"""Hidden tests for the c_close change (closing jobs). Never shown to the
writer or the editor.

Usage (with board.py importable, e.g. in the sandbox):
    python -m pytest changes/c_close/private/test_close_new.py
"""

import pytest
from board import BoardError, JobBoard, JobClosed

NAMES = ["ann", "bob"]


@pytest.fixture
def board():
    jb = JobBoard()
    jb.post_job("j1", "Data Engineer", 90000)
    jb.post_job("j2", "Designer", 70000)
    jb.post_job("j3", "Analyst", 60000)
    jb.add_applicant("ann")
    jb.add_applicant("bob")
    jb.apply("ann", "j1")
    return jb


def state(jb):
    jobs = {j: (jb.get_job(j), jb.get_applicants(j), jb.is_open(j)) for j in jb.get_jobs()}
    return jobs, {n: jb.get_applications(n) for n in NAMES}


def test_jobs_start_open(board):
    assert all(board.is_open(j) for j in ["j1", "j2", "j3"])
    assert board.get_open_jobs() == ["j1", "j2", "j3"]


def test_closing_and_reopening_flip_the_flag(board):
    board.close_job("j2")
    assert not board.is_open("j2")
    assert board.is_open("j1")
    board.reopen_job("j2")
    assert board.is_open("j2")


def test_closing_or_reopening_twice_is_harmless(board):
    board.close_job("j1")
    board.close_job("j1")
    assert not board.is_open("j1")
    board.reopen_job("j1")
    board.reopen_job("j1")
    assert board.is_open("j1")
    assert board.get_applicants("j1") == ["ann"]


def test_applying_to_a_closed_job_changes_nothing(board):
    board.close_job("j2")
    before = state(board)
    with pytest.raises(JobClosed):
        board.apply("bob", "j2")
    assert state(board) == before


def test_a_closed_job_keeps_its_applicants_and_details(board):
    board.close_job("j1")
    assert board.get_applicants("j1") == ["ann"]
    assert board.get_applications("ann") == ["j1"]
    assert board.get_job("j1") == ("Data Engineer", 90000)
    assert board.get_jobs() == ["j1", "j2", "j3"]


def test_open_jobs_keep_posting_order(board):
    board.close_job("j2")
    assert board.get_open_jobs() == ["j1", "j3"]
    board.close_job("j1")
    assert board.get_open_jobs() == ["j3"]
    board.reopen_job("j1")
    assert board.get_open_jobs() == ["j1", "j3"]


def test_other_jobs_still_take_applications(board):
    board.close_job("j1")
    board.apply("bob", "j2")
    assert board.get_applicants("j2") == ["bob"]


def test_a_reopened_job_takes_applications_again(board):
    board.close_job("j3")
    board.reopen_job("j3")
    board.apply("ann", "j3")
    assert board.get_applications("ann") == ["j1", "j3"]


@pytest.mark.parametrize("job_id", ["j9", None, 1])
def test_closing_an_unknown_job_raises_key_error(board, job_id):
    before = state(board)
    with pytest.raises(KeyError):
        board.close_job(job_id)
    with pytest.raises(KeyError):
        board.reopen_job(job_id)
    with pytest.raises(KeyError):
        board.is_open(job_id)
    assert state(board) == before


def test_job_closed_is_a_board_error():
    assert issubclass(JobClosed, BoardError)


def test_key_errors_are_reported_before_job_closed(board):
    board.close_job("j1")
    with pytest.raises(KeyError):
        board.apply("cat", "j1")
    with pytest.raises(KeyError):
        board.apply("ann", "j9")


def test_job_closed_is_reported_before_a_repeated_application(board):
    board.close_job("j1")
    with pytest.raises(JobClosed):
        board.apply("ann", "j1")
    board.reopen_job("j1")
    with pytest.raises(BoardError):
        board.apply("ann", "j1")
    assert board.get_applicants("j1") == ["ann"]
