"""Hidden tests for the c_queries change (query). Never shown to the writer
or the editor.

Usage (with setlists.py importable, e.g. in the sandbox):
    python -m pytest changes/c_queries/private/test_queries_new.py
"""

import pytest
from setlists import Setlists


@pytest.fixture
def sets():
    s = Setlists()
    for name in ["friday", "saturday", "encore", "sunday"]:
        s.create_setlist(name)
    for title in ["Intro", "Blue", "Run", "Home"]:
        s.add_song("friday", title)
    for title in ["Run", "Rain", "Intro"]:
        s.add_song("saturday", title)
    s.add_song("sunday", "Run")
    return s


def state(s):
    return [(name, s.get_songs(name)) for name in s.get_setlists()]


# --- get_setlists_with ------------------------------------------------------


def test_setlists_with_a_title_follow_the_setlist_order(sets):
    assert sets.get_setlists_with("Run") == ["friday", "saturday", "sunday"]
    assert sets.get_setlists_with("Intro") == ["friday", "saturday"]
    assert sets.get_setlists_with("Rain") == ["saturday"]


def test_a_title_nobody_holds_gives_an_empty_list(sets):
    assert sets.get_setlists_with("Storm") == []


def test_setlists_with_compares_titles_exactly(sets):
    assert sets.get_setlists_with("run") == []


def test_setlists_with_follows_changes(sets):
    sets.move_song("Blue", "friday", "encore")
    sets.remove_song("saturday", "Run")
    assert sets.get_setlists_with("Blue") == ["encore"]
    assert sets.get_setlists_with("Run") == ["friday", "sunday"]
    sets.merge_setlists("friday", "sunday")
    assert sets.get_setlists_with("Home") == ["sunday"]
    assert sets.get_setlists_with("Run") == ["sunday"]
    sets.drop_song_everywhere("Intro")
    assert sets.get_setlists_with("Intro") == []


def test_a_new_object_has_no_setlists_with_anything():
    assert Setlists().get_setlists_with("Run") == []


# --- get_common_songs -------------------------------------------------------


def test_common_songs_in_the_order_of_the_first_setlist(sets):
    assert sets.get_common_songs("friday", "saturday") == ["Intro", "Run"]
    assert sets.get_common_songs("saturday", "friday") == ["Run", "Intro"]


def test_common_songs_with_one_shared_title(sets):
    assert sets.get_common_songs("friday", "sunday") == ["Run"]
    assert sets.get_common_songs("sunday", "saturday") == ["Run"]


def test_no_common_songs_gives_an_empty_list(sets):
    assert sets.get_common_songs("friday", "encore") == []
    assert sets.get_common_songs("encore", "friday") == []


def test_common_songs_of_a_setlist_with_itself_are_all_its_songs(sets):
    assert sets.get_common_songs("friday", "friday") == ["Intro", "Blue", "Run", "Home"]
    assert sets.get_common_songs("encore", "encore") == []


@pytest.mark.parametrize(
    "first, second",
    [("monday", "friday"), ("friday", "monday"), ("monday", "monday")],
)
def test_common_songs_of_a_setlist_not_in_use_raise_key_error(sets, first, second):
    with pytest.raises(KeyError):
        sets.get_common_songs(first, second)


def test_common_songs_of_a_merged_setlist_raise_key_error(sets):
    sets.merge_setlists("sunday", "saturday")
    with pytest.raises(KeyError):
        sets.get_common_songs("sunday", "friday")


# --- nothing changes --------------------------------------------------------


def test_the_queries_change_nothing(sets):
    before = state(sets)
    sets.get_setlists_with("Run")
    sets.get_common_songs("friday", "saturday")
    assert state(sets) == before
    sets.add_song("encore", "Run")
    assert sets.get_setlists_with("Run") == ["friday", "saturday", "encore", "sunday"]
