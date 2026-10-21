"""Public checks for the c_count_query change (queries over a rectangle).
Shown to the editor, never to the writer.

Usage (with lights.py importable, e.g. in the sandbox):
    python -m pytest changes/c_count_query/public/test_count_query_public.py
"""

import pytest
from lights import LightGrid


@pytest.fixture
def grid():
    g = LightGrid(4, 3)
    g.turn_on(1, 0, 2, 1)
    g.turn_on(3, 2, 3, 2)
    return g


def test_query_count_in_a_rectangle(grid):
    assert grid.get_count_in(0, 0, 1, 2) == 2
    assert grid.get_count_in(0, 0, 3, 2) == 5


def test_query_lit_lights_row_by_row(grid):
    assert grid.get_lit_in(0, 0, 3, 2) == [(1, 0), (2, 0), (1, 1), (2, 1), (3, 2)]


def test_query_row_counts(grid):
    assert grid.get_row_counts() == [2, 2, 1]
