"""Hidden tests for the initial photo_albums spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with albums.py importable, e.g. in the sandbox):
    python -m pytest private/test_albums_initial.py
"""

import pytest
from albums import AlbumError, PhotoLibrary


@pytest.fixture
def library():
    lib = PhotoLibrary()
    for name in ["Holiday", "Family", "Garden"]:
        lib.create_album(name)
    for photo in ["beach.jpg", "boat.jpg", "sunset.jpg"]:
        lib.add_photo("Holiday", photo)
    for photo in ["cake.jpg", "dog.jpg"]:
        lib.add_photo("Family", photo)
    lib.add_photo("Unsorted", "scan.jpg")
    return lib


def state(lib):
    """Every album in order with its photos, to check that a failed call
    changed nothing."""
    return [(album, lib.get_photos(album)) for album in lib.get_albums()]


# --- albums -------------------------------------------------------------------


def test_a_new_library_has_only_an_empty_unsorted_album():
    lib = PhotoLibrary()
    assert lib.get_albums() == ["Unsorted"]
    assert lib.get_photos("Unsorted") == []


def test_albums_are_listed_in_the_order_created(library):
    assert library.get_albums() == ["Unsorted", "Holiday", "Family", "Garden"]
    assert library.get_photos("Garden") == []


@pytest.mark.parametrize("name", ["Holiday", "Unsorted"])
def test_creating_an_album_name_in_use_is_rejected(library, name):
    before = state(library)
    with pytest.raises(AlbumError):
        library.create_album(name)
    assert state(library) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda lib: lib.add_photo("Work", "desk.jpg"),
        lambda lib: lib.move_photo("beach.jpg", "Work"),
        lambda lib: lib.merge_albums("Work", "Holiday"),
        lambda lib: lib.merge_albums("Holiday", "Work"),
        lambda lib: lib.delete_album("Work"),
        lambda lib: lib.get_photos("Work"),
    ],
)
def test_albums_that_were_never_created_raise_key_error(library, call):
    before = state(library)
    with pytest.raises(KeyError):
        call(library)
    assert state(library) == before


def test_libraries_do_not_share_albums():
    first, second = PhotoLibrary(), PhotoLibrary()
    first.create_album("Holiday")
    first.add_photo("Unsorted", "scan.jpg")
    assert second.get_albums() == ["Unsorted"]
    assert second.get_photos("Unsorted") == []


# --- photos -------------------------------------------------------------------


def test_photos_are_kept_in_the_order_added(library):
    assert library.get_photos("Holiday") == ["beach.jpg", "boat.jpg", "sunset.jpg"]
    assert library.get_photos("Family") == ["cake.jpg", "dog.jpg"]
    assert library.get_photos("Unsorted") == ["scan.jpg"]


@pytest.mark.parametrize("album", ["Holiday", "Garden", "Unsorted"])
def test_a_photo_name_already_in_the_library_is_rejected(library, album):
    before = state(library)
    with pytest.raises(AlbumError):
        library.add_photo(album, "boat.jpg")
    assert state(library) == before


def test_move_photo_puts_it_at_the_end_of_the_other_album(library):
    library.move_photo("beach.jpg", "Family")
    assert library.get_photos("Holiday") == ["boat.jpg", "sunset.jpg"]
    assert library.get_photos("Family") == ["cake.jpg", "dog.jpg", "beach.jpg"]


def test_photos_can_move_into_and_out_of_unsorted(library):
    library.move_photo("scan.jpg", "Garden")
    library.move_photo("dog.jpg", "Unsorted")
    assert library.get_photos("Garden") == ["scan.jpg"]
    assert library.get_photos("Unsorted") == ["dog.jpg"]
    assert library.get_photos("Family") == ["cake.jpg"]


def test_a_moved_photo_is_still_in_the_library(library):
    library.move_photo("boat.jpg", "Garden")
    with pytest.raises(AlbumError):
        library.add_photo("Holiday", "boat.jpg")
    library.move_photo("boat.jpg", "Holiday")
    assert library.get_photos("Holiday") == ["beach.jpg", "sunset.jpg", "boat.jpg"]


def test_moving_a_photo_to_its_own_album_is_rejected(library):
    before = state(library)
    with pytest.raises(ValueError):
        library.move_photo("boat.jpg", "Holiday")
    assert state(library) == before


def test_remove_photo_keeps_the_order_of_the_others(library):
    library.remove_photo("boat.jpg")
    assert library.get_photos("Holiday") == ["beach.jpg", "sunset.jpg"]
    library.remove_photo("scan.jpg")
    assert library.get_photos("Unsorted") == []
    assert library.get_photos("Family") == ["cake.jpg", "dog.jpg"]


@pytest.mark.parametrize(
    "call",
    [
        lambda lib: lib.move_photo("tree.jpg", "Garden"),
        lambda lib: lib.remove_photo("tree.jpg"),
    ],
)
def test_photos_not_in_the_library_raise_key_error(library, call):
    before = state(library)
    with pytest.raises(KeyError):
        call(library)
    assert state(library) == before


# --- merging albums -------------------------------------------------------------


def test_merge_albums_moves_every_photo_in_order(library):
    assert library.merge_albums("Holiday", "Family") == 3
    assert library.get_photos("Family") == ["cake.jpg", "dog.jpg", "beach.jpg", "boat.jpg", "sunset.jpg"]
    assert library.get_albums() == ["Unsorted", "Family", "Garden"]


def test_merging_into_unsorted_and_into_an_empty_album(library):
    assert library.merge_albums("Family", "Unsorted") == 2
    assert library.get_photos("Unsorted") == ["scan.jpg", "cake.jpg", "dog.jpg"]
    assert library.merge_albums("Holiday", "Garden") == 3
    assert library.get_photos("Garden") == ["beach.jpg", "boat.jpg", "sunset.jpg"]
    assert library.get_albums() == ["Unsorted", "Garden"]


def test_merged_photos_are_still_in_the_library(library):
    library.merge_albums("Holiday", "Garden")
    library.move_photo("boat.jpg", "Family")
    assert library.get_photos("Garden") == ["beach.jpg", "sunset.jpg"]
    assert library.get_photos("Family") == ["cake.jpg", "dog.jpg", "boat.jpg"]


def test_merging_an_album_into_itself_is_rejected(library):
    before = state(library)
    with pytest.raises(ValueError):
        library.merge_albums("Holiday", "Holiday")
    assert state(library) == before


def test_unsorted_cannot_be_merged_away(library):
    before = state(library)
    with pytest.raises(AlbumError):
        library.merge_albums("Unsorted", "Holiday")
    assert state(library) == before


# --- deleting albums ------------------------------------------------------------


def test_delete_album_puts_its_photos_at_the_end_of_unsorted(library):
    assert library.delete_album("Holiday") == 3
    assert library.get_photos("Unsorted") == ["scan.jpg", "beach.jpg", "boat.jpg", "sunset.jpg"]
    assert library.get_albums() == ["Unsorted", "Family", "Garden"]
    assert library.get_photos("Family") == ["cake.jpg", "dog.jpg"]


def test_deleted_photos_can_still_be_moved(library):
    library.delete_album("Family")
    library.move_photo("cake.jpg", "Garden")
    assert library.get_photos("Unsorted") == ["scan.jpg", "dog.jpg"]
    assert library.get_photos("Garden") == ["cake.jpg"]


def test_unsorted_cannot_be_deleted(library):
    before = state(library)
    with pytest.raises(AlbumError):
        library.delete_album("Unsorted")
    assert state(library) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda lib: lib.add_photo("Holiday", "desk.jpg"),
        lambda lib: lib.move_photo("cake.jpg", "Holiday"),
        lambda lib: lib.merge_albums("Holiday", "Family"),
        lambda lib: lib.merge_albums("Family", "Holiday"),
        lambda lib: lib.delete_album("Holiday"),
        lambda lib: lib.get_photos("Holiday"),
    ],
    ids=["add_photo", "move_photo", "merge_from", "merge_into", "delete", "get_photos"],
)
@pytest.mark.parametrize("remove", ["merge", "delete"])
def test_a_merged_or_deleted_album_is_not_in_use(library, remove, call):
    if remove == "merge":
        library.merge_albums("Holiday", "Garden")
    else:
        library.delete_album("Holiday")
    before = state(library)
    with pytest.raises(KeyError):
        call(library)
    assert state(library) == before
