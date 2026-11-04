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
    second.add_song("Blue", "Nina", 200)
    assert first.get_song_time_played("Blue") == 200
    assert second.get_song_time_played("Blue") == 0


def song_times(lib, titles=("Blue", "Red", "Gold")):
    return {title: lib.get_song_time_played(title) for title in titles}


def test_each_song_counts_only_its_own_plays(library):
    for title in ["Red", "Blue", "Red", "Gold", "Red"]:
        library.enqueue(title)
    for _ in range(5):
        library.play_next()
    assert song_times(library) == {"Blue": 200, "Red": 540, "Gold": 240}
    assert library.get_time_played() == 980


def test_a_song_that_was_queued_but_not_played_has_no_time(library):
    library.enqueue("Blue")
    library.enqueue("Gold")
    assert song_times(library) == {"Blue": 0, "Red": 0, "Gold": 0}
    library.play_next()
    assert song_times(library) == {"Blue": 200, "Red": 0, "Gold": 0}


@pytest.mark.parametrize("title", ["Green", "blue", "", None])
def test_song_time_of_a_title_not_in_the_library_raises_key_error(library, title):
    with pytest.raises(KeyError):
        library.get_song_time_played(title)


def test_a_removed_song_has_no_time_of_its_own_but_still_counts_in_the_total(library):
    library.enqueue("Blue")
    library.enqueue("Red")
    library.play_next()
    library.play_next()
    library.remove_song("Blue")
    with pytest.raises(KeyError):
        library.get_song_time_played("Blue")
    assert library.get_song_time_played("Red") == 180
    assert library.get_time_played() == 380


def test_a_song_added_again_starts_again_from_zero(library):
    for title in ["Blue", "Red", "Blue"]:
        library.enqueue(title)
    for _ in range(3):
        library.play_next()
    library.remove_song("Blue")
    library.add_song("Blue", "Omar", 5)
    assert song_times(library) == {"Blue": 0, "Red": 180, "Gold": 0}
    library.enqueue("Blue")
    library.play_next()
    assert song_times(library) == {"Blue": 5, "Red": 180, "Gold": 0}
    assert library.get_time_played() == 585


def test_a_song_removed_with_copies_still_queued_starts_again_from_zero(library):
    for title in ["Gold", "Gold", "Gold"]:
        library.enqueue(title)
    library.play_next()
    library.remove_song("Gold")
    library.add_song("Gold", "Omar", 240)
    library.enqueue("Gold")
    library.play_next()
    assert library.get_song_time_played("Gold") == 240
    assert library.get_time_played() == 480
    assert library.get_queue_duration() == 0


def test_taking_a_song_out_of_a_playlist_keeps_its_time(library):
    library.add_to_playlist("morning", "Red")
    library.enqueue("Red")
    library.play_next()
    library.remove_from_playlist("morning", "Red")
    assert library.get_song_time_played("Red") == 180


def test_failed_calls_leave_every_song_time_alone(library):
    for title in ["Blue", "Red", "Blue"]:
        library.enqueue(title)
    for _ in range(3):
        library.play_next()
    before = (song_times(library), library.get_time_played())
    for call in (
        lambda: library.add_song("Blue", "Nina", 1),
        lambda: library.add_song("Red", "Omar", 9),
        lambda: library.remove_song("Green"),
        lambda: library.enqueue("Green"),
        lambda: library.remove_from_playlist("morning", "Blue"),
    ):
        with pytest.raises((KeyError, ValueError, LibraryError)):
            call()
    assert (song_times(library), library.get_time_played()) == before
