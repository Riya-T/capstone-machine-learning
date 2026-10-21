"""Hidden tests for the c_paths change (path queries). Never shown to the
writer or the editor.

Usage (with rovers.py importable, e.g. in the sandbox):
    python -m pytest changes/c_paths/private/test_paths_new.py
"""

import pytest
from rovers import RoverFleet


@pytest.fixture
def fleet():
    f = RoverFleet(width=6, height=5)
    f.land("scout", 1, 1, "east")
    f.land("mole", 4, 3, "west")
    return f


def test_path_starts_at_the_landing_cell(fleet):
    assert fleet.get_path("mole") == [(4, 3)]
    assert fleet.get_explored("mole") == 1


def test_path_ignores_turns(fleet):
    fleet.drive("scout", "LRLR")
    assert fleet.get_path("scout") == [(1, 1)]


def test_path_repeats_cells_on_return(fleet):
    fleet.drive("scout", "FBFB")
    assert fleet.get_path("scout") == [(1, 1), (2, 1), (1, 1), (2, 1), (1, 1)]
    assert fleet.get_explored("scout") == 2
    assert fleet.get_odometer("scout") == 4


def test_path_follows_wrapping(fleet):
    fleet.drive("mole", "FFFFF")
    assert fleet.get_path("mole") == [(4, 3), (3, 3), (2, 3), (1, 3), (0, 3), (5, 3)]
    assert fleet.get_explored("mole") == 6


def test_path_leaves_out_blocked_moves(fleet):
    fleet.add_obstacle(3, 1)
    fleet.drive("scout", "FFF")
    fleet.drive("mole", "LF")  # (4, 2)
    fleet.drive("scout", "LFRFF")  # (2, 2), then (3, 2), then mole blocks
    assert fleet.get_path("scout") == [(1, 1), (2, 1), (2, 2), (3, 2)]
    assert fleet.get_path("mole") == [(4, 3), (4, 2)]


def test_path_is_kept_per_rover(fleet):
    fleet.drive("scout", "F")
    fleet.drive("mole", "F")
    fleet.drive("scout", "F")
    assert fleet.get_path("scout") == [(1, 1), (2, 1), (3, 1)]
    assert fleet.get_path("mole") == [(4, 3), (3, 3)]


def test_path_visitors_are_listed_once_in_landing_order(fleet):
    fleet.land("digger", 0, 0, "north")
    fleet.drive("digger", "FRFF")  # (0, 1), (1, 1) is taken by scout
    fleet.drive("scout", "LF")  # leaves (1, 1) for (1, 2)
    fleet.drive("digger", "F")  # now on (1, 1)
    fleet.drive("digger", "BF")
    fleet.drive("mole", "LLFF")  # (5, 3), then (0, 3)
    assert fleet.get_visitors(1, 1) == ["scout", "digger"]
    assert fleet.get_visitors(0, 3) == ["mole"]
    assert fleet.get_visitors(4, 3) == ["mole"]


def test_path_visitors_include_rovers_that_left(fleet):
    fleet.drive("mole", "FFF")
    fleet.land("digger", 4, 3, "north")
    assert fleet.get_visitors(4, 3) == ["mole", "digger"]
    assert fleet.get_visitors(2, 3) == ["mole"]
    assert fleet.get_visitors(1, 3) == ["mole"]


@pytest.mark.parametrize("cell", [(6, 0), (0, 5), (-1, 0), (0, 1.0), ("1", 1)])
def test_path_visitors_reject_cells_off_the_plateau(fleet, cell):
    with pytest.raises(ValueError):
        fleet.get_visitors(*cell)


def test_path_queries_raise_key_error_for_unknown_rovers(fleet):
    for call in (
        lambda: fleet.get_path("digger"),
        lambda: fleet.get_explored("digger"),
        lambda: fleet.get_path(None),
        lambda: fleet.get_explored(1),
    ):
        with pytest.raises(KeyError):
            call()
