"""Public checks for gradebook.py.

Usage (with gradebook.py importable, e.g. in the sandbox):
    python -m pytest public/test_gradebook_public.py
"""

import pytest
from gradebook import Gradebook, GradebookError


@pytest.fixture
def book():
    gb = Gradebook()
    gb.add_student("ana")
    gb.add_student("ben")
    gb.add_assignment("essay", 20)
    gb.add_assignment("quiz", 10)
    return gb


def test_recorded_score_is_returned(book):
    book.record_score("ana", "quiz", 7)
    assert book.get_score("ana", "quiz") == 7


def test_total_adds_up_recorded_scores(book):
    book.record_score("ana", "essay", 15)
    book.record_score("ana", "quiz", 7)
    assert book.get_total("ana") == 22
    assert book.get_total("ben") == 0


def test_points_outside_the_assignment_range_are_rejected(book):
    with pytest.raises(ValueError):
        book.record_score("ana", "quiz", 11)
    with pytest.raises(ValueError):
        book.record_score("ana", "quiz", -1)
    assert book.get_total("ana") == 0


def test_a_score_that_was_never_recorded_raises_gradebook_error(book):
    with pytest.raises(GradebookError):
        book.get_score("ana", "quiz")


def test_unknown_student_raises_key_error(book):
    with pytest.raises(KeyError):
        book.get_total("dan")
    with pytest.raises(KeyError):
        book.record_score("dan", "quiz", 5)


def test_students_and_assignments_are_listed_in_the_order_added(book):
    assert book.get_students() == ["ana", "ben"]
    assert book.get_assignments() == ["essay", "quiz"]
