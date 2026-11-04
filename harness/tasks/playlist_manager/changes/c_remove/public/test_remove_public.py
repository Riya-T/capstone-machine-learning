"""Public checks for the c_remove change (removing songs). Shown to the
editor, never to the writer.

Usage (with playlist.py importable, e.g. in the sandbox):
    python -m pytest changes/c_remove/public/test_remove_public.py
"""

import pytest
from playlist import MusicLibrary


def test_removing_from_one_playlist_keeps_the_rest():
    lib = MusicLibrary()
    lib.add_song("Blue", "Nina", 200)
    lib.add_song("Red", "Nina", 180)
    lib.add_song("Gold", "Omar", 240)
    lib.create_playlist("morning")
    for title in ["Blue", "Red", "Gold"]:
        lib.add_to_playlist("morning", title)
    lib.remove_from_playlist("morning", "Red")
    assert lib.get_playlist("morning") == ["Blue", "Gold"]


def test_removing_a_song_clears_it_from_playlists_and_queue():
    lib = MusicLibrary()
    lib.add_song("Blue", "Nina", 200)
    lib.add_song("Red", "Nina", 180)
    lib.create_playlist("morning")
    lib.add_to_playlist("morning", "Blue")
    lib.add_to_playlist("morning", "Red")
    lib.enqueue("Blue")
    lib.enqueue("Red")
    lib.enqueue("Blue")
    lib.remove_song("Blue")
    assert lib.get_playlist("morning") == ["Red"]
    assert lib.get_queue() == ["Red"]
    with pytest.raises(KeyError):
        lib.enqueue("Blue")


def test_removing_an_artists_last_song_drops_the_artist_from_searches():
    lib = MusicLibrary()
    if not hasattr(lib, "get_artists"):
        return  # only for a library that can be searched by artist
    lib.add_song("Blue", "Nina", 200)
    lib.add_song("Gold", "Omar", 240)
    lib.add_song("Red", "Nina", 180)
    lib.remove_song("Gold")
    assert lib.get_artists() == ["Nina"]
    assert lib.get_songs_by_artist("Omar") == []
