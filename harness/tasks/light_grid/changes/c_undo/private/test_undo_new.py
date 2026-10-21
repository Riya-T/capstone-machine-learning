"""Hidden tests for the c_undo change (taking commands back).
Never shown to the writer or the editor.

Usage (with lights.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
"""

import pytest
from lights import LightGrid, NothingToUndo


@pytest.fixture
def grid():
    return LightGrid(4, 3, max_brightness=4)


def levels(g, width=4, height=3):
    return [[g.get_brightness(x, y) for x in range(width)] for y in range(height)]


def test_undo_new_grid_has_nothing_to_take_back(grid):
    assert grid.get_undo_count() == 0
    with pytest.raises(NothingToUndo):
        grid.undo()
    assert levels(grid) == [[0] * 4 for _ in range(3)]


def test_undo_restores_the_brightness_from_before_a_capped_step(grid):
    grid.turn_on(0, 0, 1, 0, step=3)
    grid.turn_on(0, 0, 2, 0, step=3)
    assert levels(grid)[0] == [4, 4, 3, 0]
    grid.undo()
    assert levels(grid)[0] == [3, 3, 0, 0]


def test_undo_restores_the_brightness_from_before_a_turn_off(grid):
    grid.turn_on(0, 0, 3, 0, step=2)
    grid.turn_on(0, 0, 0, 0, step=2)
    grid.turn_off(0, 0, 3, 0, step=3)
    assert levels(grid)[0] == [1, 0, 0, 0]
    grid.undo()
    assert levels(grid)[0] == [4, 2, 2, 2]


def test_undo_of_a_toggle(grid):
    grid.turn_on(0, 0, 1, 1, step=2)
    before = levels(grid)
    grid.toggle(1, 1, 3, 2)
    grid.undo()
    assert levels(grid) == before
    assert grid.get_lit_count() == 4


def test_undo_count_follows_commands_and_undos(grid):
    grid.turn_on(0, 0, 0, 0)
    grid.turn_off(0, 0, 0, 0)
    grid.toggle(0, 0, 3, 2)
    assert grid.get_undo_count() == 3
    grid.undo()
    assert grid.get_undo_count() == 2
    grid.undo()
    grid.undo()
    assert grid.get_undo_count() == 0
    assert grid.get_total_brightness() == 0


def test_undo_of_a_command_that_changed_nothing(grid):
    grid.turn_on(0, 0, 3, 2, step=4)
    grid.turn_on(0, 0, 3, 2)  # everything is already at the maximum
    assert grid.get_undo_count() == 2
    grid.undo()
    assert grid.get_total_brightness() == 48
    grid.undo()
    assert grid.get_total_brightness() == 0


def test_undo_ignores_failed_commands(grid):
    grid.turn_on(0, 0, 0, 0)
    for call in (
        lambda: grid.turn_on(0, 0, 9, 0),
        lambda: grid.toggle(2, 0, 1, 0),
        lambda: grid.turn_off(0, 0, 0, 0, step=0),
    ):
        with pytest.raises(ValueError):
            call()
    assert grid.get_undo_count() == 1
    grid.undo()
    assert grid.get_lit_count() == 0


def test_undo_skips_lock_and_unlock(grid):
    grid.turn_on(0, 0, 1, 0)
    grid.lock(3, 2, 3, 2)
    grid.unlock(3, 2, 3, 2)
    grid.lock(0, 2, 1, 2)
    assert grid.get_undo_count() == 1
    grid.undo()
    assert grid.get_lit_count() == 0
    assert grid.get_locked_count() == 2
    assert not grid.is_locked(3, 2)


def test_undo_restores_lights_locked_since_the_command(grid):
    grid.turn_on(0, 0, 3, 0, step=2)
    grid.lock(0, 0, 1, 0)
    grid.undo()
    assert levels(grid)[0] == [0, 0, 0, 0]
    assert grid.is_locked(0, 0) and grid.is_locked(1, 0)


def test_undo_leaves_lights_that_were_locked_during_the_command(grid):
    grid.turn_on(1, 0, 1, 0, step=3)
    grid.lock(1, 0, 1, 0)
    grid.turn_on(0, 0, 3, 0)
    grid.turn_off(0, 0, 3, 0, step=4)
    grid.unlock(1, 0, 1, 0)
    grid.undo()
    assert levels(grid)[0] == [1, 3, 1, 1]
    grid.undo()
    assert levels(grid)[0] == [0, 3, 0, 0]


def test_undo_when_everything_is_taken_back_changes_nothing(grid):
    grid.turn_on(0, 0, 1, 1)
    grid.undo()
    grid.lock(0, 0, 0, 0)
    with pytest.raises(NothingToUndo):
        grid.undo()
    assert grid.get_lit_count() == 0
    assert grid.get_locked_count() == 1


def test_undo_has_no_redo(grid):
    grid.turn_on(0, 0, 0, 0)
    grid.turn_on(1, 0, 1, 0)
    grid.undo()
    grid.turn_on(2, 0, 2, 0)
    assert grid.get_undo_count() == 2
    grid.undo()
    assert levels(grid)[0] == [1, 0, 0, 0]
    grid.undo()
    assert grid.get_lit_count() == 0


def test_undo_on_a_plain_on_off_grid():
    grid = LightGrid(3, 1)
    grid.toggle(0, 0, 1, 0)
    grid.toggle(1, 0, 2, 0)
    grid.undo()
    assert [grid.is_on(x, 0) for x in range(3)] == [True, True, False]
