"""Hidden tests for the c_limit change (round limits). Never shown to the
writer or the editor.

Usage (with quiz.py importable, e.g. in the sandbox):
    python -m pytest changes/c_limit/private/test_limit_new.py
"""

import pytest
from quiz import Quiz, QuizError, RoundFull

BAD_LIMITS = [0, -2]


@pytest.fixture
def quiz():
    q = Quiz()
    for name in ["music", "sport", "film"]:
        q.add_round(name)
    for question in ["m1", "m2", "m3"]:
        q.add_question("music", question)
    q.add_question("sport", "s1")
    return q


def state(q):
    return [(r, q.get_questions(r)) for r in q.get_rounds()]


# --- the setting ------------------------------------------------------------


def test_every_round_starts_without_a_limit(quiz):
    assert [quiz.get_limit(r) for r in quiz.get_rounds()] == [None, None, None]
    quiz.add_round("art")
    assert quiz.get_limit("art") is None
    for n in range(20):
        quiz.add_question("art", f"a{n}")
    assert len(quiz.get_questions("art")) == 20


def test_a_round_added_again_under_an_old_name_has_no_limit(quiz):
    quiz.set_limit("film", 1)
    quiz.merge_rounds("film", "sport")
    quiz.add_round("film")
    assert quiz.get_limit("film") is None
    quiz.set_limit("sport", 1)
    quiz.drop_round("sport")
    quiz.add_round("sport")
    assert quiz.get_limit("sport") is None
    quiz.add_question("sport", "x1")
    quiz.add_question("sport", "x2")
    assert quiz.get_questions("sport") == ["x1", "x2"]


def test_each_setting_replaces_the_one_before(quiz):
    quiz.set_limit("film", 1)
    quiz.set_limit("film", 2)
    assert quiz.get_limit("film") == 2
    quiz.add_question("film", "f1")
    quiz.add_question("film", "f2")
    quiz.set_limit("film", None)
    assert quiz.get_limit("film") is None
    quiz.add_question("film", "f3")
    assert quiz.get_questions("film") == ["f1", "f2", "f3"]


@pytest.mark.parametrize("limit", BAD_LIMITS)
def test_limits_of_0_or_less_are_rejected_and_keep_the_old_one(quiz, limit):
    quiz.set_limit("sport", 4)
    with pytest.raises(ValueError):
        quiz.set_limit("sport", limit)
    assert quiz.get_limit("sport") == 4


@pytest.mark.parametrize(
    "call",
    [
        lambda q: q.set_limit("art", 3),
        lambda q: q.get_limit("art"),
        lambda q: q.set_limit("film", 3),  # dropped below
        lambda q: q.get_limit("film"),
    ],
)
def test_rounds_not_in_use_raise_key_error(quiz, call):
    quiz.drop_round("film")
    with pytest.raises(KeyError):
        call(quiz)


def test_a_setting_changes_no_questions(quiz):
    before = state(quiz)
    quiz.set_limit("music", 1)
    quiz.set_limit("film", 5)
    assert state(quiz) == before


# --- add_question and move_question -------------------------------------------


def test_filling_a_round_exactly_is_allowed(quiz):
    quiz.set_limit("film", 2)
    quiz.add_question("film", "f1")
    quiz.add_question("film", "f2")
    before = state(quiz)
    with pytest.raises(RoundFull):
        quiz.add_question("film", "f3")
    assert state(quiz) == before


def test_move_into_a_round_with_room(quiz):
    quiz.set_limit("sport", 2)
    quiz.move_question("m2", "sport")
    assert quiz.get_questions("sport") == ["s1", "m2"]


def test_move_into_a_full_round_changes_nothing(quiz):
    quiz.set_limit("sport", 1)
    before = state(quiz)
    with pytest.raises(RoundFull):
        quiz.move_question("m2", "sport")
    assert state(quiz) == before


def test_a_limit_only_applies_to_its_own_round(quiz):
    quiz.set_limit("film", 1)
    quiz.add_question("sport", "s2")
    quiz.move_question("m1", "sport")
    assert quiz.get_questions("sport") == ["s1", "s2", "m1"]


# --- merge_rounds -------------------------------------------------------------


def test_merge_into_a_round_with_room(quiz):
    quiz.set_limit("sport", 4)
    assert quiz.merge_rounds("music", "sport") == 3
    assert quiz.get_questions("sport") == ["s1", "m1", "m2", "m3"]
    assert quiz.get_rounds() == ["sport", "film"]


def test_merge_into_a_round_without_room_moves_nothing_and_keeps_the_source(quiz):
    quiz.set_limit("sport", 3)
    before = state(quiz)
    with pytest.raises(RoundFull):
        quiz.merge_rounds("music", "sport")
    assert state(quiz) == before
    assert quiz.get_rounds() == ["music", "sport", "film"]


def test_a_refused_merge_can_be_retried_with_a_larger_limit(quiz):
    quiz.set_limit("film", 2)
    with pytest.raises(RoundFull):
        quiz.merge_rounds("music", "film")
    quiz.set_limit("film", 3)
    assert quiz.merge_rounds("music", "film") == 3
    assert quiz.get_questions("film") == ["m1", "m2", "m3"]


def test_the_limit_of_the_round_questions_leave_is_not_checked(quiz):
    quiz.set_limit("music", 1)
    quiz.move_question("m1", "film")
    assert quiz.merge_rounds("music", "sport") == 2
    assert quiz.get_questions("sport") == ["s1", "m2", "m3"]


# --- questions already there ----------------------------------------------------


def test_a_limit_below_the_questions_held_keeps_them(quiz):
    quiz.set_limit("music", 1)  # music holds 3 questions
    assert quiz.get_questions("music") == ["m1", "m2", "m3"]
    with pytest.raises(RoundFull):
        quiz.move_question("s1", "music")
    with pytest.raises(RoundFull):
        quiz.merge_rounds("sport", "music")
    quiz.remove_question("m1")
    quiz.move_question("m2", "film")
    with pytest.raises(RoundFull):
        quiz.add_question("music", "m4")
    quiz.remove_question("m3")
    quiz.add_question("music", "m4")
    assert quiz.get_questions("music") == ["m4"]


def test_remove_and_drop_never_check_the_limit(quiz):
    quiz.set_limit("music", 1)
    quiz.remove_question("m3")
    assert quiz.drop_round("music") == 2
    assert quiz.get_rounds() == ["sport", "film"]


def test_round_full_is_a_quiz_error():
    assert issubclass(RoundFull, QuizError)


# --- undo -----------------------------------------------------------------------


def test_undoing_set_limit_gives_back_the_old_limit(quiz):
    quiz.set_limit("film", 1)
    quiz.set_limit("film", 4)
    quiz.undo()
    assert quiz.get_limit("film") == 1
    quiz.undo()
    assert quiz.get_limit("film") is None


def test_undoing_an_add_keeps_the_limit(quiz):
    quiz.set_limit("film", 1)
    quiz.add_question("film", "f1")
    quiz.undo()
    assert quiz.get_questions("film") == []
    assert quiz.get_limit("film") == 1
    quiz.add_question("film", "f2")
    with pytest.raises(RoundFull):
        quiz.add_question("film", "f3")


def test_an_undone_merge_brings_the_round_back_with_its_limit(quiz):
    quiz.set_limit("music", 3)
    quiz.merge_rounds("music", "film")
    quiz.undo()
    assert quiz.get_limit("music") == 3
    with pytest.raises(RoundFull):
        quiz.add_question("music", "m4")


def test_failed_calls_on_full_rounds_are_not_recorded(quiz):
    quiz.set_limit("sport", 1)
    for call in (
        lambda: quiz.add_question("sport", "s2"),
        lambda: quiz.move_question("m1", "sport"),
        lambda: quiz.merge_rounds("music", "sport"),
    ):
        with pytest.raises(RoundFull):
            call()
    quiz.undo()  # the limit
    assert quiz.get_limit("sport") is None
    assert quiz.get_questions("sport") == ["s1"]
