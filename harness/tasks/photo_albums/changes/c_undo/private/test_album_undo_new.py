"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with albums.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_album_undo_new.py
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
    return [(album, lib.get_photos(album)) for album in lib.get_albums()]


# --- each call can be undone ------------------------------------------------


def test_undo_of_add_photo_frees_the_name(library):
    before = state(library)
    library.add_photo("Garden", "tree.jpg")
    library.undo()
    assert state(library) == before
    library.add_photo("Family", "tree.jpg")
    assert library.get_photos("Family") == ["cake.jpg", "dog.jpg", "tree.jpg"]


@pytest.mark.parametrize("photo", ["beach.jpg", "boat.jpg", "sunset.jpg"])
def test_undo_of_move_photo_puts_it_back_in_its_place(library, photo):
    before = state(library)
    library.move_photo(photo, "Family")
    library.undo()
    assert state(library) == before
    assert library.get_photos("Holiday") == ["beach.jpg", "boat.jpg", "sunset.jpg"]
    assert library.get_photos("Family") == ["cake.jpg", "dog.jpg"]


@pytest.mark.parametrize("photo", ["beach.jpg", "boat.jpg", "sunset.jpg"])
def test_undo_of_remove_photo_puts_it_back_in_its_place(library, photo):
    before = state(library)
    library.remove_photo(photo)
    library.undo()
    assert state(library) == before
    with pytest.raises(AlbumError):
        library.add_photo("Garden", photo)


def test_undo_of_merge_albums_brings_the_source_back_in_its_place(library):
    before = state(library)
    assert library.merge_albums("Holiday", "Garden") == 3
    library.undo()
    assert state(library) == before
    assert library.get_albums() == ["Unsorted", "Holiday", "Family", "Garden"]
    assert library.get_photos("Garden") == []


def test_undo_of_merge_albums_into_an_album_with_photos(library):
    before = state(library)
    library.merge_albums("Family", "Holiday")
    assert library.get_photos("Holiday") == ["beach.jpg", "boat.jpg", "sunset.jpg", "cake.jpg", "dog.jpg"]
    library.undo()
    assert state(library) == before


def test_undo_of_delete_album_brings_it_back_and_empties_unsorted_again(library):
    before = state(library)
    assert library.delete_album("Holiday") == 3
    library.undo()
    assert state(library) == before
    assert library.get_photos("Unsorted") == ["scan.jpg"]
    assert library.get_albums() == ["Unsorted", "Holiday", "Family", "Garden"]


def test_an_album_brought_back_is_in_use_again(library):
    library.delete_album("Family")
    library.undo()
    library.add_photo("Family", "kite.jpg")
    assert library.get_photos("Family") == ["cake.jpg", "dog.jpg", "kite.jpg"]
    with pytest.raises(AlbumError):
        library.create_album("Family")
    library.move_photo("cake.jpg", "Garden")
    assert library.get_photos("Garden") == ["cake.jpg"]
    assert library.merge_albums("Family", "Holiday") == 2


def test_undo_of_create_album_removes_it_and_frees_the_name(library):
    library.create_album("Work")
    library.undo()
    assert library.get_albums() == ["Unsorted", "Holiday", "Family", "Garden"]
    with pytest.raises(KeyError):
        library.get_photos("Work")
    library.create_album("Work")
    assert library.get_albums() == ["Unsorted", "Holiday", "Family", "Garden", "Work"]
    assert library.get_photos("Work") == []


def test_undo_of_a_photo_moved_twice(library):
    library.move_photo("boat.jpg", "Garden")
    library.move_photo("boat.jpg", "Family")
    library.undo()
    assert library.get_photos("Garden") == ["boat.jpg"]
    assert library.get_photos("Family") == ["cake.jpg", "dog.jpg"]
    library.undo()
    assert library.get_photos("Holiday") == ["beach.jpg", "boat.jpg", "sunset.jpg"]
    assert library.get_photos("Garden") == []


# --- what is and is not recorded --------------------------------------------


def test_each_undo_goes_one_call_further_back():
    lib = PhotoLibrary()
    calls = [
        lambda: lib.create_album("Holiday"),
        lambda: lib.create_album("Family"),
        lambda: lib.add_photo("Holiday", "beach.jpg"),
        lambda: lib.add_photo("Holiday", "boat.jpg"),
        lambda: lib.add_photo("Holiday", "sunset.jpg"),
        lambda: lib.add_photo("Family", "cake.jpg"),
        lambda: lib.add_photo("Unsorted", "scan.jpg"),
        lambda: lib.create_album("Garden"),
        lambda: lib.move_photo("boat.jpg", "Garden"),
        lambda: lib.move_photo("scan.jpg", "Family"),
        lambda: lib.remove_photo("beach.jpg"),
        lambda: lib.merge_albums("Garden", "Holiday"),
        lambda: lib.add_photo("Family", "dog.jpg"),
        lambda: lib.delete_album("Family"),
        lambda: lib.move_photo("sunset.jpg", "Unsorted"),
        lambda: lib.delete_album("Holiday"),
    ]
    states = [state(lib)]
    for call in calls:
        call()
        states.append(state(lib))
    assert lib.get_albums() == ["Unsorted"]
    assert lib.get_photos("Unsorted") == ["cake.jpg", "scan.jpg", "dog.jpg", "sunset.jpg", "boat.jpg"]
    for expected in reversed(states[:-1]):
        lib.undo()
        assert state(lib) == expected
    with pytest.raises(AlbumError):
        lib.undo()
    assert lib.get_albums() == ["Unsorted"]
    assert lib.get_photos("Unsorted") == []


def test_failed_calls_are_not_recorded(library):
    library.add_photo("Garden", "tree.jpg")
    for call in (
        lambda: library.create_album("Holiday"),
        lambda: library.add_photo("Family", "beach.jpg"),
        lambda: library.add_photo("Work", "desk.jpg"),
        lambda: library.move_photo("boat.jpg", "Holiday"),
        lambda: library.move_photo("kite.jpg", "Holiday"),
        lambda: library.remove_photo("kite.jpg"),
        lambda: library.merge_albums("Holiday", "Holiday"),
        lambda: library.merge_albums("Unsorted", "Family"),
        lambda: library.delete_album("Unsorted"),
        lambda: library.delete_album("Work"),
    ):
        with pytest.raises((KeyError, ValueError, AlbumError)):
            call()
    library.undo()  # the add_photo of tree.jpg
    assert library.get_photos("Garden") == []
    assert library.get_photos("Holiday") == ["beach.jpg", "boat.jpg", "sunset.jpg"]


def test_get_calls_are_not_recorded(library):
    library.add_photo("Garden", "tree.jpg")
    library.get_photos("Garden")
    library.get_albums()
    library.undo()
    assert library.get_photos("Garden") == []
    assert library.get_photos("Unsorted") == ["scan.jpg"]


def test_there_is_no_redo():
    lib = PhotoLibrary()
    lib.create_album("Holiday")
    lib.add_photo("Holiday", "beach.jpg")
    lib.undo()
    lib.undo()
    assert lib.get_albums() == ["Unsorted"]
    with pytest.raises(AlbumError):
        lib.undo()


def test_new_calls_after_an_undo_are_undone_first(library):
    library.add_photo("Garden", "tree.jpg")
    library.undo()
    library.add_photo("Garden", "kite.jpg")
    library.undo()
    assert library.get_photos("Garden") == []
    library.undo()  # the add_photo of scan.jpg in the fixture
    assert library.get_photos("Unsorted") == []
    assert library.get_photos("Family") == ["cake.jpg", "dog.jpg"]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    lib = PhotoLibrary()
    with pytest.raises(AlbumError):
        lib.undo()
    lib.create_album("Holiday")
    lib.undo()
    with pytest.raises(AlbumError):
        lib.undo()
    assert lib.get_albums() == ["Unsorted"]
    lib.add_photo("Unsorted", "scan.jpg")
    assert lib.get_photos("Unsorted") == ["scan.jpg"]


def test_the_whole_fixture_can_be_undone(library):
    for _ in range(9):
        library.undo()
    assert library.get_albums() == ["Unsorted"]
    assert library.get_photos("Unsorted") == []
    with pytest.raises(AlbumError):
        library.undo()


def test_undo_restores_photos_that_a_later_call_checks(library):
    library.delete_album("Holiday")
    library.undo()
    with pytest.raises(ValueError):
        library.move_photo("boat.jpg", "Holiday")
    library.move_photo("boat.jpg", "Unsorted")
    assert library.get_photos("Unsorted") == ["scan.jpg", "boat.jpg"]
    assert library.get_photos("Holiday") == ["beach.jpg", "sunset.jpg"]
