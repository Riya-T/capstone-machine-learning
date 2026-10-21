"""Public checks for the c_locks change (locked lights).
Shown to the editor, never to the writer.

Usage (with lights.py importable, e.g. in the sandbox):
    python -m pytest changes/c_locks/public/test_locks_public.py
"""

from lights import LightGrid


def test_lock_keeps_a_light_as_it_is():
    grid = LightGrid(3, 3)
    grid.lock(1, 1, 1, 1)
    grid.turn_on(0, 0, 2, 2)
    assert grid.get_lit_count() == 8
    assert not grid.is_on(1, 1)


def test_lock_released_by_unlock():
    grid = LightGrid(3, 3)
    grid.lock(0, 0, 2, 0)
    grid.unlock(0, 0, 2, 0)
    grid.turn_on(0, 0, 2, 0)
    assert grid.get_lit_count() == 3


def test_lock_status_and_count():
    grid = LightGrid(3, 3)
    grid.lock(0, 0, 1, 1)
    assert grid.is_locked(1, 0)
    assert not grid.is_locked(2, 0)
    assert grid.get_locked_count() == 4
