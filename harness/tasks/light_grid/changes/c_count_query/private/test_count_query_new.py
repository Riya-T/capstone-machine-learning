"""Hidden tests for the c_count_query change (queries over a rectangle).
Never shown to the writer or the editor.

Usage (with lights.py importable, e.g. in the sandbox):
    python -m pytest changes/c_count_query/private/test_count_query_new.py
"""

import pytest
from lights import LightGrid


@pytest.fixture
def grid():
    # . # . . #
    # # . . # .
    # . . # . .
    g = LightGrid(5, 3)
    g.turn_on(1, 0, 1, 0)
    g.turn_on(4, 0, 4, 0)
    g.turn_on(0, 1, 0, 1)
    g.turn_on(3, 1, 3, 1)
    g.turn_on(2, 2, 2, 2)
    return g


def state(g, width=5, height=3):
    return [[g.is_on(x, y) for x in range(width)] for y in range(height)]


def test_query_count_includes_both_corners(grid):
    assert grid.get_count_in(1, 0, 3, 1) == 2
    assert grid.get_count_in(0, 1, 3, 2) == 3


def test_query_count_reaches_the_last_column_and_row(grid):
    assert grid.get_count_in(4, 0, 4, 2) == 1
    assert grid.get_count_in(2, 2, 4, 2) == 1
    assert grid.get_count_in(3, 0, 4, 1) == 2


def test_query_count_of_the_whole_grid_is_the_lit_count(grid):
    assert grid.get_count_in(0, 0, 4, 2) == grid.get_lit_count() == 5


def test_query_count_of_a_single_light(grid):
    assert grid.get_count_in(3, 1, 3, 1) == 1
    assert grid.get_count_in(3, 0, 3, 0) == 0


def test_query_lit_lights_go_row_by_row_then_column(grid):
    assert grid.get_lit_in(0, 0, 4, 2) == [(1, 0), (4, 0), (0, 1), (3, 1), (2, 2)]
    assert grid.get_lit_in(0, 0, 3, 1) == [(1, 0), (0, 1), (3, 1)]


def test_query_lit_lights_only_inside_the_rectangle(grid):
    assert grid.get_lit_in(1, 1, 2, 2) == [(2, 2)]
    assert grid.get_lit_in(2, 0, 3, 0) == []


def test_query_row_counts_one_per_row(grid):
    assert grid.get_row_counts() == [2, 2, 1]
    grid.toggle(0, 0, 4, 0)
    assert grid.get_row_counts() == [3, 2, 1]


def test_query_row_counts_of_a_new_grid():
    assert LightGrid(2, 4).get_row_counts() == [0, 0, 0, 0]
    assert LightGrid(3, 1).get_row_counts() == [0]


def test_query_results_follow_later_commands(grid):
    grid.turn_off(0, 0, 4, 1)
    assert grid.get_count_in(0, 0, 4, 2) == 1
    assert grid.get_lit_in(0, 0, 4, 2) == [(2, 2)]
    assert grid.get_row_counts() == [0, 0, 1]


@pytest.mark.parametrize("method", ["get_count_in", "get_lit_in"])
@pytest.mark.parametrize(
    "rect",
    [(0, 0, 5, 2), (-1, 0, 1, 1), (0, 0, 1, 3), (3, 0, 2, 0), (0, 2, 0, 1), (0, 0, 1.0, 1), ("0", 0, 1, 1)],
)
def test_query_bad_rectangles_are_rejected(grid, method, rect):
    before = state(grid)
    with pytest.raises(ValueError):
        getattr(grid, method)(*rect)
    assert state(grid) == before


def test_query_methods_change_nothing(grid):
    before = state(grid)
    grid.get_count_in(0, 0, 4, 2)
    grid.get_lit_in(0, 0, 4, 2)
    grid.get_row_counts()
    assert state(grid) == before
