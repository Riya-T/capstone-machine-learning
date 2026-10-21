"""Public checks for playlist.py.

Usage (with playlist.py importable, e.g. in the sandbox):
    python -m pytest public/test_playlist_public.py
"""

import pytest
from playlist import MusicLibrary, QueueEmpty


@pytest.fixture
def library():
    lib = MusicLibrary()
    lib.add_song("Blue", "Nina", 200)
    lib.add_song("Red", "Nina", 180)
    lib.add_song("Gold", "Omar", 240)
    lib.create_playlist("morning")
    return lib


def test_songs_are_added_to_a_playlist_in_order(library):
    library.add_to_playlist("morning", "Gold")
    library.add_to_playlist("morning", "Blue")
    assert library.get_playlist("morning") == ["Gold", "Blue"]


def test_a_new_playlist_is_empty(library):
    assert library.get_playlist("morning") == []


def test_queue_plays_in_the_order_songs_were_queued(library):
    library.enqueue("Red")
    library.enqueue("Blue")
    assert library.get_queue() == ["Red", "Blue"]
    assert library.play_next() == "Red"
    assert library.get_queue() == ["Blue"]


def test_playing_from_an_empty_queue_raises(library):
    with pytest.raises(QueueEmpty):
        library.play_next()


def test_durations_must_be_positive(library):
    with pytest.raises(ValueError):
        library.add_song("Short", "Nina", 0)
    with pytest.raises(ValueError):
        library.add_song("Negative", "Nina", -30)


def test_unknown_songs_and_playlists_raise_key_error(library):
    with pytest.raises(KeyError):
        library.enqueue("Green")
    with pytest.raises(KeyError):
        library.get_playlist("evening")
