"""Public checks for lights.py.

Usage (with lights.py importable, e.g. in the sandbox):
    python -m pytest public/test_lights_public.py
"""

import pytest
from lights import LightGrid


def test_new_grid_is_dark():
    grid = LightGrid(4, 3)
    assert grid.get_lit_count() == 0
    assert grid.is_on(0, 0) is False


def test_turn_on_includes_both_corners():
    grid = LightGrid(4, 3)
    grid.turn_on(1, 0, 2, 1)
    assert grid.get_lit_count() == 4
    assert grid.is_on(1, 0) and grid.is_on(2, 1)
    assert not grid.is_on(3, 1)
    assert not grid.is_on(1, 2)


def test_turn_off_part_of_a_lit_area():
    grid = LightGrid(4, 3)
    grid.turn_on(0, 0, 3, 2)
    grid.turn_off(0, 0, 3, 0)
    assert grid.get_lit_count() == 8
    assert not grid.is_on(2, 0)
    assert grid.is_on(2, 1)


def test_toggle_flips_each_light():
    grid = LightGrid(4, 3)
    grid.turn_on(0, 0, 1, 0)
    grid.toggle(1, 0, 2, 0)
    assert [grid.is_on(x, 0) for x in range(4)] == [True, False, True, False]


def test_a_rectangle_outside_the_grid_is_rejected():
    grid = LightGrid(4, 3)
    with pytest.raises(ValueError):
        grid.turn_on(0, 0, 4, 0)
    assert grid.get_lit_count() == 0


def test_size_must_be_at_least_one():
    with pytest.raises(ValueError):
        LightGrid(0, 3)
