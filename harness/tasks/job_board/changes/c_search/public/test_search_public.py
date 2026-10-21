"""Public checks for the c_search change (searching jobs). Shown to the
editor, never to the writer.

Usage (with board.py importable, e.g. in the sandbox):
    python -m pytest changes/c_search/public/test_search_public.py
"""

import pytest
from board import JobBoard


@pytest.fixture
def board():
    jb = JobBoard()
    jb.post_job("j1", "Data Engineer", 90000)
    jb.post_job("j2", "Designer", 70000)
    jb.post_job("j3", "Data Analyst", 70000)
    jb.add_applicant("ann")
    jb.add_applicant("bob")
    return jb


def test_jobs_can_be_found_by_keyword_and_salary(board):
    assert board.find_jobs(keyword="data") == ["j1", "j3"]
    assert board.find_jobs(min_salary=70000, max_salary=80000) == ["j2", "j3"]
    assert board.find_jobs() == ["j1", "j2", "j3"]


def test_popularity_counts_applicants(board):
    board.apply("ann", "j3")
    board.apply("bob", "j3")
    board.apply("ann", "j1")
    assert board.get_jobs_by_popularity() == ["j3", "j1", "j2"]
