"""Hidden tests for the c_album_limit change (at most 5 photos per album).
Never shown to the writer or the editor.

Usage (with albums.py importable, e.g. in the sandbox):
    python -m pytest changes/c_album_limit/private/test_album_limit_new.py
"""

import pytest
from albums import AlbumError, AlbumFull, PhotoLibrary


@pytest.fixture
def library():
    # Holiday is full, Family has 3 photos, Garden 2, Unsorted 1.
    lib = PhotoLibrary()
    for name in ["Holiday", "Family", "Garden"]:
        lib.create_album(name)
    for photo in ["beach.jpg", "boat.jpg", "sunset.jpg", "pier.jpg", "shell.jpg"]:
        lib.add_photo("Holiday", photo)
    for photo in ["cake.jpg", "dog.jpg", "kite.jpg"]:
        lib.add_photo("Family", photo)
    for photo in ["tree.jpg", "rose.jpg"]:
        lib.add_photo("Garden", photo)
    lib.add_photo("Unsorted", "scan.jpg")
    return lib


def state(lib):
    return [(album, lib.get_photos(album)) for album in lib.get_albums()]


# --- add_photo and move_photo ---------------------------------------------------


def test_five_photos_fit_in_an_album():
    lib = PhotoLibrary()
    lib.create_album("Holiday")
    for photo in ["1.jpg", "2.jpg", "3.jpg", "4.jpg", "5.jpg"]:
        lib.add_photo("Holiday", photo)
    assert lib.get_photos("Holiday") == ["1.jpg", "2.jpg", "3.jpg", "4.jpg", "5.jpg"]


def test_add_photo_to_a_full_album_changes_nothing(library):
    before = state(library)
    with pytest.raises(AlbumFull):
        library.add_photo("Holiday", "wave.jpg")
    assert state(library) == before
    library.add_photo("Garden", "wave.jpg")  # the name was not taken
    assert library.get_photos("Garden") == ["tree.jpg", "rose.jpg", "wave.jpg"]


def test_album_full_is_an_album_error():
    assert issubclass(AlbumFull, AlbumError)


def test_move_photo_into_a_full_album_changes_nothing(library):
    before = state(library)
    with pytest.raises(AlbumFull):
        library.move_photo("cake.jpg", "Holiday")
    with pytest.raises(AlbumFull):
        library.move_photo("scan.jpg", "Holiday")
    assert state(library) == before


def test_move_photo_until_an_album_is_full(library):
    library.move_photo("tree.jpg", "Family")
    library.move_photo("rose.jpg", "Family")
    assert library.get_photos("Family") == ["cake.jpg", "dog.jpg", "kite.jpg", "tree.jpg", "rose.jpg"]
    with pytest.raises(AlbumFull):
        library.move_photo("scan.jpg", "Family")


def test_a_full_album_has_room_after_a_photo_moves_out(library):
    library.move_photo("boat.jpg", "Garden")
    library.move_photo("cake.jpg", "Holiday")
    assert library.get_photos("Holiday") == ["beach.jpg", "sunset.jpg", "pier.jpg", "shell.jpg", "cake.jpg"]
    assert library.get_photos("Garden") == ["tree.jpg", "rose.jpg", "boat.jpg"]


def test_a_full_album_has_room_after_remove_photo(library):
    library.remove_photo("pier.jpg")
    library.add_photo("Holiday", "wave.jpg")
    assert library.get_photos("Holiday") == ["beach.jpg", "boat.jpg", "sunset.jpg", "shell.jpg", "wave.jpg"]


def test_photos_can_always_leave_a_full_album(library):
    library.move_photo("beach.jpg", "Unsorted")
    library.remove_photo("boat.jpg")
    assert library.get_photos("Holiday") == ["sunset.jpg", "pier.jpg", "shell.jpg"]


# --- merge_albums and delete_album ----------------------------------------------


def test_a_merge_that_ends_at_exactly_five_photos_is_allowed(library):
    assert library.merge_albums("Garden", "Family") == 2
    assert library.get_photos("Family") == ["cake.jpg", "dog.jpg", "kite.jpg", "tree.jpg", "rose.jpg"]
    assert library.get_albums() == ["Unsorted", "Holiday", "Family"]


def test_a_merge_that_would_go_over_five_photos_changes_nothing(library):
    library.add_photo("Garden", "wave.jpg")
    before = state(library)
    with pytest.raises(AlbumFull):
        library.merge_albums("Garden", "Family")
    assert state(library) == before
    assert library.get_albums() == ["Unsorted", "Holiday", "Family", "Garden"]
    assert library.get_photos("Family") == ["cake.jpg", "dog.jpg", "kite.jpg"]


def test_a_merge_into_a_full_album_is_refused(library):
    library.create_album("Work")
    library.add_photo("Work", "desk.jpg")
    before = state(library)
    with pytest.raises(AlbumFull):
        library.merge_albums("Work", "Holiday")
    assert state(library) == before


def test_a_refused_merge_can_be_retried_once_there_is_room(library):
    library.add_photo("Garden", "wave.jpg")
    with pytest.raises(AlbumFull):
        library.merge_albums("Garden", "Family")
    library.remove_photo("kite.jpg")
    assert library.merge_albums("Garden", "Family") == 3
    assert library.get_photos("Family") == ["cake.jpg", "dog.jpg", "tree.jpg", "rose.jpg", "wave.jpg"]


def test_merging_into_unsorted_is_never_refused(library):
    assert library.merge_albums("Holiday", "Unsorted") == 5
    assert library.merge_albums("Family", "Unsorted") == 3
    assert len(library.get_photos("Unsorted")) == 9
    assert library.get_albums() == ["Unsorted", "Garden"]


def test_delete_album_is_never_refused(library):
    library.add_photo("Unsorted", "map.jpg")
    assert library.delete_album("Holiday") == 5
    assert library.delete_album("Family") == 3
    assert library.get_photos("Unsorted") == [
        "scan.jpg", "map.jpg",
        "beach.jpg", "boat.jpg", "sunset.jpg", "pier.jpg", "shell.jpg",
        "cake.jpg", "dog.jpg", "kite.jpg",
    ]  # fmt: skip


def test_the_merged_album_is_full_afterwards(library):
    library.merge_albums("Garden", "Family")
    with pytest.raises(AlbumFull):
        library.add_photo("Family", "wave.jpg")
    with pytest.raises(AlbumFull):
        library.move_photo("scan.jpg", "Family")
    assert library.get_photos("Unsorted") == ["scan.jpg"]
