"""Hidden tests for the c_remove change (removing songs). Never shown to the
writer or the editor.

Usage (with playlist.py importable, e.g. in the sandbox):
    python -m pytest changes/c_remove/private/test_remove_new.py
"""

import pytest
from playlist import LibraryError, MusicLibrary

PLAYLISTS = ["morning", "late"]


@pytest.fixture
def library():
    lib = MusicLibrary()
    lib.add_song("Blue", "Nina", 200)
    lib.add_song("Red", "Nina", 180)
    lib.add_song("Gold", "Omar", 240)
    for name in PLAYLISTS:
        lib.create_playlist(name)
    for title in ["Blue", "Red", "Gold"]:
        lib.add_to_playlist("morning", title)
    lib.add_to_playlist("late", "Red")
    return lib


def state(lib):
    return ({n: lib.get_playlist(n) for n in PLAYLISTS}, lib.get_queue())


def test_taking_a_song_out_of_a_playlist_leaves_other_playlists_alone(library):
    library.enqueue("Red")
    library.remove_from_playlist("morning", "Red")
    assert library.get_playlist("morning") == ["Blue", "Gold"]
    assert library.get_playlist("late") == ["Red"]
    assert library.get_queue() == ["Red"]


def test_a_song_taken_out_can_be_put_back_at_the_end(library):
    library.remove_from_playlist("morning", "Blue")
    library.add_to_playlist("morning", "Blue")
    assert library.get_playlist("morning") == ["Red", "Gold", "Blue"]


def test_taking_out_a_song_that_is_not_in_the_playlist_is_refused(library):
    before = state(library)
    with pytest.raises(LibraryError):
        library.remove_from_playlist("late", "Blue")
    assert state(library) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda lib: lib.remove_from_playlist("evening", "Blue"),
        lambda lib: lib.remove_from_playlist(None, "Blue"),
        lambda lib: lib.remove_from_playlist("morning", "Green"),
        lambda lib: lib.remove_from_playlist("morning", None),
        lambda lib: lib.remove_song("Green"),
        lambda lib: lib.remove_song(None),
        lambda lib: lib.remove_song(2),
    ],
)
def test_removing_with_unknown_names_raises_key_error_and_changes_nothing(library, call):
    before = state(library)
    with pytest.raises(KeyError):
        call(library)
    assert state(library) == before


def test_an_unknown_playlist_wins_over_an_unknown_song_when_taking_out(library):
    # Both would be KeyError; a missing song in a known playlist is LibraryError,
    # so a missing playlist must be reported before the playlist check.
    with pytest.raises(KeyError):
        library.remove_from_playlist("evening", "Green")
    with pytest.raises(KeyError):
        library.remove_from_playlist("late", "Green")


def test_removing_a_song_drops_every_queued_copy_in_order(library):
    for title in ["Blue", "Red", "Blue", "Gold", "Blue"]:
        library.enqueue(title)
    library.remove_song("Blue")
    assert library.get_queue() == ["Red", "Gold"]
    assert library.play_next() == "Red"


def test_removing_a_song_takes_it_out_of_every_playlist(library):
    library.remove_song("Red")
    assert library.get_playlist("morning") == ["Blue", "Gold"]
    assert library.get_playlist("late") == []


@pytest.mark.parametrize(
    "call",
    [
        lambda lib: lib.enqueue("Red"),
        lambda lib: lib.add_to_playlist("late", "Red"),
        lambda lib: lib.remove_from_playlist("morning", "Red"),
        lambda lib: lib.remove_song("Red"),
    ],
)
def test_a_removed_title_is_unknown_afterwards(library, call):
    library.remove_song("Red")
    before = state(library)
    with pytest.raises(KeyError):
        call(library)
    assert state(library) == before


def test_a_removed_title_can_be_added_again_as_a_fresh_song(library):
    library.enqueue("Red")
    library.remove_song("Red")
    library.add_song("Red", "Omar", 30)
    assert library.get_playlist("morning") == ["Blue", "Gold"]
    assert library.get_playlist("late") == []
    assert library.get_queue() == []
    library.add_to_playlist("late", "Red")
    library.enqueue("Red")
    assert library.get_playlist("late") == ["Red"]
    assert library.get_queue() == ["Red"]


def test_removing_the_last_song_leaves_an_empty_library(library):
    for title in ["Blue", "Red", "Gold"]:
        library.remove_song(title)
    assert state(library) == ({"morning": [], "late": []}, [])
    library.add_song("Blue", "Nina", 1)
    library.add_to_playlist("morning", "Blue")
    assert library.get_playlist("morning") == ["Blue"]
