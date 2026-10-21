"""Hidden tests for the c_drop_lowest change (totals that drop the lowest
scores). Never shown to the writer or the editor.

Usage (with gradebook.py importable, e.g. in the sandbox):
    python -m pytest changes/c_drop_lowest/private/test_drop_lowest_new.py
"""

import pytest
from gradebook import Gradebook

BAD_COUNTS = [-1, 1.5, "1", True, None]


@pytest.fixture
def book():
    gb = Gradebook()
    gb.add_student("ana")
    gb.add_student("ben")
    gb.add_assignment("quiz", 10)
    gb.add_assignment("essay", 20)
    gb.add_assignment("final", 100)
    gb.add_assignment("lab", 50)
    return gb


def test_dropping_zero_scores_equals_the_total(book):
    book.record_score("ana", "quiz", 4)
    book.record_score("ana", "lab", 30)
    assert book.get_total_dropping("ana", 0) == 34
    assert book.get_dropped("ana", 0) == []


def test_the_single_lowest_score_is_dropped(book):
    book.record_score("ana", "quiz", 9)
    book.record_score("ana", "essay", 6)
    book.record_score("ana", "final", 50)
    assert book.get_total_dropping("ana", 1) == 59
    assert book.get_dropped("ana", 1) == ["essay"]


def test_several_lowest_scores_are_dropped(book):
    book.record_score("ana", "quiz", 9)
    book.record_score("ana", "essay", 6)
    book.record_score("ana", "final", 50)
    book.record_score("ana", "lab", 7)
    assert book.get_total_dropping("ana", 2) == 59
    assert book.get_dropped("ana", 2) == ["essay", "lab"]
    assert book.get_total_dropping("ana", 3) == 50
    assert book.get_dropped("ana", 3) == ["quiz", "essay", "lab"]


@pytest.mark.parametrize("count", [3, 4, 10])
def test_dropping_every_score_gives_zero(book, count):
    book.record_score("ana", "quiz", 9)
    book.record_score("ana", "essay", 6)
    book.record_score("ana", "lab", 7)
    assert book.get_total_dropping("ana", count) == 0
    assert book.get_dropped("ana", count) == ["quiz", "essay", "lab"]


def test_a_student_without_scores_drops_nothing(book):
    assert book.get_total_dropping("ben", 2) == 0
    assert book.get_dropped("ben", 2) == []


def test_only_recorded_scores_can_be_dropped(book):
    # A missing assignment is not a score of 0: the recorded 0 is dropped,
    # and the missing one never appears in the dropped list.
    book.record_score("ana", "quiz", 0)
    book.record_score("ana", "final", 40)
    assert book.get_dropped("ana", 1) == ["quiz"]
    assert book.get_total_dropping("ana", 1) == 40
    assert book.get_dropped("ana", 2) == ["quiz", "final"]


def test_dropped_titles_follow_the_order_assignments_were_added(book):
    book.record_score("ana", "lab", 1)
    book.record_score("ana", "final", 90)
    book.record_score("ana", "essay", 2)
    book.record_score("ana", "quiz", 3)
    assert book.get_dropped("ana", 3) == ["quiz", "essay", "lab"]


def test_equal_scores_drop_the_earlier_assignment_first(book):
    # "quiz" was added before "essay" although it sorts after it.
    book.record_score("ana", "essay", 5)
    book.record_score("ana", "quiz", 5)
    book.record_score("ana", "final", 5)
    assert book.get_dropped("ana", 1) == ["quiz"]
    assert book.get_dropped("ana", 2) == ["quiz", "essay"]
    assert book.get_total_dropping("ana", 2) == 5


def test_dropping_is_per_student(book):
    book.record_score("ana", "quiz", 2)
    book.record_score("ana", "essay", 18)
    book.record_score("ben", "quiz", 8)
    book.record_score("ben", "essay", 3)
    assert book.get_total_dropping("ana", 1) == 18
    assert book.get_dropped("ana", 1) == ["quiz"]
    assert book.get_total_dropping("ben", 1) == 8
    assert book.get_dropped("ben", 1) == ["essay"]


def test_replacing_a_score_changes_what_is_dropped(book):
    book.record_score("ana", "quiz", 2)
    book.record_score("ana", "essay", 18)
    assert book.get_dropped("ana", 1) == ["quiz"]
    book.record_score("ana", "quiz", 10)
    book.record_score("ana", "essay", 1)
    assert book.get_dropped("ana", 1) == ["essay"]
    assert book.get_total_dropping("ana", 1) == 10


@pytest.mark.parametrize("count", BAD_COUNTS)
@pytest.mark.parametrize("method", ["get_total_dropping", "get_dropped"])
def test_invalid_counts_are_rejected(book, method, count):
    book.record_score("ana", "quiz", 5)
    with pytest.raises(ValueError):
        getattr(book, method)("ana", count)
    assert book.get_total("ana") == 5


@pytest.mark.parametrize("name", ["dan", None, 1])
@pytest.mark.parametrize("method", ["get_total_dropping", "get_dropped"])
def test_unknown_students_raise_key_error(book, method, name):
    with pytest.raises(KeyError):
        getattr(book, method)(name, 1)


def test_an_unknown_student_is_reported_before_a_bad_count(book):
    with pytest.raises(KeyError):
        book.get_total_dropping("dan", -1)
    with pytest.raises(KeyError):
        book.get_dropped("dan", -1)


def test_dropping_does_not_change_the_gradebook(book):
    book.record_score("ana", "quiz", 2)
    book.record_score("ana", "essay", 18)
    book.get_total_dropping("ana", 1)
    book.get_dropped("ana", 1)
    assert book.get_total("ana") == 20
    assert book.get_score("ana", "quiz") == 2
