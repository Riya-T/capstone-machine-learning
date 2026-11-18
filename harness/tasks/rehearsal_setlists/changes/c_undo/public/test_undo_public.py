"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with setlists.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from setlists import SetlistError, Setlists


@pytest.fixture
def sets():
    s = Setlists()
    s.create_setlist("friday")
    s.create_setlist("encore")
    return s


def test_undo_takes_back_the_last_song_added(sets):
    sets.add_song("friday", "Intro")
    sets.add_song("friday", "Blue")
    sets.undo()
    assert sets.get_songs("friday") == ["Intro"]
    sets.undo()
    assert sets.get_songs("friday") == []


def test_undo_takes_back_a_move(sets):
    sets.add_song("friday", "Intro")
    sets.add_song("friday", "Blue")
    sets.move_song("Intro", "friday", "encore")
    sets.undo()
    assert sets.get_songs("friday") == ["Intro", "Blue"]
    assert sets.get_songs("encore") == []


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(SetlistError):
        Setlists().undo()
