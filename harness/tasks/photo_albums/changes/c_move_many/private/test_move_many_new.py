"""Hidden tests for the c_move_many change (moving several photos at once).
Never shown to the writer or the editor.

Usage (with albums.py importable, e.g. in the sandbox):
    python -m pytest changes/c_move_many/private/test_move_many_new.py
"""

import pytest
from albums import AlbumError, PhotoLibrary


@pytest.fixture
def library():
    lib = PhotoLibrary()
    for name in ["Holiday", "Family", "Garden"]:
        lib.create_album(name)
    for photo in ["beach.jpg", "boat.jpg", "sunset.jpg", "pier.jpg"]:
        lib.add_photo("Holiday", photo)
    for photo in ["cake.jpg", "dog.jpg"]:
        lib.add_photo("Family", photo)
    lib.add_photo("Unsorted", "scan.jpg")
    return lib


def state(lib):
    return [(album, lib.get_photos(album)) for album in lib.get_albums()]


# --- moving -------------------------------------------------------------------


def test_photos_are_added_in_the_order_of_the_list(library):
    library.move_photos(["pier.jpg", "beach.jpg"], "Garden")
    assert library.get_photos("Garden") == ["pier.jpg", "beach.jpg"]
    assert library.get_photos("Holiday") == ["boat.jpg", "sunset.jpg"]


def test_photos_go_after_the_ones_already_there(library):
    library.move_photos(["boat.jpg", "sunset.jpg"], "Family")
    assert library.get_photos("Family") == ["cake.jpg", "dog.jpg", "boat.jpg", "sunset.jpg"]
    assert library.get_photos("Holiday") == ["beach.jpg", "pier.jpg"]


def test_photos_can_come_from_several_albums(library):
    library.move_photos(["dog.jpg", "scan.jpg", "boat.jpg"], "Garden")
    assert state(library) == [
        ("Unsorted", []),
        ("Holiday", ["beach.jpg", "sunset.jpg", "pier.jpg"]),
        ("Family", ["cake.jpg"]),
        ("Garden", ["dog.jpg", "scan.jpg", "boat.jpg"]),
    ]


def test_photos_can_move_into_unsorted(library):
    library.move_photos(["cake.jpg", "beach.jpg"], "Unsorted")
    assert library.get_photos("Unsorted") == ["scan.jpg", "cake.jpg", "beach.jpg"]
    assert library.get_photos("Family") == ["dog.jpg"]


def test_moving_every_photo_of_an_album_leaves_it_empty_but_in_use(library):
    library.move_photos(["dog.jpg", "cake.jpg"], "Holiday")
    assert library.get_albums() == ["Unsorted", "Holiday", "Family", "Garden"]
    assert library.get_photos("Family") == []
    assert library.get_photos("Holiday") == [
        "beach.jpg", "boat.jpg", "sunset.jpg", "pier.jpg", "dog.jpg", "cake.jpg",
    ]  # fmt: skip


def test_a_list_of_one_photo_works_like_move_photo(library):
    library.move_photos(["boat.jpg"], "Garden")
    assert library.get_photos("Garden") == ["boat.jpg"]
    assert library.get_photos("Holiday") == ["beach.jpg", "sunset.jpg", "pier.jpg"]


def test_moved_photos_are_still_in_the_library(library):
    library.move_photos(["beach.jpg", "cake.jpg"], "Garden")
    with pytest.raises(AlbumError):
        library.add_photo("Holiday", "beach.jpg")
    library.move_photo("beach.jpg", "Family")
    library.remove_photo("cake.jpg")
    assert library.get_photos("Garden") == []
    assert library.get_photos("Family") == ["dog.jpg", "beach.jpg"]


def test_photos_can_be_moved_back_together(library):
    library.move_photos(["beach.jpg", "boat.jpg"], "Garden")
    library.move_photos(["boat.jpg", "beach.jpg"], "Holiday")
    assert library.get_photos("Holiday") == ["sunset.jpg", "pier.jpg", "boat.jpg", "beach.jpg"]
    assert library.get_photos("Garden") == []


# --- all or nothing -------------------------------------------------------------


@pytest.mark.parametrize(
    "photos",
    [
        ["kite.jpg", "beach.jpg"],
        ["beach.jpg", "kite.jpg"],
        ["beach.jpg", "cake.jpg", "kite.jpg"],
    ],
)
def test_a_photo_not_in_the_library_moves_nothing(library, photos):
    before = state(library)
    with pytest.raises(KeyError):
        library.move_photos(photos, "Garden")
    assert state(library) == before


def test_an_album_not_in_use_moves_nothing(library):
    before = state(library)
    with pytest.raises(KeyError):
        library.move_photos(["beach.jpg", "cake.jpg"], "Work")
    assert state(library) == before
    library.delete_album("Garden")
    before = state(library)
    with pytest.raises(KeyError):
        library.move_photos(["beach.jpg"], "Garden")
    assert state(library) == before


@pytest.mark.parametrize(
    "photos",
    [
        ["cake.jpg", "beach.jpg"],
        ["beach.jpg", "boat.jpg", "dog.jpg"],
    ],
)
def test_a_photo_already_in_the_album_moves_nothing(library, photos):
    before = state(library)
    with pytest.raises(ValueError):
        library.move_photos(photos, "Family")
    assert state(library) == before


def test_a_photo_named_twice_moves_nothing(library):
    before = state(library)
    with pytest.raises(ValueError):
        library.move_photos(["beach.jpg", "cake.jpg", "beach.jpg"], "Garden")
    assert state(library) == before


def test_a_refused_call_can_be_retried_without_the_bad_photo(library):
    with pytest.raises(KeyError):
        library.move_photos(["boat.jpg", "kite.jpg", "scan.jpg"], "Garden")
    library.move_photos(["boat.jpg", "scan.jpg"], "Garden")
    assert library.get_photos("Garden") == ["boat.jpg", "scan.jpg"]
    assert library.get_photos("Unsorted") == []
