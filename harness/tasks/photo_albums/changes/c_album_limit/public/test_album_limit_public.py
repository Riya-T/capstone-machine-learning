"""Public checks for the c_album_limit change (at most 5 photos per album).
Shown to the editor, never to the writer.

Usage (with albums.py importable, e.g. in the sandbox):
    python -m pytest changes/c_album_limit/public/test_album_limit_public.py
"""

import pytest
from albums import AlbumFull, PhotoLibrary

FIVE = ["1.jpg", "2.jpg", "3.jpg", "4.jpg", "5.jpg"]


@pytest.fixture
def library():
    lib = PhotoLibrary()
    lib.create_album("Holiday")
    lib.create_album("Family")
    return lib


def test_a_sixth_photo_is_refused(library):
    for photo in FIVE:
        library.add_photo("Holiday", photo)
    with pytest.raises(AlbumFull):
        library.add_photo("Holiday", "6.jpg")
    assert library.get_photos("Holiday") == FIVE


def test_unsorted_has_no_limit(library):
    for photo in FIVE + ["6.jpg", "7.jpg"]:
        library.add_photo("Unsorted", photo)
    assert len(library.get_photos("Unsorted")) == 7
