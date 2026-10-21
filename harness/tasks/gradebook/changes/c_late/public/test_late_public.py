"""Public checks for the c_late change (late submissions count half). Shown
to the editor, never to the writer.

Usage (with gradebook.py importable, e.g. in the sandbox):
    python -m pytest changes/c_late/public/test_late_public.py
"""

import pytest
from gradebook import Gradebook


@pytest.fixture
def book():
    gb = Gradebook()
    gb.add_student("ana")
    gb.add_assignment("quiz", 10)
    gb.add_assignment("essay", 20)
    return gb


def test_a_late_score_counts_half_in_the_total(book):
    book.record_score("ana", "quiz", 7)
    book.record_score("ana", "essay", 20)
    book.mark_late("ana", "quiz")
    assert book.is_late("ana", "quiz")
    assert book.get_score("ana", "quiz") == 7
    assert book.get_total("ana") == 23


def test_clearing_the_flag_restores_the_full_score(book):
    book.record_score("ana", "quiz", 8)
    book.mark_late("ana", "quiz")
    book.clear_late("ana", "quiz")
    assert not book.is_late("ana", "quiz")
    assert book.get_total("ana") == 8


def test_marking_an_unknown_student_raises_key_error(book):
    with pytest.raises(KeyError):
        book.mark_late("dan", "quiz")
