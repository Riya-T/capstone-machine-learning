"""Public checks for the c_drop_lowest change (totals that drop the lowest
scores). Shown to the editor, never to the writer.

Usage (with gradebook.py importable, e.g. in the sandbox):
    python -m pytest changes/c_drop_lowest/public/test_drop_lowest_public.py
"""

import pytest
from gradebook import Gradebook


@pytest.fixture
def book():
    gb = Gradebook()
    gb.add_student("ana")
    gb.add_assignment("quiz", 10)
    gb.add_assignment("essay", 20)
    gb.add_assignment("final", 100)
    gb.record_score("ana", "quiz", 3)
    gb.record_score("ana", "essay", 15)
    gb.record_score("ana", "final", 70)
    return gb


def test_the_lowest_score_is_dropped(book):
    assert book.get_total_dropping("ana", 1) == 85
    assert book.get_dropped("ana", 1) == ["quiz"]


def test_dropping_nothing_equals_the_total(book):
    assert book.get_total_dropping("ana", 0) == book.get_total("ana") == 88
    assert book.get_dropped("ana", 0) == []


def test_dropping_more_scores_than_recorded_gives_zero(book):
    assert book.get_total_dropping("ana", 5) == 0
    assert book.get_dropped("ana", 5) == ["quiz", "essay", "final"]
