"""Public checks for the c_locks change (locked galleries). Shown to the
editor, never to the writer.

Usage (with museum.py importable, e.g. in the sandbox):
    python -m pytest changes/c_locks/public/test_locks_public.py
"""

import pytest
from museum import GalleryLocked, Museum


@pytest.fixture
def museum():
    m = Museum()
    m.add_gallery("east")
    m.add_gallery("west")
    m.hang("lilies", "east")
    m.hang("storm", "west")
    return m


def test_galleries_start_unlocked_and_can_be_locked(museum):
    assert museum.is_locked("east") is False
    museum.lock_gallery("east")
    assert museum.is_locked("east") is True
    assert museum.is_locked("west") is False


def test_nothing_can_be_hung_in_a_locked_gallery(museum):
    museum.lock_gallery("east")
    with pytest.raises(GalleryLocked):
        museum.hang("harbor", "east")
    assert museum.get_artworks("east") == ["lilies"]


def test_unlocking_lifts_the_lock(museum):
    museum.lock_gallery("west")
    museum.unlock_gallery("west")
    museum.move_artwork("lilies", "west")
    assert museum.get_artworks("west") == ["storm", "lilies"]
