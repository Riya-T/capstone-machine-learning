"""Public checks for the c_move_many change (moving several photos at once).
Shown to the editor, never to the writer.

Usage (with albums.py importable, e.g. in the sandbox):
    python -m pytest changes/c_move_many/public/test_move_many_public.py
"""

import pytest
from albums import PhotoLibrary


@pytest.fixture
def library():
    lib = PhotoLibrary()
    lib.create_album("Holiday")
    lib.create_album("Family")
    for photo in ["beach.jpg", "boat.jpg", "sunset.jpg"]:
        lib.add_photo("Holiday", photo)
    lib.add_photo("Unsorted", "cake.jpg")
    return lib


def test_move_photos_moves_them_in_the_order_given(library):
    library.move_photos(["sunset.jpg", "cake.jpg", "beach.jpg"], "Family")
    assert library.get_photos("Family") == ["sunset.jpg", "cake.jpg", "beach.jpg"]
    assert library.get_photos("Holiday") == ["boat.jpg"]
    assert library.get_photos("Unsorted") == []


def test_one_bad_photo_moves_nothing(library):
    with pytest.raises(KeyError):
        library.move_photos(["beach.jpg", "kite.jpg"], "Family")
    assert library.get_photos("Holiday") == ["beach.jpg", "boat.jpg", "sunset.jpg"]
    assert library.get_photos("Family") == []
