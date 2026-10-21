"""Hidden tests for the c_late change (late submissions count half). Never
shown to the writer or the editor.

Usage (with gradebook.py importable, e.g. in the sandbox):
    python -m pytest changes/c_late/private/test_late_new.py
"""

import pytest
from gradebook import Gradebook, GradebookError


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
    snap = {}
    for name in gb.get_students():
        scores = {}
        for title in gb.get_assignments():
            try:
                scores[title] = gb.get_score(name, title)
            except GradebookError:
                scores[title] = None
            scores[title] = (scores[title], gb.is_late(name, title))
        snap[name] = (gb.get_total(name), scores)
    return snap


def test_submissions_start_out_not_late(book):
    for name in ["ana", "ben"]:
        for title in ["quiz", "essay", "final"]:
            assert not book.is_late(name, title)


def test_marking_or_clearing_twice_is_harmless(book):
    book.record_score("ana", "quiz", 8)
    book.mark_late("ana", "quiz")
    book.mark_late("ana", "quiz")
    assert book.is_late("ana", "quiz")
    assert book.get_total("ana") == 4
    book.clear_late("ana", "quiz")
    book.clear_late("ana", "quiz")
    assert not book.is_late("ana", "quiz")
    assert book.get_total("ana") == 8


@pytest.mark.parametrize("method", ["mark_late", "clear_late", "is_late"])
@pytest.mark.parametrize(
    "name, title",
    [("dan", "quiz"), ("ana", "lab"), (None, "quiz"), ("ana", None), (1, "quiz")],
)
def test_unknown_students_and_assignments_raise_key_error(book, method, name, title):
    book.record_score("ana", "quiz", 5)
    before = state(book)
    with pytest.raises(KeyError):
        getattr(book, method)(name, title)
    assert state(book) == before


@pytest.mark.parametrize("points, counted", [(7, 3), (10, 5), (1, 0), (0, 0)])
def test_a_late_score_counts_half_rounded_down(book, points, counted):
    book.record_score("ana", "quiz", points)
    book.mark_late("ana", "quiz")
    assert book.get_total("ana") == counted
    assert book.get_score("ana", "quiz") == points


def test_the_flag_can_be_set_before_the_score_is_recorded(book):
    book.mark_late("ana", "essay")
    assert book.is_late("ana", "essay")
    assert book.get_total("ana") == 0
    with pytest.raises(GradebookError):
        book.get_score("ana", "essay")
    book.record_score("ana", "essay", 15)
    assert book.get_total("ana") == 7


def test_recording_again_keeps_the_flag(book):
    book.record_score("ana", "quiz", 6)
    book.mark_late("ana", "quiz")
    book.record_score("ana", "quiz", 9)
    assert book.is_late("ana", "quiz")
    assert book.get_score("ana", "quiz") == 9
    assert book.get_total("ana") == 4


def test_only_the_flagged_submission_is_affected(book):
    book.record_score("ana", "quiz", 8)
    book.record_score("ana", "essay", 14)
    book.record_score("ben", "quiz", 8)
    book.mark_late("ana", "quiz")
    assert book.get_total("ana") == 18
    assert book.get_total("ben") == 8
    assert not book.is_late("ana", "essay")
    assert not book.is_late("ben", "quiz")


def test_several_late_scores_each_count_half(book):
    book.record_score("ana", "quiz", 9)
    book.record_score("ana", "essay", 15)
    book.record_score("ana", "final", 81)
    book.mark_late("ana", "quiz")
    book.mark_late("ana", "final")
    assert book.get_total("ana") == 4 + 15 + 40


def test_clearing_one_flag_leaves_the_others(book):
    book.record_score("ana", "quiz", 10)
    book.record_score("ana", "essay", 20)
    book.mark_late("ana", "quiz")
    book.mark_late("ana", "essay")
    book.clear_late("ana", "essay")
    assert book.get_total("ana") == 25
    assert book.is_late("ana", "quiz")
    assert not book.is_late("ana", "essay")


def test_marking_records_no_score(book):
    book.mark_late("ana", "quiz")
    book.clear_late("ana", "essay")
    with pytest.raises(GradebookError):
        book.get_score("ana", "quiz")
    with pytest.raises(GradebookError):
        book.get_score("ana", "essay")
    assert book.get_total("ana") == 0


def test_an_unknown_student_is_reported_before_an_unknown_title(book):
    with pytest.raises(KeyError):
        book.mark_late("dan", "lab")
    assert book.get_students() == ["ana", "ben"]
    assert book.get_assignments() == ["quiz", "essay", "final"]
