"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with setlists.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
"""

import pytest
from setlists import SetlistError, Setlists


@pytest.fixture
def sets():
    s = Setlists()
    for name in ["friday", "saturday", "encore"]:
        s.create_setlist(name)
    for title in ["Intro", "Blue", "Run", "Home"]:
        s.add_song("friday", title)
    for title in ["Run", "Rain"]:
        s.add_song("saturday", title)
    return s


def state(s):
    return [(name, s.get_songs(name)) for name in s.get_setlists()]


# --- each call can be undone ------------------------------------------------


def test_undo_of_add_song(sets):
    before = state(sets)
    sets.add_song("encore", "Storm")
    sets.undo()
    assert state(sets) == before
    assert sets.get_songs("encore") == []


def test_undo_of_remove_song_puts_it_back_in_its_place(sets):
    before = state(sets)
    sets.remove_song("friday", "Blue")
    sets.undo()
    assert sets.get_songs("friday") == ["Intro", "Blue", "Run", "Home"]
    assert state(sets) == before


def test_undo_of_removing_the_first_song(sets):
    sets.remove_song("friday", "Intro")
    sets.undo()
    assert sets.get_songs("friday") == ["Intro", "Blue", "Run", "Home"]


def test_undo_of_move_song_puts_it_back_in_its_place(sets):
    before = state(sets)
    sets.move_song("Blue", "friday", "saturday")
    sets.undo()
    assert state(sets) == before
    assert sets.get_songs("saturday") == ["Run", "Rain"]


def test_undo_of_merge_brings_the_source_back(sets):
    before = state(sets)
    assert sets.merge_setlists("saturday", "friday") == 1
    sets.undo()
    assert state(sets) == before
    assert sets.get_setlists() == ["friday", "saturday", "encore"]
    assert sets.get_songs("friday") == ["Intro", "Blue", "Run", "Home"]


def test_undo_of_merge_keeps_the_skipped_titles_in_into(sets):
    sets.merge_setlists("friday", "saturday")
    assert sets.get_songs("saturday") == ["Run", "Rain", "Intro", "Blue", "Home"]
    sets.undo()
    assert sets.get_songs("saturday") == ["Run", "Rain"]
    assert sets.get_songs("friday") == ["Intro", "Blue", "Run", "Home"]
    assert sets.get_setlists() == ["friday", "saturday", "encore"]


def test_undo_of_merge_keeps_its_place_in_the_list(sets):
    sets.create_setlist("sunday")
    before = state(sets)
    sets.merge_setlists("saturday", "sunday")
    assert sets.get_setlists() == ["friday", "encore", "sunday"]
    sets.undo()
    assert sets.get_setlists() == ["friday", "saturday", "encore", "sunday"]
    assert state(sets) == before


def test_a_setlist_brought_back_is_in_use_again(sets):
    sets.merge_setlists("saturday", "encore")
    sets.undo()
    sets.add_song("saturday", "Storm")
    assert sets.get_songs("saturday") == ["Run", "Rain", "Storm"]
    with pytest.raises(SetlistError):
        sets.create_setlist("saturday")
    assert sets.merge_setlists("saturday", "friday") == 2
    assert sets.get_setlists() == ["friday", "encore"]


def test_undo_of_drop_song_everywhere_puts_it_back_everywhere(sets):
    sets.add_song("encore", "Run")
    before = state(sets)
    assert sets.drop_song_everywhere("Run") == 3
    sets.undo()
    assert state(sets) == before
    assert sets.get_songs("friday") == ["Intro", "Blue", "Run", "Home"]
    assert sets.get_songs("saturday") == ["Run", "Rain"]


def test_undo_of_create_setlist_removes_it_and_frees_the_name(sets):
    sets.create_setlist("sunday")
    sets.undo()
    assert sets.get_setlists() == ["friday", "saturday", "encore"]
    with pytest.raises(KeyError):
        sets.get_songs("sunday")
    sets.create_setlist("sunday")
    assert sets.get_setlists() == ["friday", "saturday", "encore", "sunday"]
    assert sets.get_songs("sunday") == []


def test_undo_of_two_merges_in_a_row(sets):
    before = state(sets)
    sets.merge_setlists("friday", "encore")
    sets.merge_setlists("encore", "saturday")
    assert sets.get_setlists() == ["saturday"]
    assert sets.get_songs("saturday") == ["Run", "Rain", "Intro", "Blue", "Home"]
    sets.undo()
    assert state(sets) == [("saturday", ["Run", "Rain"]), ("encore", ["Intro", "Blue", "Run", "Home"])]
    sets.undo()
    assert state(sets) == before


# --- calls that change nothing ------------------------------------------------


def test_a_drop_of_a_title_nobody_holds_is_still_a_call(sets):
    sets.add_song("encore", "Storm")
    assert sets.drop_song_everywhere("Thunder") == 0
    sets.undo()  # the drop, which changed nothing
    assert sets.get_songs("encore") == ["Storm"]
    sets.undo()  # the add_song
    assert sets.get_songs("encore") == []


def test_merging_an_empty_setlist_can_be_undone(sets):
    sets.add_song("friday", "Storm")
    assert sets.merge_setlists("encore", "friday") == 0
    sets.undo()
    assert sets.get_setlists() == ["friday", "saturday", "encore"]
    assert sets.get_songs("friday")[-1] == "Storm"
    sets.undo()
    assert sets.get_songs("friday") == ["Intro", "Blue", "Run", "Home"]


# --- what is and is not recorded --------------------------------------------


def test_each_undo_goes_one_call_further_back():
    s = Setlists()
    calls = [
        lambda: s.create_setlist("friday"),
        lambda: s.create_setlist("saturday"),
        lambda: s.add_song("friday", "Intro"),
        lambda: s.add_song("friday", "Blue"),
        lambda: s.add_song("friday", "Run"),
        lambda: s.create_setlist("encore"),
        lambda: s.add_song("saturday", "Run"),
        lambda: s.add_song("saturday", "Rain"),
        lambda: s.remove_song("friday", "Intro"),
        lambda: s.move_song("Blue", "friday", "encore"),
        lambda: s.drop_song_everywhere("Run"),
        lambda: s.add_song("encore", "Home"),
        lambda: s.merge_setlists("encore", "saturday"),
        lambda: s.create_setlist("sunday"),
        lambda: s.merge_setlists("friday", "sunday"),
    ]
    states = [state(s)]
    for call in calls:
        call()
        states.append(state(s))
    assert s.get_setlists() == ["saturday", "sunday"]
    assert s.get_songs("saturday") == ["Rain", "Blue", "Home"]
    for expected in reversed(states[:-1]):
        s.undo()
        assert state(s) == expected
    with pytest.raises(SetlistError):
        s.undo()
    assert s.get_setlists() == []


def test_failed_calls_are_not_recorded(sets):
    sets.add_song("encore", "Storm")
    for call in (
        lambda: sets.create_setlist("friday"),
        lambda: sets.add_song("friday", "Blue"),
        lambda: sets.add_song("sunday", "Blue"),
        lambda: sets.remove_song("friday", "Rain"),
        lambda: sets.move_song("Run", "friday", "saturday"),
        lambda: sets.move_song("Blue", "friday", "friday"),
        lambda: sets.merge_setlists("friday", "friday"),
        lambda: sets.merge_setlists("sunday", "friday"),
    ):
        with pytest.raises((ValueError, KeyError, SetlistError)):
            call()
    sets.undo()  # the add_song of Storm
    assert sets.get_songs("encore") == []
    assert sets.get_songs("friday") == ["Intro", "Blue", "Run", "Home"]


def test_get_calls_are_not_recorded(sets):
    sets.add_song("encore", "Storm")
    sets.get_songs("encore")
    sets.get_setlists()
    sets.undo()
    assert sets.get_songs("encore") == []
    assert sets.get_songs("saturday") == ["Run", "Rain"]


def test_there_is_no_redo():
    s = Setlists()
    s.create_setlist("friday")
    s.add_song("friday", "Blue")
    s.undo()
    s.undo()
    assert s.get_setlists() == []
    with pytest.raises(SetlistError):
        s.undo()


def test_new_calls_after_an_undo_are_undone_first(sets):
    sets.add_song("encore", "Storm")
    sets.undo()
    sets.add_song("encore", "Thunder")
    sets.undo()
    assert sets.get_songs("encore") == []
    sets.undo()  # the last add_song of the fixture
    assert sets.get_songs("saturday") == ["Run"]
    assert sets.get_songs("friday") == ["Intro", "Blue", "Run", "Home"]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    s = Setlists()
    with pytest.raises(SetlistError):
        s.undo()
    s.create_setlist("friday")
    s.undo()
    with pytest.raises(SetlistError):
        s.undo()
    assert s.get_setlists() == []
    s.create_setlist("friday")
    s.add_song("friday", "Blue")
    assert s.get_songs("friday") == ["Blue"]


def test_the_whole_fixture_can_be_undone(sets):
    for _ in range(9):
        sets.undo()
    assert sets.get_setlists() == []
    with pytest.raises(SetlistError):
        sets.undo()


def test_undo_restores_titles_that_a_later_call_checks(sets):
    sets.remove_song("friday", "Run")
    sets.undo()
    with pytest.raises(SetlistError):
        sets.add_song("friday", "Run")
    assert sets.merge_setlists("saturday", "friday") == 1
    assert sets.get_songs("friday") == ["Intro", "Blue", "Run", "Home", "Rain"]
