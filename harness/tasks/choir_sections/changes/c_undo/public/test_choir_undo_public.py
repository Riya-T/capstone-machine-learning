"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with choir.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_choir_undo_public.py
"""

import pytest
from choir import Choir, ChoirError


@pytest.fixture
def choir():
    c = Choir()
    c.add_section("alto")
    c.add_section("tenor")
    return c


def test_undo_takes_back_the_last_singer_added(choir):
    choir.add_singer("alto", "Ada")
    choir.add_singer("alto", "Bea")
    choir.undo()
    assert choir.get_singers("alto") == ["Ada"]
    choir.undo()
    assert choir.get_singers("alto") == []


def test_undo_takes_back_a_move(choir):
    choir.add_singer("alto", "Ada")
    choir.move_singer("Ada", "tenor")
    choir.undo()
    assert choir.get_singers("alto") == ["Ada"]
    assert choir.get_singers("tenor") == []


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(ChoirError):
        Choir().undo()
