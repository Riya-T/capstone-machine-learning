"""Hidden tests for the initial playlist_manager spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with playlist.py importable, e.g. in the sandbox):
    python -m pytest private/test_playlist_initial.py
"""

import pytest
from playlist import LibraryError, MusicLibrary, QueueEmpty

BAD_DURATIONS = [0, -5, 1.5, "10", None]
PLAYLISTS = ["morning", "late"]


@pytest.fixture
def library():
    lib = MusicLibrary()
    lib.add_song("Blue", "Nina", 200)
    lib.add_song("Red", "Nina", 180)
    lib.add_song("Gold", "Omar", 240)
    for name in PLAYLISTS:
        lib.create_playlist(name)
    return lib


def state(lib):
    """Every playlist and the queue, to check that a failed call changed nothing."""
    return ({n: lib.get_playlist(n) for n in PLAYLISTS}, lib.get_queue())


# --- songs ------------------------------------------------------------------


def test_an_added_song_can_be_used_everywhere(library):
    library.add_song("Dusk", "Omar", 90)
    library.add_to_playlist("morning", "Dusk")
    library.enqueue("Dusk")
    assert library.get_playlist("morning") == ["Dusk"]
    assert library.get_queue() == ["Dusk"]


def test_adding_a_title_twice_is_rejected(library):
    library.enqueue("Blue")
    before = state(library)
    with pytest.raises(LibraryError):
        library.add_song("Blue", "Omar", 10)
    assert state(library) == before


@pytest.mark.parametrize("title", [""])
def test_empty_titles_are_rejected(library, title):
    with pytest.raises(ValueError):
        library.add_song(title, "Nina", 100)
    with pytest.raises(KeyError):
        library.enqueue(title)


@pytest.mark.parametrize("artist", [""])
def test_invalid_artists_are_rejected(library, artist):
    with pytest.raises(ValueError):
        library.add_song("Dusk", artist, 100)
    with pytest.raises(KeyError):
        library.enqueue("Dusk")


@pytest.mark.parametrize("duration", BAD_DURATIONS)
def test_invalid_durations_are_rejected(library, duration):
    with pytest.raises(ValueError):
        library.add_song("Dusk", "Nina", duration)
    with pytest.raises(KeyError):
        library.enqueue("Dusk")


def test_a_bad_duration_is_reported_before_a_repeated_title(library):
    with pytest.raises(ValueError):
        library.add_song("Blue", "Nina", -1)


@pytest.mark.parametrize(
    "call",
    [
        lambda lib: lib.add_to_playlist("morning", "Green"),
        lambda lib: lib.enqueue("Green"),
        lambda lib: lib.enqueue(None),
        lambda lib: lib.enqueue(1),
        lambda lib: lib.add_to_playlist("morning", None),
    ],
)
def test_unknown_songs_raise_key_error(library, call):
    library.add_to_playlist("morning", "Blue")
    library.enqueue("Red")
    before = state(library)
    with pytest.raises(KeyError):
        call(library)
    assert state(library) == before


# --- playlists --------------------------------------------------------------


def test_playlists_keep_songs_in_the_order_added(library):
    for title in ["Gold", "Blue", "Red"]:
        library.add_to_playlist("late", title)
    assert library.get_playlist("late") == ["Gold", "Blue", "Red"]
    assert library.get_playlist("morning") == []


def test_a_song_can_be_in_several_playlists(library):
    library.add_to_playlist("morning", "Blue")
    library.add_to_playlist("late", "Blue")
    assert library.get_playlist("morning") == ["Blue"]
    assert library.get_playlist("late") == ["Blue"]


def test_a_song_cannot_be_in_a_playlist_twice(library):
    library.add_to_playlist("morning", "Blue")
    library.add_to_playlist("morning", "Red")
    before = state(library)
    with pytest.raises(LibraryError):
        library.add_to_playlist("morning", "Blue")
    assert state(library) == before


def test_creating_a_playlist_twice_is_rejected(library):
    library.add_to_playlist("morning", "Blue")
    with pytest.raises(LibraryError):
        library.create_playlist("morning")
    assert library.get_playlist("morning") == ["Blue"]


@pytest.mark.parametrize("name", [""])
def test_empty_playlist_names_are_rejected(library, name):
    with pytest.raises(ValueError):
        library.create_playlist(name)
    with pytest.raises(KeyError):
        library.get_playlist(name)


@pytest.mark.parametrize(
    "call",
    [
        lambda lib: lib.add_to_playlist("evening", "Blue"),
        lambda lib: lib.get_playlist("evening"),
        lambda lib: lib.get_playlist(None),
        lambda lib: lib.get_playlist(3),
    ],
)
def test_unknown_playlists_raise_key_error(library, call):
    before = state(library)
    with pytest.raises(KeyError):
        call(library)
    assert state(library) == before


# --- queue ------------------------------------------------------------------


def test_the_queue_is_played_front_to_back(library):
    library.enqueue("Gold")
    library.enqueue("Blue")
    library.enqueue("Red")
    assert library.get_queue() == ["Gold", "Blue", "Red"]
    assert library.play_next() == "Gold"
    assert library.play_next() == "Blue"
    assert library.get_queue() == ["Red"]


def test_the_same_song_can_be_queued_repeatedly(library):
    library.enqueue("Blue")
    library.enqueue("Blue")
    library.enqueue("Red")
    library.enqueue("Blue")
    assert library.get_queue() == ["Blue", "Blue", "Red", "Blue"]
    assert library.play_next() == "Blue"
    assert library.get_queue() == ["Blue", "Red", "Blue"]


def test_an_empty_queue_raises_and_stays_empty(library):
    library.enqueue("Blue")
    assert library.play_next() == "Blue"
    with pytest.raises(QueueEmpty):
        library.play_next()
    assert library.get_queue() == []
    library.enqueue("Red")
    assert library.play_next() == "Red"


def test_queue_empty_is_a_library_error():
    assert issubclass(QueueEmpty, LibraryError)


def test_playlists_and_queue_are_independent(library):
    library.add_to_playlist("morning", "Blue")
    library.enqueue("Red")
    library.play_next()
    assert library.get_playlist("morning") == ["Blue"]
    assert library.get_queue() == []


def test_libraries_do_not_share_songs():
    first, second = MusicLibrary(), MusicLibrary()
    first.add_song("Blue", "Nina", 200)
    first.create_playlist("morning")
    with pytest.raises(KeyError):
        second.enqueue("Blue")
    with pytest.raises(KeyError):
        second.get_playlist("morning")
    second.add_song("Blue", "Omar", 5)
    assert second.get_queue() == []
