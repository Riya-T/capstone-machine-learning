"""Hidden tests for the c_ranking change (class rankings). Never shown to
the writer or the editor.

Usage (with gradebook.py importable, e.g. in the sandbox):
    python -m pytest changes/c_ranking/private/test_ranking_new.py
"""

import pytest
from gradebook import Gradebook


@pytest.fixture
def book():
    gb = Gradebook()
    for name in ["ana", "ben", "cho", "dee"]:
        gb.add_student(name)
    gb.add_assignment("quiz", 10)
    gb.add_assignment("essay", 20)
    gb.add_assignment("final", 100)
    return gb


def test_ranking_orders_by_total_highest_first(book):
    book.record_score("ana", "quiz", 5)
    book.record_score("ana", "essay", 10)  # 15
    book.record_score("ben", "final", 40)  # 40
    book.record_score("cho", "essay", 20)  # 20
    book.record_score("dee", "quiz", 1)  # 1
    assert book.get_ranking() == ["ben", "cho", "ana", "dee"]


def test_ties_keep_the_order_students_were_added(book):
    book.record_score("dee", "quiz", 7)
    book.record_score("ben", "essay", 7)
    book.record_score("ana", "quiz", 7)
    assert book.get_ranking() == ["ana", "ben", "dee", "cho"]


def test_an_empty_gradebook_has_an_empty_ranking():
    gb = Gradebook()
    assert gb.get_ranking() == []
    gb.add_assignment("quiz", 10)
    assert gb.get_ranking() == []


def test_students_without_scores_rank_last_in_added_order(book):
    book.record_score("cho", "quiz", 1)
    assert book.get_ranking() == ["cho", "ana", "ben", "dee"]


def test_rank_is_the_one_based_position(book):
    book.record_score("ana", "quiz", 2)
    book.record_score("ben", "quiz", 9)
    book.record_score("cho", "quiz", 5)
    assert book.get_rank("ben") == 1
    assert book.get_rank("cho") == 2
    assert book.get_rank("ana") == 3
    assert book.get_rank("dee") == 4


def test_tied_students_get_consecutive_ranks(book):
    book.record_score("ana", "quiz", 5)
    book.record_score("ben", "quiz", 5)
    assert book.get_rank("ana") == 1
    assert book.get_rank("ben") == 2


@pytest.mark.parametrize("name", ["eve", None, 1])
def test_rank_of_an_unknown_student_raises_key_error(book, name):
    with pytest.raises(KeyError):
        book.get_rank(name)


def test_assignment_ranking_uses_the_recorded_scores(book):
    book.record_score("ana", "quiz", 6)
    book.record_score("ben", "quiz", 10)
    book.record_score("cho", "quiz", 6)
    book.record_score("dee", "quiz", 8)
    book.record_score("ana", "essay", 20)  # other assignments do not matter
    assert book.get_assignment_ranking("quiz") == ["ben", "dee", "ana", "cho"]


def test_assignment_ranking_leaves_out_students_without_a_score(book):
    assert book.get_assignment_ranking("essay") == []
    book.record_score("dee", "essay", 3)
    book.record_score("ben", "essay", 3)
    assert book.get_assignment_ranking("essay") == ["ben", "dee"]


@pytest.mark.parametrize("title", ["lab", None, 1])
def test_assignment_ranking_of_an_unknown_title_raises_key_error(book, title):
    with pytest.raises(KeyError):
        book.get_assignment_ranking(title)


def test_late_scores_lower_the_ranking(book):
    book.record_score("ana", "quiz", 10)
    book.record_score("ben", "quiz", 6)
    assert book.get_ranking() == ["ana", "ben", "cho", "dee"]
    book.mark_late("ana", "quiz")  # ana now counts 5
    assert book.get_ranking() == ["ben", "ana", "cho", "dee"]
    assert book.get_rank("ana") == 2
    book.clear_late("ana", "quiz")
    assert book.get_rank("ana") == 1


def test_assignment_ranking_ignores_the_late_flag(book):
    book.record_score("ana", "quiz", 10)
    book.record_score("ben", "quiz", 6)
    book.mark_late("ana", "quiz")
    assert book.get_assignment_ranking("quiz") == ["ana", "ben"]


def test_replacing_a_score_changes_the_ranking(book):
    book.record_score("ana", "quiz", 9)
    book.record_score("ben", "quiz", 4)
    assert book.get_ranking()[:2] == ["ana", "ben"]
    book.record_score("ana", "quiz", 2)
    assert book.get_ranking()[:2] == ["ben", "ana"]
    assert book.get_assignment_ranking("quiz") == ["ben", "ana"]


def test_rankings_do_not_change_the_gradebook(book):
    book.record_score("ana", "quiz", 9)
    book.get_ranking()
    book.get_rank("ben")
    book.get_assignment_ranking("quiz")
    assert book.get_students() == ["ana", "ben", "cho", "dee"]
    assert book.get_total("ana") == 9
    assert book.get_total("ben") == 0
