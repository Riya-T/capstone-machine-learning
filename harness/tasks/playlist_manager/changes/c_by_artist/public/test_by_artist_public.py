"""Public checks for the c_by_artist change (searching by artist). Shown to
the editor, never to the writer.

Usage (with playlist.py importable, e.g. in the sandbox):
    python -m pytest changes/c_by_artist/public/test_by_artist_public.py
"""

from playlist import MusicLibrary


def test_songs_by_an_artist_come_back_in_the_order_added():
    lib = MusicLibrary()
    lib.add_song("Blue", "Nina", 200)
    lib.add_song("Gold", "Omar", 240)
    lib.add_song("Red", "Nina", 180)
    assert lib.get_songs_by_artist("Nina") == ["Blue", "Red"]
    assert lib.get_songs_by_artist("Omar") == ["Gold"]
    assert lib.get_songs_by_artist("Zed") == []


def test_artists_are_listed_once_by_first_song():
    lib = MusicLibrary()
    lib.add_song("Blue", "Nina", 200)
    lib.add_song("Gold", "Omar", 240)
    lib.add_song("Red", "Nina", 180)
    assert lib.get_artists() == ["Nina", "Omar"]


def test_a_playlist_can_be_filtered_by_artist():
    lib = MusicLibrary()
    lib.add_song("Blue", "Nina", 200)
    lib.add_song("Gold", "Omar", 240)
    lib.add_song("Red", "Nina", 180)
    lib.create_playlist("morning")
    for title in ["Red", "Gold", "Blue"]:
        lib.add_to_playlist("morning", title)
    assert lib.get_playlist_by_artist("morning", "Nina") == ["Red", "Blue"]
