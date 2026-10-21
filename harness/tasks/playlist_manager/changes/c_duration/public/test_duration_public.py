"""Public checks for the c_duration change (summed durations). Shown to the
editor, never to the writer.

Usage (with playlist.py importable, e.g. in the sandbox):
    python -m pytest changes/c_duration/public/test_duration_public.py
"""

from playlist import MusicLibrary


def test_playlist_and_queue_durations_add_up():
    lib = MusicLibrary()
    lib.add_song("Blue", "Nina", 200)
    lib.add_song("Red", "Nina", 180)
    lib.create_playlist("morning")
    lib.add_to_playlist("morning", "Blue")
    lib.add_to_playlist("morning", "Red")
    lib.enqueue("Red")
    lib.enqueue("Red")
    assert lib.get_playlist_duration("morning") == 380
    assert lib.get_queue_duration() == 360


def test_time_played_grows_with_every_song_played():
    lib = MusicLibrary()
    lib.add_song("Blue", "Nina", 200)
    lib.add_song("Red", "Nina", 180)
    lib.enqueue("Blue")
    lib.enqueue("Red")
    assert lib.get_time_played() == 0
    lib.play_next()
    assert lib.get_time_played() == 200
    lib.play_next()
    assert lib.get_time_played() == 380
