"""Hidden tests for the c_duration change (summed durations). Never shown to
the writer or the editor.

Usage (with playlist.py importable, e.g. in the sandbox):
    python -m pytest changes/c_duration/private/test_duration_new.py
"""

import pytest
from playlist import LibraryError, MusicLibrary


@pytest.fixture
def library():
    lib = MusicLibrary()
    lib.add_song("Blue", "Nina", 200)
    lib.add_song("Red", "Nina", 180)
    lib.add_song("Gold", "Omar", 240)
    lib.create_playlist("morning")
    lib.create_playlist("late")
    return lib


def totals(lib):
    return (
        lib.get_playlist_duration("morning"),
        lib.get_playlist_duration("late"),
        lib.get_queue_duration(),
        lib.get_time_played(),
    )


def test_empty_playlists_and_queues_sum_to_zero(library):
    assert totals(library) == (0, 0, 0, 0)


def test_a_playlist_sums_the_durations_of_its_songs(library):
    library.add_to_playlist("morning", "Blue")
    library.add_to_playlist("morning", "Gold")
    library.add_to_playlist("late", "Red")
    assert library.get_playlist_duration("morning") == 440
    assert library.get_playlist_duration("late") == 180


def test_taking_a_song_out_of_a_playlist_shortens_it(library):
    for title in ["Blue", "Red", "Gold"]:
        library.add_to_playlist("morning", title)
    library.remove_from_playlist("morning", "Red")
    assert library.get_playlist_duration("morning") == 440
    library.remove_song("Gold")
    assert library.get_playlist_duration("morning") == 200


@pytest.mark.parametrize("name", ["evening", None, 4])
def test_duration_of_an_unknown_playlist_raises_key_error(library, name):
    with pytest.raises(KeyError):
        library.get_playlist_duration(name)


def test_the_queue_counts_every_copy_of_a_song(library):
    for title in ["Blue", "Blue", "Red"]:
        library.enqueue(title)
    assert library.get_queue_duration() == 580
    library.play_next()
    assert library.get_queue_duration() == 380
    library.remove_song("Blue")
    assert library.get_queue_duration() == 180


def test_time_played_adds_up_over_many_plays(library):
    for title in ["Blue", "Red", "Blue", "Gold"]:
        library.enqueue(title)
    played = 0
    for expected in [200, 180, 200, 240]:
        library.play_next()
        played += expected
        assert library.get_time_played() == played
    assert library.get_queue_duration() == 0


def test_time_played_only_counts_songs_that_were_actually_played(library):
    library.add_to_playlist("morning", "Blue")
    library.enqueue("Gold")
    assert library.get_time_played() == 0
    library.remove_song("Gold")
    assert library.get_time_played() == 0
    assert library.get_queue_duration() == 0


def test_a_removed_song_still_counts_toward_time_played(library):
    library.enqueue("Blue")
    library.enqueue("Red")
    library.play_next()
    library.remove_song("Blue")
    assert library.get_time_played() == 200
    library.add_song("Blue", "Omar", 5)
    assert library.get_time_played() == 200
    library.enqueue("Blue")
    library.play_next()
    library.play_next()
    assert library.get_time_played() == 385


def test_failed_calls_leave_every_total_alone(library):
    library.add_to_playlist("morning", "Blue")
    library.enqueue("Red")
    library.play_next()
    before = totals(library)
    for call in (
        lambda: library.add_to_playlist("morning", "Blue"),
        lambda: library.add_song("Blue", "Nina", 1),
        lambda: library.enqueue("Green"),
        lambda: library.remove_from_playlist("late", "Blue"),
        lambda: library.add_song("Dusk", "Nina", 0),
    ):
        with pytest.raises((KeyError, ValueError, LibraryError)):
            call()
    assert totals(library) == before


def test_totals_are_kept_per_library():
    first, second = MusicLibrary(), MusicLibrary()
    first.add_song("Blue", "Nina", 200)
    first.enqueue("Blue")
    first.play_next()
    assert first.get_time_played() == 200
    assert second.get_time_played() == 0
    assert second.get_queue_duration() == 0
