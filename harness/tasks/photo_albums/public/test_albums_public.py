"""Public checks for albums.py.

Usage (with albums.py importable, e.g. in the sandbox):
    python -m pytest public/test_albums_public.py
"""

import pytest
from albums import AlbumError, PhotoLibrary


@pytest.fixture
def library():
    lib = PhotoLibrary()
    lib.create_album("Holiday")
    lib.create_album("Family")
    return lib


def test_photos_and_albums_are_listed_in_the_order_added(library):
    library.add_photo("Holiday", "beach.jpg")
    library.add_photo("Holiday", "boat.jpg")
    library.add_photo("Holiday", "sunset.jpg")
    assert library.get_photos("Holiday") == ["beach.jpg", "boat.jpg", "sunset.jpg"]
    assert library.get_photos("Family") == []
    assert library.get_albums() == ["Unsorted", "Holiday", "Family"]


def test_a_photo_name_is_used_once_in_the_whole_library(library):
    library.add_photo("Holiday", "beach.jpg")
    with pytest.raises(AlbumError):
        library.add_photo("Family", "beach.jpg")
    assert library.get_photos("Family") == []


def test_move_photo_puts_it_at_the_end_of_the_other_album(library):
    for photo in ["beach.jpg", "boat.jpg", "sunset.jpg"]:
        library.add_photo("Holiday", photo)
    library.add_photo("Family", "cake.jpg")
    library.move_photo("boat.jpg", "Family")
    assert library.get_photos("Holiday") == ["beach.jpg", "sunset.jpg"]
    assert library.get_photos("Family") == ["cake.jpg", "boat.jpg"]
    with pytest.raises(ValueError):
        library.move_photo("cake.jpg", "Family")


def test_merge_albums_moves_every_photo_and_removes_the_source(library):
    library.add_photo("Holiday", "beach.jpg")
    library.add_photo("Holiday", "boat.jpg")
    library.add_photo("Family", "cake.jpg")
    assert library.merge_albums("Holiday", "Family") == 2
    assert library.get_photos("Family") == ["cake.jpg", "beach.jpg", "boat.jpg"]
    assert library.get_albums() == ["Unsorted", "Family"]
    with pytest.raises(KeyError):
        library.get_photos("Holiday")


def test_delete_album_puts_its_photos_in_unsorted(library):
    library.add_photo("Holiday", "beach.jpg")
    library.add_photo("Holiday", "boat.jpg")
    assert library.delete_album("Holiday") == 2
    assert library.get_photos("Unsorted") == ["beach.jpg", "boat.jpg"]
    assert library.get_albums() == ["Unsorted", "Family"]
    with pytest.raises(AlbumError):
        library.delete_album("Unsorted")
