"""Public checks for the c_obstacles change (obstacles). Shown to the
editor, never to the writer.

Usage (with rovers.py importable, e.g. in the sandbox):
    python -m pytest changes/c_obstacles/public/test_obstacles_public.py
"""

import pytest
from rovers import RoverError, RoverFleet


def test_obstacle_blocks_a_move():
    f = RoverFleet()
    f.land("scout", 1, 1, "east")
    f.add_obstacle(3, 1)
    assert f.drive("scout", "FFF") == 1
    assert f.get_location("scout") == (2, 1, "east")
    assert f.get_obstacles() == [(3, 1)]


def test_obstacle_cannot_be_landed_on():
    f = RoverFleet()
    f.add_obstacle(4, 4)
    with pytest.raises(RoverError):
        f.land("scout", 4, 4, "north")
    assert f.get_rovers() == []
