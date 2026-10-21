"""Hidden tests for the initial job_board spec. They decide whether a program
is correct to begin with. Never shown to the writer or the editor.

Usage (with board.py importable, e.g. in the sandbox):
    python -m pytest private/test_board_initial.py
"""

import pytest
from board import BoardError, JobBoard

BAD_SALARIES = [0, -1, 2.5, "90000", None, True]
NAMES = ["ann", "bob"]


@pytest.fixture
def board():
    jb = JobBoard()
    jb.post_job("j1", "Data Engineer", 90000)
    jb.post_job("j2", "Designer", 70000)
    jb.add_applicant("ann")
    jb.add_applicant("bob")
    return jb


def state(jb):
    """Every job, its applicants and every fixture applicant's applications,
    to check that a failed call changed nothing."""
    jobs = {j: (jb.get_job(j), jb.get_applicants(j)) for j in jb.get_jobs()}
    return jobs, {n: jb.get_applications(n) for n in NAMES}


# --- jobs -------------------------------------------------------------------


def test_jobs_are_listed_in_posting_order():
    jb = JobBoard()
    for job_id in ["j3", "j1", "j2"]:
        jb.post_job(job_id, "Role", 50000)
    assert jb.get_jobs() == ["j3", "j1", "j2"]


def test_get_job_returns_title_and_salary(board):
    assert board.get_job("j1") == ("Data Engineer", 90000)
    assert board.get_job("j2") == ("Designer", 70000)


def test_an_empty_job_id_is_rejected(board):
    before = state(board)
    with pytest.raises(ValueError):
        board.post_job("", "Role", 50000)
    assert state(board) == before


def test_posting_a_job_id_twice_is_rejected(board):
    board.apply("ann", "j1")
    before = state(board)
    with pytest.raises(BoardError):
        board.post_job("j1", "Other", 1)
    assert state(board) == before
    assert board.get_job("j1") == ("Data Engineer", 90000)


@pytest.mark.parametrize("title", ["", None, 5])
def test_invalid_titles_are_rejected(board, title):
    before = state(board)
    with pytest.raises(ValueError):
        board.post_job("j3", title, 50000)
    assert state(board) == before


@pytest.mark.parametrize("salary", BAD_SALARIES)
def test_invalid_salaries_are_rejected(board, salary):
    before = state(board)
    with pytest.raises(ValueError):
        board.post_job("j3", "Role", salary)
    assert state(board) == before


def test_a_salary_of_one_is_allowed(board):
    board.post_job("j3", "Volunteer", 1)
    assert board.get_job("j3") == ("Volunteer", 1)


@pytest.mark.parametrize(
    "call",
    [
        lambda jb: jb.get_job("j9"),
        lambda jb: jb.get_applicants("j9"),
        lambda jb: jb.apply("ann", "j9"),
        lambda jb: jb.get_job(None),
        lambda jb: jb.get_applicants(1),
        lambda jb: jb.apply("ann", None),
    ],
)
def test_jobs_that_were_not_posted_raise_key_error(board, call):
    board.apply("ann", "j1")
    before = state(board)
    with pytest.raises(KeyError):
        call(board)
    assert state(board) == before


# --- applicants -------------------------------------------------------------


def test_a_new_applicant_has_no_applications(board):
    board.add_applicant("cat")
    assert board.get_applications("cat") == []


def test_an_empty_name_is_rejected(board):
    before = state(board)
    with pytest.raises(ValueError):
        board.add_applicant("")
    assert state(board) == before


def test_registering_a_name_twice_is_rejected(board):
    board.apply("ann", "j2")
    before = state(board)
    with pytest.raises(BoardError):
        board.add_applicant("ann")
    assert state(board) == before
    assert board.get_applications("ann") == ["j2"]


@pytest.mark.parametrize(
    "call",
    [
        lambda jb: jb.get_applications("cat"),
        lambda jb: jb.apply("cat", "j1"),
        lambda jb: jb.get_applications(None),
        lambda jb: jb.apply(3, "j1"),
    ],
)
def test_names_that_are_not_registered_raise_key_error(board, call):
    before = state(board)
    with pytest.raises(KeyError):
        call(board)
    assert state(board) == before


# --- applications -----------------------------------------------------------


def test_applicants_are_listed_in_application_order(board):
    board.add_applicant("cat")
    board.apply("cat", "j1")
    board.apply("ann", "j1")
    board.apply("bob", "j2")
    board.apply("bob", "j1")
    assert board.get_applicants("j1") == ["cat", "ann", "bob"]
    assert board.get_applicants("j2") == ["bob"]


def test_applications_are_listed_in_application_order(board):
    board.post_job("j3", "Analyst", 60000)
    board.apply("ann", "j3")
    board.apply("ann", "j1")
    board.apply("bob", "j2")
    board.apply("ann", "j2")
    assert board.get_applications("ann") == ["j3", "j1", "j2"]
    assert board.get_applications("bob") == ["j2"]


def test_applying_twice_to_the_same_job_is_rejected(board):
    board.apply("ann", "j1")
    before = state(board)
    with pytest.raises(BoardError):
        board.apply("ann", "j1")
    assert state(board) == before


def test_another_applicant_can_still_apply_after_a_rejection(board):
    board.apply("ann", "j1")
    with pytest.raises(BoardError):
        board.apply("ann", "j1")
    board.apply("bob", "j1")
    assert board.get_applicants("j1") == ["ann", "bob"]


# --- error order ------------------------------------------------------------


def test_a_posted_job_id_is_reported_before_a_bad_title(board):
    with pytest.raises(BoardError):
        board.post_job("j1", "", 0)
    assert board.get_job("j1") == ("Data Engineer", 90000)


def test_a_bad_title_is_reported_before_a_bad_salary(board):
    with pytest.raises(ValueError):
        board.post_job("j3", "", -1)
    assert board.get_jobs() == ["j1", "j2"]


def test_an_unregistered_name_is_reported_before_an_unknown_job(board):
    with pytest.raises(KeyError):
        board.apply("cat", "j9")


def test_a_repeated_application_is_only_reported_for_known_names_and_jobs(board):
    board.apply("ann", "j1")
    with pytest.raises(KeyError):
        board.apply("cat", "j1")
    with pytest.raises(KeyError):
        board.apply("ann", "j9")
    assert board.get_applicants("j1") == ["ann"]


def test_boards_do_not_share_data():
    first, second = JobBoard(), JobBoard()
    first.post_job("j1", "Role", 50000)
    first.add_applicant("ann")
    assert second.get_jobs() == []
    with pytest.raises(KeyError):
        second.get_applications("ann")
    second.post_job("j1", "Other", 1)
    assert second.get_job("j1") == ("Other", 1)
    assert first.get_job("j1") == ("Role", 50000)
