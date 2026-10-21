"""Hidden tests for the c_brightness change (brightness levels).
Never shown to the writer or the editor.

Usage (with lights.py importable, e.g. in the sandbox):
    python -m pytest changes/c_brightness/private/test_brightness_new.py
"""

import pytest
from lights import LightGrid

BAD_LEVELS = [0, -1, 1.5, "2", True, None]


def levels(g, width=4, height=3):
    return [[g.get_brightness(x, y) for x in range(width)] for y in range(height)]


def test_brightness_starts_at_zero():
    grid = LightGrid(4, 3, max_brightness=9)
    assert levels(grid) == [[0] * 4 for _ in range(3)]
    assert grid.get_total_brightness() == 0


def test_brightness_turn_off_steps_down_but_not_below_zero():
    grid = LightGrid(4, 3, max_brightness=3)
    grid.turn_on(0, 0, 3, 0, step=3)
    grid.turn_off(0, 0, 1, 0)
    assert levels(grid)[0] == [2, 2, 3, 3]
    grid.turn_off(0, 0, 3, 0, step=2)
    assert levels(grid)[0] == [0, 0, 1, 1]
    grid.turn_off(0, 0, 3, 0)
    grid.turn_off(0, 0, 3, 0)
    assert levels(grid)[0] == [0, 0, 0, 0]


def test_brightness_step_moves_by_that_much():
    grid = LightGrid(4, 3, max_brightness=5)
    grid.turn_on(2, 1, 2, 1, step=2)
    assert grid.get_brightness(2, 1) == 2
    grid.turn_on(2, 1, 2, 1, step=2)
    assert grid.get_brightness(2, 1) == 4
    grid.turn_on(2, 1, 2, 1, step=2)
    assert grid.get_brightness(2, 1) == 5
    grid.turn_off(2, 1, 2, 1, step=3)
    assert grid.get_brightness(2, 1) == 2


def test_brightness_large_steps_stop_at_the_limits():
    grid = LightGrid(4, 3, max_brightness=4)
    grid.turn_on(0, 0, 3, 2, step=100)
    assert grid.get_total_brightness() == 48
    grid.turn_off(0, 0, 3, 2, step=100)
    assert grid.get_total_brightness() == 0


def test_brightness_toggle_switches_a_dim_light_off():
    grid = LightGrid(4, 3, max_brightness=4)
    grid.turn_on(0, 0, 1, 0)
    grid.toggle(0, 0, 2, 0)
    assert levels(grid)[0] == [0, 0, 4, 0]


def test_brightness_above_zero_counts_as_on():
    grid = LightGrid(4, 3, max_brightness=10)
    grid.turn_on(0, 0, 1, 1, step=7)
    grid.turn_off(0, 0, 0, 1, step=6)
    assert grid.is_on(0, 0) and grid.is_on(1, 1)
    assert grid.get_lit_count() == 4
    grid.turn_off(0, 0, 0, 1)
    assert not grid.is_on(0, 0)
    assert grid.get_lit_count() == 2


def test_brightness_total_adds_up_every_light():
    grid = LightGrid(4, 3, max_brightness=6)
    grid.turn_on(0, 0, 3, 2, step=2)
    grid.turn_on(1, 1, 2, 2, step=3)
    grid.toggle(3, 0, 3, 0)
    assert grid.get_total_brightness() == 2 * 12 + 3 * 4 - 2
    assert grid.get_brightness(2, 2) == 5


def test_brightness_with_maximum_one_matches_plain_on_and_off():
    grid = LightGrid(4, 3)
    grid.turn_on(0, 0, 3, 2)
    grid.turn_off(1, 1, 2, 1)
    grid.toggle(0, 0, 3, 0)
    grid.turn_on(0, 2, 0, 2, step=5)
    assert levels(grid) == [[0, 0, 0, 0], [1, 0, 0, 1], [1, 1, 1, 1]]
    assert grid.get_lit_count() == 6
    assert grid.get_total_brightness() == 6


@pytest.mark.parametrize("bad", BAD_LEVELS)
def test_brightness_invalid_maximum_is_rejected(bad):
    with pytest.raises(ValueError):
        LightGrid(4, 3, max_brightness=bad)


@pytest.mark.parametrize("command", ["turn_on", "turn_off"])
@pytest.mark.parametrize("bad", BAD_LEVELS)
def test_brightness_invalid_step_changes_nothing(command, bad):
    grid = LightGrid(4, 3, max_brightness=5)
    grid.turn_on(0, 0, 3, 2, step=2)
    before = levels(grid)
    with pytest.raises(ValueError):
        getattr(grid, command)(0, 0, 3, 2, step=bad)
    assert levels(grid) == before


@pytest.mark.parametrize("point", [(-1, 0), (4, 0), (0, 3), (1.0, 0), (0, "1")])
def test_brightness_of_a_bad_light_is_rejected(point):
    grid = LightGrid(4, 3, max_brightness=5)
    with pytest.raises(ValueError):
        grid.get_brightness(*point)


def test_brightness_bad_rectangle_with_a_step_changes_nothing():
    grid = LightGrid(4, 3, max_brightness=5)
    grid.turn_on(0, 0, 1, 1, step=3)
    before = levels(grid)
    with pytest.raises(ValueError):
        grid.turn_on(0, 0, 4, 2, step=1)
    with pytest.raises(ValueError):
        grid.turn_off(2, 0, 0, 0, step=1)
    with pytest.raises(ValueError):
        grid.turn_on(0, 0, 9, 9, step=0)
    assert levels(grid) == before
