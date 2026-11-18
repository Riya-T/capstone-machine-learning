"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with cellar.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from cellar import Cellar, CellarError


@pytest.fixture
def cellar():
    c = Cellar()
    c.add_rack("north")
    c.add_rack("south")
    return c


def test_undo_takes_back_the_last_bottles_stored(cellar):
    cellar.store("north", 2015, 6)
    cellar.store("north", 2015, 2)
    cellar.undo()
    assert cellar.get_count("north", 2015) == 6
    cellar.undo()
    assert cellar.get_vintages("north") == []


def test_undo_takes_back_bottles_taken(cellar):
    cellar.store("south", 2018, 4)
    cellar.take("south", 2018, 3)
    cellar.undo()
    assert cellar.get_count("south", 2018) == 4


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(CellarError):
        Cellar().undo()
