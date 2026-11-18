"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with albums.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_album_undo_public.py
"""

import pytest
from albums import AlbumError, PhotoLibrary


@pytest.fixture
def library():
    lib = PhotoLibrary()
    lib.create_album("Holiday")
    lib.create_album("Family")
    return lib


def test_undo_takes_back_the_last_photo_added(library):
    library.add_photo("Holiday", "beach.jpg")
    library.add_photo("Holiday", "boat.jpg")
    library.undo()
    assert library.get_photos("Holiday") == ["beach.jpg"]
    library.undo()
    assert library.get_photos("Holiday") == []


def test_undo_takes_back_a_move(library):
    library.add_photo("Holiday", "beach.jpg")
    library.move_photo("beach.jpg", "Family")
    library.undo()
    assert library.get_photos("Holiday") == ["beach.jpg"]
    assert library.get_photos("Family") == []


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(AlbumError):
        PhotoLibrary().undo()
