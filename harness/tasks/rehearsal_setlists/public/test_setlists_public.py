"""Public checks for setlists.py.

Usage (with setlists.py importable, e.g. in the sandbox):
    python -m pytest public/test_setlists_public.py
"""

import pytest
from setlists import SetlistError, Setlists


@pytest.fixture
def sets():
    s = Setlists()
    s.create_setlist("friday")
    s.create_setlist("encore")
    for title in ["Intro", "Blue", "Run"]:
        s.add_song("friday", title)
    return s


def test_songs_are_kept_in_the_order_added(sets):
    assert sets.get_songs("friday") == ["Intro", "Blue", "Run"]
    assert sets.get_songs("encore") == []
    assert sets.get_setlists() == ["friday", "encore"]


def test_a_setlist_holds_each_title_once(sets):
    with pytest.raises(SetlistError):
        sets.add_song("friday", "Blue")
    sets.add_song("encore", "Blue")
    assert sets.get_songs("friday") == ["Intro", "Blue", "Run"]
    assert sets.get_songs("encore") == ["Blue"]


def test_removing_a_song_closes_the_gap(sets):
    sets.remove_song("friday", "Blue")
    assert sets.get_songs("friday") == ["Intro", "Run"]
    with pytest.raises(KeyError):
        sets.remove_song("friday", "Blue")


def test_a_moved_song_goes_to_the_end(sets):
    sets.add_song("encore", "Home")
    sets.move_song("Intro", "friday", "encore")
    assert sets.get_songs("friday") == ["Blue", "Run"]
    assert sets.get_songs("encore") == ["Home", "Intro"]


def test_merge_appends_new_songs_and_removes_the_source(sets):
    sets.add_song("encore", "Run")
    sets.add_song("encore", "Home")
    assert sets.merge_setlists("encore", "friday") == 1
    assert sets.get_songs("friday") == ["Intro", "Blue", "Run", "Home"]
    assert sets.get_setlists() == ["friday"]
    with pytest.raises(KeyError):
        sets.get_songs("encore")


def test_drop_song_everywhere_returns_how_many_setlists(sets):
    sets.add_song("encore", "Blue")
    assert sets.drop_song_everywhere("Blue") == 2
    assert sets.get_songs("friday") == ["Intro", "Run"]
    assert sets.get_songs("encore") == []
    assert sets.drop_song_everywhere("Blue") == 0
