"""Hidden tests for the c_lock change (state_flag). Never shown to the writer
or the editor.

Usage (with setlists.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lock/private/test_lock_new.py
"""

import pytest
from setlists import SetlistError, SetlistLocked, Setlists


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


# --- lock, unlock and get_locked ----------------------------------------------


def test_new_setlists_are_not_locked(sets):
    assert sets.get_locked() == []


def test_locked_setlists_are_listed_in_setlist_order(sets):
    sets.lock("encore")
    sets.lock("friday")
    assert sets.get_locked() == ["friday", "encore"]


def test_locking_twice_and_unlocking_an_unlocked_setlist_do_nothing(sets):
    sets.lock("friday")
    sets.lock("friday")
    assert sets.get_locked() == ["friday"]
    sets.unlock("saturday")
    assert sets.get_locked() == ["friday"]
    sets.unlock("friday")
    assert sets.get_locked() == []


@pytest.mark.parametrize("call", [lambda s: s.lock("sunday"), lambda s: s.unlock("sunday")])
def test_lock_and_unlock_of_a_setlist_not_in_use_raise_key_error(sets, call):
    with pytest.raises(KeyError):
        call(sets)
    assert sets.get_locked() == []


def test_setlist_locked_is_a_setlist_error():
    assert issubclass(SetlistLocked, SetlistError)


def test_locking_changes_no_songs(sets):
    before = state(sets)
    sets.lock("friday")
    assert state(sets) == before


# --- what a lock blocks -----------------------------------------------------------


@pytest.mark.parametrize(
    "call",
    [
        lambda s: s.add_song("friday", "Storm"),
        lambda s: s.remove_song("friday", "Blue"),
        lambda s: s.move_song("Blue", "friday", "encore"),
        lambda s: s.move_song("Rain", "saturday", "friday"),
        lambda s: s.merge_setlists("friday", "encore"),
        lambda s: s.merge_setlists("saturday", "friday"),
        lambda s: s.drop_song_everywhere("Blue"),
        lambda s: s.drop_song_everywhere("Run"),
    ],
    ids=[
        "add_song",
        "remove_song",
        "move_out",
        "move_in",
        "merge_locked_source",
        "merge_into_locked",
        "drop_only_in_locked",
        "drop_also_in_locked",
    ],
)
def test_calls_that_would_change_a_locked_setlist_raise(sets, call):
    sets.lock("friday")
    before = state(sets)
    with pytest.raises(SetlistLocked):
        call(sets)
    assert state(sets) == before
    assert sets.get_setlists() == ["friday", "saturday", "encore"]


def test_other_setlists_can_still_change(sets):
    sets.lock("friday")
    sets.add_song("encore", "Storm")
    sets.move_song("Rain", "saturday", "encore")
    sets.remove_song("saturday", "Run")
    assert sets.merge_setlists("saturday", "encore") == 0
    assert state(sets) == [("friday", ["Intro", "Blue", "Run", "Home"]), ("encore", ["Storm", "Rain"])]


def test_drop_ignores_locked_setlists_without_the_title(sets):
    sets.lock("friday")
    assert sets.drop_song_everywhere("Rain") == 1
    assert sets.get_songs("saturday") == ["Run"]
    assert sets.get_songs("friday") == ["Intro", "Blue", "Run", "Home"]


def test_a_locked_setlist_that_stays_locked_keeps_blocking(sets):
    sets.lock("saturday")
    with pytest.raises(SetlistLocked):
        sets.add_song("saturday", "Storm")
    with pytest.raises(SetlistLocked):
        sets.merge_setlists("friday", "saturday")
    assert sets.get_songs("saturday") == ["Run", "Rain"]
    assert sets.get_songs("friday") == ["Intro", "Blue", "Run", "Home"]


def test_get_methods_work_on_locked_setlists(sets):
    sets.lock("friday")
    sets.lock("saturday")
    assert sets.get_songs("friday") == ["Intro", "Blue", "Run", "Home"]
    assert sets.get_setlists() == ["friday", "saturday", "encore"]


# --- unlocking ---------------------------------------------------------------------


def test_after_unlock_everything_works_again(sets):
    sets.lock("friday")
    sets.unlock("friday")
    sets.add_song("friday", "Storm")
    sets.remove_song("friday", "Intro")
    assert sets.drop_song_everywhere("Run") == 2
    assert sets.merge_setlists("friday", "encore") == 3
    assert state(sets) == [("saturday", ["Rain"]), ("encore", ["Blue", "Home", "Storm"])]
