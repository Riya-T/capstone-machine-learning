"""Public checks for the c_lock change (state_flag). Shown to the editor,
never to the writer.

Usage (with setlists.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lock/public/test_lock_public.py
"""

import pytest
from setlists import SetlistLocked, Setlists


@pytest.fixture
def sets():
    s = Setlists()
    s.create_setlist("friday")
    s.create_setlist("encore")
    s.add_song("friday", "Intro")
    return s


def test_locked_setlists_are_listed(sets):
    assert sets.get_locked() == []
    sets.lock("friday")
    assert sets.get_locked() == ["friday"]


def test_a_locked_setlist_takes_no_new_songs(sets):
    sets.lock("friday")
    with pytest.raises(SetlistLocked):
        sets.add_song("friday", "Blue")
    assert sets.get_songs("friday") == ["Intro"]


def test_unlock_lifts_the_lock(sets):
    sets.lock("friday")
    sets.unlock("friday")
    sets.add_song("friday", "Blue")
    assert sets.get_songs("friday") == ["Intro", "Blue"]
    assert sets.get_locked() == []
