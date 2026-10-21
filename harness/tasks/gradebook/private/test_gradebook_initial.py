"""Hidden tests for the initial gradebook spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with gradebook.py importable, e.g. in the sandbox):
    python -m pytest private/test_gradebook_initial.py
"""

import pytest
from gradebook import Gradebook, GradebookError

BAD_POINTS = [-1, 11, 2.5, "5", None]
BAD_MAX_POINTS = [0, -5, 2.5, "10", None]


@pytest.fixture
def book():
    gb = Gradebook()
    gb.add_student("ana")
    gb.add_student("ben")
    gb.add_assignment("quiz", 10)
    gb.add_assignment("essay", 20)
    gb.add_assignment("final", 100)
    return gb


def state(gb):
    """Every total and every score, to check that a failed call changed nothing."""
    snap = {}
    for name in gb.get_students():
        scores = {}
        for title in gb.get_assignments():
            try:
                scores[title] = gb.get_score(name, title)
            except GradebookError:
                scores[title] = None
        snap[name] = (gb.get_total(name), scores)
    return snap


# --- students and assignments -----------------------------------------------


def test_a_new_student_has_no_scores(book):
    assert book.get_total("ana") == 0
    with pytest.raises(GradebookError):
        book.get_score("ana", "quiz")


def test_students_are_listed_in_the_order_added():
    gb = Gradebook()
    for name in ["cho", "ana", "ben"]:
        gb.add_student(name)
    assert gb.get_students() == ["cho", "ana", "ben"]


def test_assignments_are_listed_in_the_order_added(book):
    assert book.get_assignments() == ["quiz", "essay", "final"]


@pytest.mark.parametrize("bad_name", [""])
def test_invalid_student_names_are_rejected(bad_name):
    gb = Gradebook()
    with pytest.raises(ValueError):
        gb.add_student(bad_name)
    assert gb.get_students() == []


def test_adding_a_student_twice_is_rejected(book):
    book.record_score("ana", "quiz", 6)
    with pytest.raises(GradebookError):
        book.add_student("ana")
    assert book.get_students() == ["ana", "ben"]
    assert book.get_score("ana", "quiz") == 6


@pytest.mark.parametrize("bad_title", [""])
def test_invalid_assignment_titles_are_rejected(book, bad_title):
    with pytest.raises(ValueError):
        book.add_assignment(bad_title, 10)
    assert book.get_assignments() == ["quiz", "essay", "final"]


@pytest.mark.parametrize("max_points", BAD_MAX_POINTS)
def test_invalid_max_points_are_rejected(book, max_points):
    with pytest.raises(ValueError):
        book.add_assignment("lab", max_points)
    assert book.get_assignments() == ["quiz", "essay", "final"]
    with pytest.raises(KeyError):
        book.record_score("ana", "lab", 0)


def test_adding_an_assignment_twice_is_rejected(book):
    with pytest.raises(GradebookError):
        book.add_assignment("quiz", 50)
    assert book.get_assignments() == ["quiz", "essay", "final"]
    # The original max_points still applies.
    with pytest.raises(ValueError):
        book.record_score("ana", "quiz", 11)


def test_bad_max_points_is_reported_before_a_duplicate_title(book):
    with pytest.raises(ValueError):
        book.add_assignment("quiz", 0)


@pytest.mark.parametrize(
    "call",
    [
        lambda gb: gb.record_score("dan", "quiz", 5),
        lambda gb: gb.record_score("ana", "lab", 5),
        lambda gb: gb.get_score("dan", "quiz"),
        lambda gb: gb.get_score("ana", "lab"),
        lambda gb: gb.get_total("dan"),
        lambda gb: gb.get_total(None),
        lambda gb: gb.get_total(1),
        lambda gb: gb.record_score("ana", None, 5),
        lambda gb: gb.get_score(None, "quiz"),
    ],
)
def test_unknown_students_and_assignments_raise_key_error(book, call):
    book.record_score("ana", "quiz", 5)
    before = state(book)
    with pytest.raises(KeyError):
        call(book)
    assert state(book) == before


# --- scores -----------------------------------------------------------------


def test_zero_and_the_maximum_are_valid_scores(book):
    book.record_score("ana", "quiz", 0)
    book.record_score("ana", "essay", 20)
    assert book.get_score("ana", "quiz") == 0
    assert book.get_score("ana", "essay") == 20
    assert book.get_total("ana") == 20


@pytest.mark.parametrize("points", BAD_POINTS)
def test_invalid_points_are_rejected_and_change_nothing(book, points):
    book.record_score("ana", "quiz", 5)
    before = state(book)
    with pytest.raises(ValueError):
        book.record_score("ana", "quiz", points)
    assert state(book) == before


def test_the_maximum_depends_on_the_assignment(book):
    book.record_score("ana", "essay", 11)  # fine for the essay
    with pytest.raises(ValueError):
        book.record_score("ana", "quiz", 11)
    assert book.get_total("ana") == 11


def test_recording_again_replaces_the_score(book):
    book.record_score("ana", "quiz", 7)
    book.record_score("ana", "quiz", 4)
    assert book.get_score("ana", "quiz") == 4
    assert book.get_total("ana") == 4


def test_total_sums_every_recorded_score(book):
    book.record_score("ana", "quiz", 8)
    book.record_score("ana", "essay", 17)
    book.record_score("ana", "final", 90)
    assert book.get_total("ana") == 115


def test_totals_are_kept_per_student(book):
    book.record_score("ana", "quiz", 8)
    book.record_score("ben", "quiz", 3)
    book.record_score("ben", "essay", 12)
    assert book.get_total("ana") == 8
    assert book.get_total("ben") == 15
    assert book.get_score("ben", "quiz") == 3


def test_missing_scores_add_nothing_to_the_total(book):
    book.record_score("ana", "final", 60)
    assert book.get_total("ana") == 60
    with pytest.raises(GradebookError):
        book.get_score("ana", "quiz")


def test_an_unknown_student_is_reported_before_an_unknown_title_or_bad_points(book):
    with pytest.raises(KeyError):
        book.record_score("dan", "quiz", -1)
    with pytest.raises(KeyError):
        book.record_score("dan", "lab", -1)


def test_an_unknown_title_is_reported_before_bad_points(book):
    with pytest.raises(KeyError):
        book.record_score("ana", "lab", -1)


def test_failed_calls_leave_scores_unchanged(book):
    book.record_score("ana", "quiz", 5)
    before = state(book)
    for call in (
        lambda: book.record_score("ana", "quiz", 11),
        lambda: book.record_score("ana", "lab", 5),
        lambda: book.record_score("dan", "quiz", 5),
        lambda: book.add_student("ana"),
        lambda: book.add_assignment("quiz", 10),
    ):
        with pytest.raises((ValueError, KeyError, GradebookError)):
            call()
    assert state(book) == before


def test_gradebooks_do_not_share_data():
    first, second = Gradebook(), Gradebook()
    first.add_student("ana")
    first.add_assignment("quiz", 10)
    first.record_score("ana", "quiz", 5)
    assert second.get_students() == []
    assert second.get_assignments() == []
    second.add_student("ana")
    assert second.get_total("ana") == 0
