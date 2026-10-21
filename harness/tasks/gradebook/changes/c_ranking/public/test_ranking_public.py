"""Public checks for the c_ranking change (class rankings). Shown to the
editor, never to the writer.

Usage (with gradebook.py importable, e.g. in the sandbox):
    python -m pytest changes/c_ranking/public/test_ranking_public.py
"""

import pytest
from gradebook import Gradebook


@pytest.fixture
def book():
    gb = Gradebook()
    for name in ["ana", "ben", "cho"]:
        gb.add_student(name)
    gb.add_assignment("quiz", 10)
    gb.add_assignment("essay", 20)
    return gb


def test_ranking_puts_the_highest_total_first(book):
    book.record_score("ana", "quiz", 4)
    book.record_score("ben", "quiz", 9)
    book.record_score("cho", "essay", 6)
    assert book.get_ranking() == ["ben", "cho", "ana"]
    assert book.get_rank("cho") == 2


def test_equal_totals_keep_the_order_students_were_added(book):
    book.record_score("ben", "quiz", 5)
    book.record_score("cho", "quiz", 5)
    assert book.get_ranking() == ["ben", "cho", "ana"]


def test_assignment_ranking_lists_only_students_with_a_score(book):
    book.record_score("ana", "quiz", 3)
    book.record_score("cho", "quiz", 8)
    assert book.get_assignment_ranking("quiz") == ["cho", "ana"]
