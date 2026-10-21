"""Public checks for the c_undo change (taking commands back).
Shown to the editor, never to the writer.

Usage (with lights.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from lights import LightGrid, NothingToUndo


def test_undo_takes_back_the_last_command():
    grid = LightGrid(3, 3)
    grid.turn_on(0, 0, 2, 2)
    grid.turn_off(0, 0, 0, 0)
    grid.undo()
    assert grid.is_on(0, 0)
    assert grid.get_lit_count() == 9


def test_undo_twice_goes_further_back():
    grid = LightGrid(3, 3)
    grid.turn_on(0, 0, 2, 2)
    grid.toggle(0, 0, 1, 0)
    grid.undo()
    grid.undo()
    assert grid.get_lit_count() == 0
    assert grid.get_undo_count() == 0


def test_undo_with_nothing_to_take_back_raises():
    grid = LightGrid(3, 3)
    with pytest.raises(NothingToUndo):
        grid.undo()
