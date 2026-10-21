"""Public checks for the c_paths change (path queries). Shown to the
editor, never to the writer.

Usage (with rovers.py importable, e.g. in the sandbox):
    python -m pytest changes/c_paths/public/test_paths_public.py
"""

from rovers import RoverFleet


def test_path_lists_every_cell_stood_on():
    f = RoverFleet()
    f.land("scout", 1, 1, "north")
    f.drive("scout", "FRFB")
    assert f.get_path("scout") == [(1, 1), (1, 2), (2, 2), (1, 2)]
    assert f.get_explored("scout") == 3


def test_path_visitors_of_a_cell():
    f = RoverFleet()
    f.land("scout", 1, 1, "east")
    f.land("mole", 5, 5, "south")
    f.drive("scout", "FF")  # passes (2, 1)
    assert f.get_visitors(2, 1) == ["scout"]
    assert f.get_visitors(5, 5) == ["mole"]
    assert f.get_visitors(0, 0) == []
