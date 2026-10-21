"""Public checks for the c_grid_size change (adjustable plateau). Shown to
the editor, never to the writer.

Usage (with rovers.py importable, e.g. in the sandbox):
    python -m pytest changes/c_grid_size/public/test_grid_size_public.py
"""

import pytest
from rovers import RoverFleet


def test_plateau_of_another_size_wraps_at_its_own_edge():
    f = RoverFleet(width=5, height=3)
    assert f.get_plateau() == (5, 3)
    f.land("scout", 4, 2, "east")
    f.drive("scout", "FLF")
    assert f.get_location("scout") == (0, 0, "north")
    with pytest.raises(ValueError):
        f.land("mole", 5, 0, "north")


def test_plateau_without_wrapping_stops_at_the_edge():
    f = RoverFleet(wrap=False)
    f.land("scout", 8, 0, "east")
    assert f.drive("scout", "FFL") == 1
    assert f.get_location("scout") == (9, 0, "east")
