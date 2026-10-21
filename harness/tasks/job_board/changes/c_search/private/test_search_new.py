"""Hidden tests for the c_search change (searching jobs). Never shown to the
writer or the editor.

Usage (with board.py importable, e.g. in the sandbox):
    python -m pytest changes/c_search/private/test_search_new.py
"""

import pytest
from board import JobBoard

BAD_SALARY_BOUNDS = [-1, 2.5, "70000", True]


@pytest.fixture
def board():
    jb = JobBoard()
    jb.post_job("j1", "Data Engineer", 90000)
    jb.post_job("j2", "Designer", 70000)
    jb.post_job("j3", "Data Analyst", 70000)
    jb.post_job("j4", "Senior DATA Scientist", 120000)
    jb.post_job("j5", "Intern", 20000)
    for name in ["ann", "bob", "cat"]:
        jb.add_applicant(name)
    return jb


def test_without_filters_every_job_is_found_highest_salary_first(board):
    assert board.find_jobs() == ["j4", "j1", "j2", "j3", "j5"]


def test_keywords_match_anywhere_in_the_title_ignoring_case(board):
    assert board.find_jobs(keyword="data") == ["j4", "j1", "j3"]
    assert board.find_jobs(keyword="ENGINEER") == ["j1"]
    assert board.find_jobs(keyword="sign") == ["j2"]
    assert board.find_jobs(keyword="manager") == []


def test_salary_bounds_are_inclusive(board):
    assert board.find_jobs(min_salary=70000) == ["j4", "j1", "j2", "j3"]
    assert board.find_jobs(max_salary=70000) == ["j2", "j3", "j5"]
    assert board.find_jobs(min_salary=70000, max_salary=70000) == ["j2", "j3"]
    assert board.find_jobs(min_salary=70001, max_salary=89999) == []


def test_all_filters_combine(board):
    assert board.find_jobs(keyword="data", min_salary=0, max_salary=90000) == ["j1", "j3"]
    assert board.find_jobs(keyword="a", min_salary=100000) == ["j4"]


def test_a_zero_minimum_is_allowed(board):
    assert board.find_jobs(min_salary=0) == ["j4", "j1", "j2", "j3", "j5"]


def test_finding_changes_nothing(board):
    board.find_jobs(keyword="data", min_salary=1)
    board.get_jobs_by_popularity()
    assert board.get_jobs() == ["j1", "j2", "j3", "j4", "j5"]
    assert board.get_applicants("j1") == []


@pytest.mark.parametrize("keyword", ["", 7])
def test_find_jobs_rejects_bad_keywords(board, keyword):
    with pytest.raises(ValueError):
        board.find_jobs(keyword=keyword)


@pytest.mark.parametrize("bound", BAD_SALARY_BOUNDS)
def test_find_jobs_rejects_bad_salary_bounds(board, bound):
    with pytest.raises(ValueError):
        board.find_jobs(min_salary=bound)
    with pytest.raises(ValueError):
        board.find_jobs(max_salary=bound)


def test_find_jobs_rejects_a_minimum_above_the_maximum(board):
    with pytest.raises(ValueError):
        board.find_jobs(min_salary=70001, max_salary=70000)


def test_a_bad_keyword_is_reported_before_bad_bounds(board):
    with pytest.raises(ValueError):
        board.find_jobs(keyword="", min_salary=-1)


def test_popularity_orders_by_applicant_count_with_ties_in_posting_order(board):
    board.apply("ann", "j3")
    board.apply("bob", "j3")
    board.apply("cat", "j3")
    board.apply("ann", "j5")
    board.apply("bob", "j5")
    board.apply("cat", "j2")
    assert board.get_jobs_by_popularity() == ["j3", "j5", "j2", "j1", "j4"]


def test_popularity_without_applications_is_posting_order(board):
    assert board.get_jobs_by_popularity() == ["j1", "j2", "j3", "j4", "j5"]


def test_popularity_follows_new_applications(board):
    board.apply("ann", "j2")
    assert board.get_jobs_by_popularity() == ["j2", "j1", "j3", "j4", "j5"]
    board.apply("ann", "j4")
    board.apply("bob", "j4")
    assert board.get_jobs_by_popularity() == ["j4", "j2", "j1", "j3", "j5"]
