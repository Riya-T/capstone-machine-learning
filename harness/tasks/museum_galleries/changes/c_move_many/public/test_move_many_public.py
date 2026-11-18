"""Public checks for the c_move_many change (several moves as one call).
Shown to the editor, never to the writer.

Usage (with museum.py importable, e.g. in the sandbox):
    python -m pytest changes/c_move_many/public/test_move_many_public.py
"""

import pytest
from museum import Museum


@pytest.fixture
def museum():
    m = Museum()
    m.add_gallery("east")
    m.add_gallery("west")
    m.hang("lilies", "east")
    m.hang("harbor", "east")
    m.hang("storm", "west")
    return m


def test_moves_are_applied_in_order(museum):
    museum.move_many([("harbor", "west"), ("storm", "east")])
    assert museum.get_artworks("east") == ["lilies", "storm"]
    assert museum.get_artworks("west") == ["harbor"]


def test_a_failing_move_changes_nothing(museum):
    with pytest.raises(KeyError):
        museum.move_many([("harbor", "west"), ("lilies", "south")])
    assert museum.get_artworks("east") == ["lilies", "harbor"]
    assert museum.get_artworks("west") == ["storm"]
