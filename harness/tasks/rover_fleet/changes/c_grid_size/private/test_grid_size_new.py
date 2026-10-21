"""Hidden tests for the c_grid_size change (adjustable plateau). Never shown
to the writer or the editor.

Usage (with rovers.py importable, e.g. in the sandbox):
    python -m pytest changes/c_grid_size/private/test_grid_size_new.py
"""

import pytest
from rovers import RoverError, RoverFleet

BAD_SIZES = [0, -3, 2.0, "10", None, True]
BAD_WRAPS = ["yes", "no", [], 2.5]


def test_plateau_defaults_to_ten_by_ten_and_wraps():
    f = RoverFleet()
    assert f.get_plateau() == (10, 10)
    f.land("scout", 9, 9, "north")
    f.drive("scout", "FRF")
    assert f.get_location("scout") == (0, 0, "east")


def test_plateau_cells_follow_width_and_height():
    f = RoverFleet(width=12, height=4)
    f.land("scout", 11, 3, "north")
    assert f.get_rover_at(11, 3) == "scout"
    for x, y in [(12, 0), (0, 4), (-1, 0)]:
        with pytest.raises(ValueError):
            f.land("mole", x, y, "north")
        with pytest.raises(ValueError):
            f.get_rover_at(x, y)
    assert f.get_rovers() == ["scout"]


def test_plateau_wraps_at_every_edge_of_its_size():
    f = RoverFleet(width=6, height=4)
    f.land("scout", 5, 0, "east")
    f.drive("scout", "F")
    assert f.get_location("scout")[:2] == (0, 0)
    f.drive("scout", "B")
    assert f.get_location("scout")[:2] == (5, 0)
    f.drive("scout", "RF")
    assert f.get_location("scout")[:2] == (5, 3)
    f.drive("scout", "B")
    assert f.get_location("scout")[:2] == (5, 0)
    assert f.get_odometer("scout") == 4


def test_plateau_cliffs_block_at_every_edge():
    f = RoverFleet(width=3, height=3, wrap=False)
    f.land("scout", 0, 0, "south")
    assert f.drive("scout", "F") == 0
    assert f.drive("scout", "RF") == 1  # turned west, then blocked
    assert f.drive("scout", "B") == 1
    assert f.drive("scout", "BB") == 1  # x = 2 is the last column
    assert f.get_location("scout") == (2, 0, "west")
    assert f.drive("scout", "RFFF") == 3
    assert f.get_location("scout") == (2, 2, "north")
    assert f.get_odometer("scout") == 4


def test_plateau_cliff_stops_the_rest_of_the_string():
    f = RoverFleet(wrap=False)
    f.land("scout", 0, 8, "north")
    assert f.drive("scout", "FFRF") == 1
    assert f.get_location("scout") == (0, 9, "north")


def test_plateau_wrap_can_be_set_per_rover():
    f = RoverFleet(width=4, height=4, wrap=False)
    f.land("glider", 3, 1, "east", wrap=True)
    f.land("crawler", 3, 2, "east")
    f.land("tank", 3, 3, "east", wrap=False)
    assert [f.drive(r, "F") for r in ["glider", "crawler", "tank"]] == [1, 0, 0]
    assert f.get_location("glider") == (0, 1, "east")

    g = RoverFleet(width=4, height=4)
    g.land("crawler", 3, 1, "east", wrap=False)
    g.land("glider", 3, 2, "east")
    assert [g.drive(r, "F") for r in ["crawler", "glider"]] == [0, 1]


def test_plateau_wrapping_onto_a_rover_is_still_blocked():
    f = RoverFleet(width=4, height=2)
    f.land("scout", 3, 1, "east")
    f.land("mole", 0, 1, "west")
    assert f.drive("scout", "F") == 0
    assert f.drive("mole", "F") == 0


@pytest.mark.parametrize("size", BAD_SIZES)
def test_plateau_size_must_be_a_positive_int(size):
    with pytest.raises(ValueError):
        RoverFleet(width=size)
    with pytest.raises(ValueError):
        RoverFleet(height=size)


@pytest.mark.parametrize("wrap", BAD_WRAPS)
def test_plateau_wrap_must_be_a_bool(wrap):
    with pytest.raises(ValueError):
        RoverFleet(wrap=wrap)
    f = RoverFleet()
    with pytest.raises(ValueError):
        f.land("scout", 0, 0, "north", wrap=wrap)
    assert f.get_rovers() == []


def test_plateau_wrap_error_comes_in_the_order():
    f = RoverFleet()
    f.land("scout", 0, 0, "north")
    with pytest.raises(RoverError):
        f.land("scout", 1, 1, "north", wrap="yes")
    with pytest.raises(ValueError):
        f.land("mole", 0, 0, "north", wrap="yes")
    assert f.get_rovers() == ["scout"]
