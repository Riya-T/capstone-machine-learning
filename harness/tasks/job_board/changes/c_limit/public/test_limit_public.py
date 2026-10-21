"""Public checks for the c_limit change (application limits). Shown to the
editor, never to the writer.

Usage (with board.py importable, e.g. in the sandbox):
    python -m pytest changes/c_limit/public/test_limit_public.py
"""

import pytest
from board import JobBoard, LimitReached


def test_an_applicant_cannot_exceed_the_board_limit():
    jb = JobBoard(max_applications=2)
    for job_id in ["j1", "j2", "j3"]:
        jb.post_job(job_id, "Role", 50000)
    jb.add_applicant("ann")
    jb.apply("ann", "j1")
    jb.apply("ann", "j2")
    with pytest.raises(LimitReached):
        jb.apply("ann", "j3")
    assert jb.get_applications("ann") == ["j1", "j2"]


def test_a_job_cannot_exceed_its_applicant_limit():
    jb = JobBoard()
    jb.post_job("j1", "Role", 50000, max_applicants=1)
    jb.add_applicant("ann")
    jb.add_applicant("bob")
    jb.apply("ann", "j1")
    with pytest.raises(LimitReached):
        jb.apply("bob", "j1")
    assert jb.get_applicants("j1") == ["ann"]
    assert jb.get_max_applicants("j1") == 1
