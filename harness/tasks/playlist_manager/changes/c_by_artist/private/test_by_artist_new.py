"""Hidden tests for the c_by_artist change (searching by artist). Never shown
to the writer or the editor.

Usage (with playlist.py importable, e.g. in the sandbox):
    python -m pytest changes/c_by_artist/private/test_by_artist_new.py
"""

import pytest
from playlist import MusicLibrary


@pytest.fixture
def library():
    lib = MusicLibrary()
    lib.add_song("Blue", "Nina", 200)
    lib.add_song("Gold", "Omar", 240)
    lib.add_song("Red", "Nina", 180)
    lib.add_song("Dusk", "Pia", 90)
    lib.create_playlist("morning")
    return lib


def test_an_empty_library_has_no_artists():
    lib = MusicLibrary()
    assert lib.get_artists() == []
    assert lib.get_songs_by_artist("Nina") == []


def test_every_song_by_an_artist_is_listed_in_added_order(library):
    library.add_song("Sun", "Nina", 60)
    assert library.get_songs_by_artist("Nina") == ["Blue", "Red", "Sun"]
    assert library.get_songs_by_artist("Pia") == ["Dusk"]


def test_an_artist_without_songs_gives_an_empty_list(library):
    assert library.get_songs_by_artist("Zed") == []
    assert library.get_playlist_by_artist("morning", "Zed") == []


def test_artist_names_match_exactly(library):
    assert library.get_songs_by_artist("nina") == []
    assert library.get_songs_by_artist("Nina ") == []
    library.add_song("Low", "nina", 10)
    assert library.get_songs_by_artist("nina") == ["Low"]
    assert library.get_artists() == ["Nina", "Omar", "Pia", "nina"]


def test_artists_appear_once_in_order_of_their_first_song(library):
    library.add_song("Sun", "Omar", 60)
    library.add_song("Low", "Pia", 10)
    assert library.get_artists() == ["Nina", "Omar", "Pia"]


def test_a_rejected_song_adds_no_artist(library):
    with pytest.raises(ValueError):
        library.add_song("Bad", "Quin", 0)
    with pytest.raises(Exception):
        library.add_song("Blue", "Quin", 10)
    assert library.get_artists() == ["Nina", "Omar", "Pia"]
    assert library.get_songs_by_artist("Quin") == []


def test_a_playlist_filtered_by_artist_keeps_playlist_order(library):
    for title in ["Dusk", "Red", "Gold", "Blue"]:
        library.add_to_playlist("morning", title)
    assert library.get_playlist_by_artist("morning", "Nina") == ["Red", "Blue"]
    assert library.get_playlist_by_artist("morning", "Omar") == ["Gold"]
    assert library.get_playlist("morning") == ["Dusk", "Red", "Gold", "Blue"]


def test_filtering_only_sees_songs_in_that_playlist(library):
    library.create_playlist("late")
    library.add_to_playlist("morning", "Red")
    library.add_to_playlist("late", "Blue")
    assert library.get_playlist_by_artist("morning", "Nina") == ["Red"]
    assert library.get_playlist_by_artist("late", "Nina") == ["Blue"]
    assert library.get_playlist_by_artist("late", "Omar") == []


@pytest.mark.parametrize("name", ["evening", None, 4])
def test_filtering_an_unknown_playlist_raises_key_error(library, name):
    with pytest.raises(KeyError):
        library.get_playlist_by_artist(name, "Nina")


def test_queueing_and_playing_do_not_change_artist_results(library):
    library.enqueue("Blue")
    library.enqueue("Blue")
    library.play_next()
    assert library.get_songs_by_artist("Nina") == ["Blue", "Red"]
    assert library.get_artists() == ["Nina", "Omar", "Pia"]
