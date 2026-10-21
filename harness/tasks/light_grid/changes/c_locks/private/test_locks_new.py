"""Hidden tests for the c_locks change (locked lights).
Never shown to the writer or the editor.

Usage (with lights.py importable, e.g. in the sandbox):
    python -m pytest changes/c_locks/private/test_locks_new.py
"""

import pytest
from lights import LightGrid


@pytest.fixture
def grid():
    return LightGrid(4, 3, max_brightness=5)


def levels(g, width=4, height=3):
    return [[g.get_brightness(x, y) for x in range(width)] for y in range(height)]


def locks(g, width=4, height=3):
    return [[g.is_locked(x, y) for x in range(width)] for y in range(height)]


def test_lock_new_grid_has_nothing_locked(grid):
    assert grid.get_locked_count() == 0
    assert locks(grid) == [[False] * 4 for _ in range(3)]


def test_lock_turn_off_leaves_locked_lights_on(grid):
    grid.turn_on(0, 0, 3, 2, step=2)
    grid.lock(0, 0, 0, 2)
    grid.turn_off(0, 0, 3, 2, step=5)
    assert levels(grid) == [[2, 0, 0, 0], [2, 0, 0, 0], [2, 0, 0, 0]]
    assert grid.get_lit_count() == 3


def test_lock_toggle_leaves_locked_lights_alone(grid):
    grid.turn_on(0, 0, 1, 0, step=3)
    grid.lock(1, 0, 2, 0)
    grid.toggle(0, 0, 3, 0)
    assert levels(grid)[0] == [0, 3, 0, 5]
    assert grid.get_lit_count() == 2


def test_lock_keeps_the_brightness_of_a_light(grid):
    grid.turn_on(2, 2, 2, 2, step=3)
    grid.lock(2, 2, 2, 2)
    grid.turn_on(0, 0, 3, 2)
    grid.turn_off(2, 0, 3, 2, step=4)
    assert grid.get_brightness(2, 2) == 3
    assert grid.get_brightness(3, 2) == 0
    assert grid.get_brightness(1, 2) == 1


def test_lock_and_unlock_never_change_a_light(grid):
    grid.turn_on(0, 0, 1, 1, step=4)
    before = levels(grid)
    grid.lock(0, 0, 3, 2)
    assert levels(grid) == before
    grid.unlock(0, 0, 3, 2)
    assert levels(grid) == before
    assert grid.get_lit_count() == 4


def test_lock_twice_or_unlock_twice_is_harmless(grid):
    grid.lock(0, 0, 1, 0)
    grid.lock(0, 0, 1, 0)
    assert grid.get_locked_count() == 2
    grid.unlock(0, 0, 1, 0)
    grid.unlock(0, 0, 1, 0)
    assert grid.get_locked_count() == 0


def test_lock_overlapping_areas_count_each_light_once(grid):
    grid.lock(0, 0, 2, 1)
    grid.lock(1, 1, 3, 2)
    assert grid.get_locked_count() == 6 + 6 - 2


def test_lock_unlock_part_of_a_locked_area(grid):
    grid.lock(0, 0, 3, 2)
    grid.unlock(1, 1, 2, 1)
    assert grid.get_locked_count() == 10
    assert locks(grid)[1] == [True, False, False, True]
    grid.turn_on(0, 1, 3, 1)
    assert levels(grid)[1] == [0, 1, 1, 0]


def test_lock_whole_grid_makes_commands_do_nothing(grid):
    grid.turn_on(0, 0, 0, 0)
    grid.lock(0, 0, 3, 2)
    grid.turn_on(0, 0, 3, 2)
    grid.toggle(0, 0, 3, 2)
    grid.turn_off(0, 0, 3, 2)
    assert grid.get_lit_count() == 1
    assert grid.get_total_brightness() == 1


def test_lock_works_on_a_plain_on_off_grid():
    grid = LightGrid(2, 2)
    grid.turn_on(0, 0, 0, 0)
    grid.lock(0, 0, 1, 0)
    grid.toggle(0, 0, 1, 1)
    assert [[grid.is_on(x, y) for x in range(2)] for y in range(2)] == [
        [True, False],
        [True, True],
    ]


@pytest.mark.parametrize("method", ["lock", "unlock"])
@pytest.mark.parametrize("rect", [(0, 0, 4, 0), (-1, 0, 0, 0), (0, 0, 0, 3), (2, 0, 1, 0), (0, 2, 0, 1), (0, 0, 1.0, 1)])
def test_lock_bad_rectangles_change_nothing(grid, method, rect):
    grid.lock(0, 0, 1, 1)
    before = locks(grid)
    with pytest.raises(ValueError):
        getattr(grid, method)(*rect)
    assert locks(grid) == before


@pytest.mark.parametrize("point", [(-1, 0), (4, 0), (0, 3), (0, None)])
def test_lock_status_of_a_bad_light_is_rejected(grid, point):
    with pytest.raises(ValueError):
        grid.is_locked(*point)
