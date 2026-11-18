"""Hidden tests for the initial rehearsal_setlists spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with setlists.py importable, e.g. in the sandbox):
    python -m pytest private/test_setlists_initial.py
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
    """Every setlist in order with its songs, to check that a failed call
    changed nothing."""
    return [(name, s.get_songs(name)) for name in s.get_setlists()]


# --- setlists -----------------------------------------------------------------


def test_a_new_setlist_is_empty():
    s = Setlists()
    s.create_setlist("friday")
    assert s.get_songs("friday") == []


def test_a_new_object_has_no_setlists():
    assert Setlists().get_setlists() == []


def test_setlists_are_listed_in_the_order_created():
    s = Setlists()
    for name in ["saturday", "friday", "encore"]:
        s.create_setlist(name)
    assert s.get_setlists() == ["saturday", "friday", "encore"]


def test_creating_a_name_in_use_is_rejected(sets):
    before = state(sets)
    with pytest.raises(SetlistError):
        sets.create_setlist("friday")
    assert state(sets) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda s: s.add_song("sunday", "Blue"),
        lambda s: s.remove_song("sunday", "Blue"),
        lambda s: s.move_song("Rain", "sunday", "friday"),
        lambda s: s.move_song("Blue", "friday", "sunday"),
        lambda s: s.merge_setlists("sunday", "friday"),
        lambda s: s.merge_setlists("friday", "sunday"),
        lambda s: s.get_songs("sunday"),
    ],
)
def test_setlists_that_were_never_created_raise_key_error(sets, call):
    before = state(sets)
    with pytest.raises(KeyError):
        call(sets)
    assert state(sets) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda s: s.add_song("encore", "Blue"),
        lambda s: s.remove_song("encore", "Blue"),
        lambda s: s.move_song("Rain", "encore", "friday"),
        lambda s: s.move_song("Blue", "friday", "encore"),
        lambda s: s.merge_setlists("encore", "friday"),
        lambda s: s.merge_setlists("friday", "encore"),
        lambda s: s.get_songs("encore"),
    ],
)
def test_a_merged_setlist_is_not_in_use(sets, call):
    sets.merge_setlists("encore", "saturday")  # encore is empty
    before = state(sets)
    with pytest.raises(KeyError):
        call(sets)
    assert state(sets) == before


# --- adding and removing ------------------------------------------------------


def test_songs_keep_the_order_they_were_added_in(sets):
    assert sets.get_songs("friday") == ["Intro", "Blue", "Run", "Home"]
    assert sets.get_songs("saturday") == ["Run", "Rain"]


def test_adding_a_title_twice_is_rejected(sets):
    before = state(sets)
    with pytest.raises(SetlistError):
        sets.add_song("friday", "Run")
    with pytest.raises(SetlistError):
        sets.add_song("saturday", "Rain")
    assert state(sets) == before


def test_titles_are_compared_exactly(sets):
    sets.add_song("friday", "blue")
    assert sets.get_songs("friday") == ["Intro", "Blue", "Run", "Home", "blue"]


def test_remove_song_closes_the_gap(sets):
    sets.remove_song("friday", "Blue")
    assert sets.get_songs("friday") == ["Intro", "Run", "Home"]
    assert sets.get_songs("saturday") == ["Run", "Rain"]


def test_the_first_and_last_songs_can_be_removed(sets):
    sets.remove_song("friday", "Intro")
    sets.remove_song("friday", "Home")
    assert sets.get_songs("friday") == ["Blue", "Run"]


def test_removing_a_title_that_is_not_there_raises_key_error(sets):
    before = state(sets)
    with pytest.raises(KeyError):
        sets.remove_song("friday", "Rain")
    with pytest.raises(KeyError):
        sets.remove_song("encore", "Run")
    with pytest.raises(KeyError):
        sets.remove_song("friday", "blue")
    assert state(sets) == before


def test_a_removed_title_can_be_added_again_at_the_end(sets):
    sets.remove_song("friday", "Blue")
    sets.add_song("friday", "Blue")
    assert sets.get_songs("friday") == ["Intro", "Run", "Home", "Blue"]


# --- moving -------------------------------------------------------------------


def test_move_song_puts_the_title_at_the_end(sets):
    sets.move_song("Blue", "friday", "saturday")
    assert sets.get_songs("friday") == ["Intro", "Run", "Home"]
    assert sets.get_songs("saturday") == ["Run", "Rain", "Blue"]


def test_a_song_can_be_moved_into_an_empty_setlist_and_back(sets):
    sets.move_song("Intro", "friday", "encore")
    assert sets.get_songs("encore") == ["Intro"]
    sets.move_song("Intro", "encore", "friday")
    assert sets.get_songs("friday") == ["Blue", "Run", "Home", "Intro"]
    assert sets.get_songs("encore") == []


@pytest.mark.parametrize(
    "call, error",
    [
        (lambda s: s.move_song("Rain", "friday", "encore"), KeyError),
        (lambda s: s.move_song("Intro", "encore", "friday"), KeyError),
        (lambda s: s.move_song("Run", "friday", "saturday"), SetlistError),
    ],
    ids=["not_in_from", "from_empty", "already_in_to"],
)
def test_bad_moves_are_rejected(sets, call, error):
    before = state(sets)
    with pytest.raises(error):
        call(sets)
    assert state(sets) == before


# --- merging ------------------------------------------------------------------


def test_merge_appends_new_songs_and_skips_titles_already_there(sets):
    assert sets.merge_setlists("saturday", "friday") == 1
    assert sets.get_songs("friday") == ["Intro", "Blue", "Run", "Home", "Rain"]
    assert sets.get_setlists() == ["friday", "encore"]


def test_merge_keeps_the_order_of_the_source(sets):
    assert sets.merge_setlists("friday", "encore") == 4
    assert sets.get_songs("encore") == ["Intro", "Blue", "Run", "Home"]
    assert sets.get_setlists() == ["saturday", "encore"]


def test_merge_into_a_setlist_with_songs(sets):
    assert sets.merge_setlists("friday", "saturday") == 3
    assert sets.get_songs("saturday") == ["Run", "Rain", "Intro", "Blue", "Home"]


def test_merging_an_empty_setlist_appends_nothing(sets):
    assert sets.merge_setlists("encore", "friday") == 0
    assert sets.get_songs("friday") == ["Intro", "Blue", "Run", "Home"]
    assert sets.get_setlists() == ["friday", "saturday"]


def test_a_merge_where_every_title_is_skipped_still_removes_the_source(sets):
    sets.add_song("encore", "Run")
    assert sets.merge_setlists("encore", "friday") == 0
    assert sets.get_setlists() == ["friday", "saturday"]
    assert sets.get_songs("friday") == ["Intro", "Blue", "Run", "Home"]


def test_the_other_setlists_keep_their_order_after_a_merge(sets):
    sets.create_setlist("sunday")
    sets.merge_setlists("saturday", "sunday")
    assert sets.get_setlists() == ["friday", "encore", "sunday"]
    sets.merge_setlists("friday", "encore")
    assert sets.get_setlists() == ["encore", "sunday"]


def test_merging_a_setlist_into_itself_is_rejected(sets):
    before = state(sets)
    with pytest.raises(ValueError):
        sets.merge_setlists("friday", "friday")
    assert state(sets) == before


# --- dropping -----------------------------------------------------------------


def test_drop_song_everywhere_removes_it_from_every_setlist(sets):
    sets.add_song("encore", "Run")
    assert sets.drop_song_everywhere("Run") == 3
    assert state(sets) == [
        ("friday", ["Intro", "Blue", "Home"]),
        ("saturday", ["Rain"]),
        ("encore", []),
    ]


def test_drop_of_a_title_in_one_setlist(sets):
    assert sets.drop_song_everywhere("Rain") == 1
    assert sets.get_songs("saturday") == ["Run"]
    assert sets.get_songs("friday") == ["Intro", "Blue", "Run", "Home"]


def test_drop_of_a_title_no_setlist_holds_changes_nothing(sets):
    before = state(sets)
    assert sets.drop_song_everywhere("Storm") == 0
    assert sets.drop_song_everywhere("run") == 0
    assert state(sets) == before


def test_a_dropped_title_can_be_added_again(sets):
    sets.drop_song_everywhere("Blue")
    sets.add_song("friday", "Blue")
    assert sets.get_songs("friday") == ["Intro", "Run", "Home", "Blue"]


# --- general ------------------------------------------------------------------


def test_objects_do_not_share_setlists():
    first, second = Setlists(), Setlists()
    first.create_setlist("friday")
    first.add_song("friday", "Blue")
    assert second.get_setlists() == []
    second.create_setlist("friday")
    assert second.get_songs("friday") == []
