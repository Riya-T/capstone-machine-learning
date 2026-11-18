"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with museum.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from museum import Museum, MuseumError


@pytest.fixture
def museum():
    m = Museum()
    m.add_gallery("east")
    m.add_gallery("west")
    return m


def test_undo_takes_back_the_last_hang(museum):
    museum.hang("lilies", "east")
    museum.hang("harbor", "east")
    museum.undo()
    assert museum.get_artworks("east") == ["lilies"]
    museum.undo()
    assert museum.get_artworks("east") == []


def test_undo_takes_back_a_move(museum):
    museum.hang("lilies", "east")
    museum.hang("harbor", "east")
    museum.move_artwork("lilies", "west")
    museum.undo()
    assert museum.get_artworks("east") == ["lilies", "harbor"]
    assert museum.get_artworks("west") == []


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(MuseumError):
        Museum().undo()
