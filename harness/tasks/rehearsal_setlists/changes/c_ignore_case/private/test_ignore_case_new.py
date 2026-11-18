"""Hidden tests for the c_ignore_case change (configuration). Never shown to
the writer or the editor.

Usage (with setlists.py importable, e.g. in the sandbox):
    python -m pytest changes/c_ignore_case/private/test_ignore_case_new.py
"""

import pytest
from setlists import SetlistError, Setlists


def state(s):
    return [(name, s.get_songs(name)) for name in s.get_setlists()]


@pytest.fixture
def sets():
    s = Setlists(ignore_case=True)
    for name in ["friday", "saturday", "encore"]:
        s.create_setlist(name)
    for title in ["Intro", "Blue Moon", "Run"]:
        s.add_song("friday", title)
    for title in ["RUN", "Rain"]:
        s.add_song("saturday", title)
    return s


# --- the setting -------------------------------------------------------------


def test_the_default_is_exact_comparison():
    assert Setlists().get_ignore_case() is False
    assert Setlists(ignore_case=False).get_ignore_case() is False


def test_the_setting_is_reported(sets):
    assert sets.get_ignore_case() is True


@pytest.mark.parametrize("bad", ["yes", "true"])
def test_values_other_than_true_or_false_are_rejected(bad):
    with pytest.raises(ValueError):
        Setlists(ignore_case=bad)


def test_objects_keep_their_own_setting(sets):
    exact = Setlists()
    exact.create_setlist("friday")
    exact.add_song("friday", "Run")
    exact.add_song("friday", "run")
    with pytest.raises(SetlistError):
        sets.add_song("friday", "run")
    assert exact.get_songs("friday") == ["Run", "run"]


def test_exact_comparison_keeps_the_old_behavior():
    s = Setlists(ignore_case=False)
    s.create_setlist("friday")
    s.create_setlist("saturday")
    s.add_song("friday", "Run")
    s.add_song("saturday", "RUN")
    with pytest.raises(KeyError):
        s.remove_song("friday", "run")
    assert s.merge_setlists("saturday", "friday") == 1
    assert s.get_songs("friday") == ["Run", "RUN"]
    assert s.drop_song_everywhere("run") == 0


# --- ignoring case ----------------------------------------------------------


@pytest.mark.parametrize("title", ["blue moon", "BLUE MOON", "Blue moon", "Blue Moon"])
def test_add_song_rejects_a_title_in_any_capitals(sets, title):
    before = state(sets)
    with pytest.raises(SetlistError):
        sets.add_song("friday", title)
    assert state(sets) == before


def test_other_setlists_may_still_hold_the_title(sets):
    sets.add_song("encore", "blue moon")
    assert sets.get_songs("encore") == ["blue moon"]


def test_remove_song_finds_the_title_in_any_capitals(sets):
    sets.remove_song("friday", "BLUE moon")
    assert sets.get_songs("friday") == ["Intro", "Run"]
    with pytest.raises(KeyError):
        sets.remove_song("friday", "blue moon")


def test_move_song_finds_the_title_and_keeps_its_spelling(sets):
    sets.move_song("intro", "friday", "encore")
    assert sets.get_songs("friday") == ["Blue Moon", "Run"]
    assert sets.get_songs("encore") == ["Intro"]


def test_move_song_rejects_a_target_holding_the_title_in_other_capitals(sets):
    before = state(sets)
    with pytest.raises(SetlistError):
        sets.move_song("run", "friday", "saturday")
    assert state(sets) == before


def test_move_song_of_a_title_not_there_raises_key_error(sets):
    with pytest.raises(KeyError):
        sets.move_song("storm", "friday", "encore")


def test_merge_skips_titles_held_in_other_capitals(sets):
    assert sets.merge_setlists("saturday", "friday") == 1
    assert sets.get_songs("friday") == ["Intro", "Blue Moon", "Run", "Rain"]
    assert sets.get_setlists() == ["friday", "encore"]


def test_merge_keeps_the_spelling_of_the_appended_songs(sets):
    sets.add_song("encore", "STORM")
    sets.add_song("encore", "intro")
    assert sets.merge_setlists("encore", "saturday") == 2
    assert sets.get_songs("saturday") == ["RUN", "Rain", "STORM", "intro"]


def test_drop_song_everywhere_matches_any_capitals(sets):
    sets.add_song("encore", "rUn")
    assert sets.drop_song_everywhere("run") == 3
    assert state(sets) == [
        ("friday", ["Intro", "Blue Moon"]),
        ("saturday", ["Rain"]),
        ("encore", []),
    ]


def test_drop_of_a_title_nobody_holds_still_returns_0(sets):
    before = state(sets)
    assert sets.drop_song_everywhere("storm") == 0
    assert state(sets) == before


def test_a_removed_title_can_be_added_in_other_capitals(sets):
    sets.remove_song("friday", "run")
    sets.add_song("friday", "RUN")
    assert sets.get_songs("friday") == ["Intro", "Blue Moon", "RUN"]
