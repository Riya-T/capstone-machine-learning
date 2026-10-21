"""Hidden tests for the initial light_grid spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with lights.py importable, e.g. in the sandbox):
    python -m pytest private/test_lights_initial.py
"""

import pytest
from lights import LightGrid

COMMANDS = ["turn_on", "turn_off", "toggle"]


@pytest.fixture
def grid():
    return LightGrid(5, 4)


def state(g, width=5, height=4):
    """Every light, row by row, to check that a failed call changed nothing."""
    return [[g.is_on(x, y) for x in range(width)] for y in range(height)]


def picture(g, width=5, height=4):
    return ["".join("#" if g.is_on(x, y) else "." for x in range(width)) for y in range(height)]


# --- the grid ---------------------------------------------------------------


def test_every_light_starts_off(grid):
    assert state(grid) == [[False] * 5 for _ in range(4)]
    assert grid.get_lit_count() == 0


@pytest.mark.parametrize("bad", [0, -1, 2.5, "3", None])
def test_invalid_sizes_are_rejected(bad):
    with pytest.raises(ValueError):
        LightGrid(bad, 3)
    with pytest.raises(ValueError):
        LightGrid(3, bad)


def test_a_one_by_one_grid_works():
    g = LightGrid(1, 1)
    g.toggle(0, 0, 0, 0)
    assert g.is_on(0, 0)
    assert g.get_lit_count() == 1


def test_width_counts_columns_and_height_counts_rows():
    g = LightGrid(6, 2)
    g.turn_on(5, 1, 5, 1)
    assert g.is_on(5, 1)
    with pytest.raises(ValueError):
        g.turn_on(1, 5, 1, 5)
    with pytest.raises(ValueError):
        g.is_on(1, 5)
    assert g.get_lit_count() == 1


def test_grids_do_not_share_lights():
    first, second = LightGrid(3, 3), LightGrid(3, 3)
    first.turn_on(0, 0, 2, 2)
    assert second.get_lit_count() == 0
    assert not second.is_on(1, 1)


# --- commands ---------------------------------------------------------------


def test_a_single_light_rectangle(grid):
    grid.turn_on(3, 2, 3, 2)
    assert grid.get_lit_count() == 1
    assert picture(grid) == [".....", ".....", "...#.", "....."]


def test_a_rectangle_covers_every_row_and_column_between_its_corners(grid):
    grid.turn_on(1, 1, 3, 2)
    assert picture(grid) == [".....", ".###.", ".###.", "....."]
    assert grid.get_lit_count() == 6


def test_the_whole_grid_can_be_switched_at_once(grid):
    grid.turn_on(0, 0, 4, 3)
    assert grid.get_lit_count() == 20
    grid.turn_off(0, 0, 4, 3)
    assert grid.get_lit_count() == 0


def test_turning_on_lit_lights_keeps_them_on(grid):
    grid.turn_on(0, 0, 2, 0)
    grid.turn_on(1, 0, 3, 0)
    assert picture(grid)[0] == "####."
    assert grid.get_lit_count() == 4


def test_turning_off_dark_lights_keeps_them_off(grid):
    grid.turn_on(0, 0, 1, 0)
    grid.turn_off(1, 0, 4, 1)
    assert picture(grid) == ["#....", ".....", ".....", "....."]


def test_toggling_twice_gives_the_original_lights(grid):
    grid.turn_on(0, 0, 2, 2)
    before = state(grid)
    grid.toggle(1, 1, 4, 3)
    grid.toggle(1, 1, 4, 3)
    assert state(grid) == before


def test_toggle_on_a_mixed_rectangle(grid):
    grid.turn_on(0, 0, 1, 1)
    grid.toggle(1, 0, 2, 1)
    assert picture(grid) == ["#.#..", "#.#..", ".....", "....."]
    assert grid.get_lit_count() == 4


def test_commands_apply_in_the_order_given(grid):
    grid.turn_on(0, 0, 4, 3)
    grid.turn_off(1, 1, 3, 2)
    grid.toggle(0, 0, 4, 0)
    grid.toggle(2, 1, 2, 3)
    assert picture(grid) == [
        ".....",
        "#.#.#",
        "#.#.#",
        "##.##",
    ]
    assert grid.get_lit_count() == 10


# --- errors -----------------------------------------------------------------


@pytest.mark.parametrize("command", COMMANDS)
@pytest.mark.parametrize(
    "rect",
    [(-1, 0, 2, 2), (0, -1, 2, 2), (0, 0, 5, 2), (0, 0, 2, 4), (5, 0, 5, 0), (0, 4, 0, 4)],
)
def test_rectangles_outside_the_grid_change_nothing(grid, command, rect):
    grid.turn_on(0, 0, 1, 1)
    before = state(grid)
    with pytest.raises(ValueError):
        getattr(grid, command)(*rect)
    assert state(grid) == before


@pytest.mark.parametrize("command", COMMANDS)
@pytest.mark.parametrize("bad", [1.0, "1", None])
def test_coordinates_must_be_ints(grid, command, bad):
    grid.turn_on(0, 0, 1, 1)
    before = state(grid)
    for rect in [(bad, 0, 2, 2), (0, bad, 2, 2), (0, 0, bad, 2), (0, 0, 2, bad)]:
        with pytest.raises(ValueError):
            getattr(grid, command)(*rect)
    assert state(grid) == before


@pytest.mark.parametrize("command", COMMANDS)
def test_reversed_corners_are_rejected(grid, command):
    grid.turn_on(0, 0, 1, 1)
    before = state(grid)
    with pytest.raises(ValueError):
        getattr(grid, command)(3, 0, 1, 2)
    with pytest.raises(ValueError):
        getattr(grid, command)(0, 2, 2, 1)
    assert state(grid) == before


@pytest.mark.parametrize("point", [(-1, 0), (0, -1), (5, 0), (0, 4), (1.0, 0), ("0", 0), (0, None)])
def test_is_on_rejects_bad_coordinates(grid, point):
    grid.turn_on(0, 0, 4, 3)
    with pytest.raises(ValueError):
        grid.is_on(*point)


def test_a_rectangle_partly_outside_the_grid_changes_nothing(grid):
    with pytest.raises(ValueError):
        grid.turn_on(2, 1, 9, 1)
    with pytest.raises(ValueError):
        grid.toggle(0, 0, 4, 7)
    assert grid.get_lit_count() == 0
