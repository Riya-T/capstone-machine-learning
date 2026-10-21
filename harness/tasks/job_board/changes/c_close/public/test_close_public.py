"""Public checks for the c_close change (closing jobs). Shown to the editor,
never to the writer.

Usage (with board.py importable, e.g. in the sandbox):
    python -m pytest changes/c_close/public/test_close_public.py
"""

import pytest
from board import JobBoard, JobClosed


@pytest.fixture
def board():
    jb = JobBoard()
    jb.post_job("j1", "Data Engineer", 90000)
    jb.post_job("j2", "Designer", 70000)
    jb.add_applicant("ann")
    return jb


def test_a_closed_job_takes_no_applications(board):
    board.close_job("j1")
    assert not board.is_open("j1")
    with pytest.raises(JobClosed):
        board.apply("ann", "j1")
    assert board.get_applicants("j1") == []
    board.reopen_job("j1")
    board.apply("ann", "j1")
    assert board.get_applicants("j1") == ["ann"]


def test_open_jobs_leave_out_the_closed_ones(board):
    board.close_job("j1")
    assert board.get_open_jobs() == ["j2"]
    assert board.get_jobs() == ["j1", "j2"]
