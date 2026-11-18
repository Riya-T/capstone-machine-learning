"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with museum.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
"""

import pytest
from museum import Museum, MuseumError


@pytest.fixture
def museum():
    m = Museum()
    for name in ["east", "west", "north"]:
        m.add_gallery(name)
    for artwork in ["lilies", "harbor", "dancer"]:
        m.hang(artwork, "east")
    m.hang("storm", "west")
    return m


def state(m):
    return [(g, m.get_artworks(g)) for g in m.get_galleries()]


# --- each call can be undone --------------------------------------------------


def test_undo_of_a_hang_frees_the_name(museum):
    before = state(museum)
    museum.hang("bridge", "north")
    museum.undo()
    assert state(museum) == before
    museum.hang("bridge", "west")
    assert museum.get_artworks("west") == ["storm", "bridge"]


def test_undo_of_a_take_down_puts_it_back_at_its_position(museum):
    before = state(museum)
    museum.take_down("harbor")
    museum.undo()
    assert state(museum) == before
    assert museum.get_artworks("east") == ["lilies", "harbor", "dancer"]


def test_undo_of_taking_down_the_first_artwork(museum):
    before = state(museum)
    museum.take_down("lilies")
    museum.undo()
    assert state(museum) == before


def test_an_artwork_brought_back_hangs_again(museum):
    museum.take_down("storm")
    museum.undo()
    with pytest.raises(MuseumError):
        museum.hang("storm", "north")
    museum.move_artwork("storm", "north")
    assert museum.get_artworks("north") == ["storm"]


def test_undo_of_a_move_puts_it_back_at_its_old_position(museum):
    before = state(museum)
    museum.move_artwork("harbor", "west")
    museum.undo()
    assert state(museum) == before
    assert museum.get_artworks("west") == ["storm"]


def test_undo_of_a_swap_between_galleries(museum):
    before = state(museum)
    museum.swap_artworks("storm", "lilies")
    museum.undo()
    assert state(museum) == before


def test_undo_of_a_swap_within_a_gallery(museum):
    before = state(museum)
    museum.swap_artworks("dancer", "lilies")
    museum.undo()
    assert museum.get_artworks("east") == ["lilies", "harbor", "dancer"]
    assert state(museum) == before


def test_undo_of_close_gallery_brings_it_back_with_its_artworks(museum):
    before = state(museum)
    assert museum.close_gallery("east", "west") == 3
    museum.undo()
    assert state(museum) == before
    assert museum.get_galleries() == ["east", "west", "north"]
    assert museum.get_artworks("west") == ["storm"]


def test_undo_of_close_gallery_keeps_its_place_in_the_list(museum):
    museum.add_gallery("south")
    before = state(museum)
    museum.close_gallery("west", "south")
    assert museum.get_galleries() == ["east", "north", "south"]
    museum.undo()
    assert museum.get_galleries() == ["east", "west", "north", "south"]
    assert state(museum) == before


def test_a_gallery_brought_back_is_in_use_again(museum):
    museum.close_gallery("east", "north")
    museum.undo()
    with pytest.raises(MuseumError):
        museum.add_gallery("east")
    museum.hang("bridge", "east")
    assert museum.get_artworks("east") == ["lilies", "harbor", "dancer", "bridge"]
    assert museum.close_gallery("east", "west") == 4
    assert museum.get_galleries() == ["west", "north"]


def test_closing_an_empty_gallery_can_be_undone(museum):
    museum.hang("bridge", "east")
    assert museum.close_gallery("north", "east") == 0
    museum.undo()
    assert museum.get_galleries() == ["east", "west", "north"]
    assert museum.get_artworks("north") == []
    museum.undo()  # the bridge
    assert museum.get_artworks("east") == ["lilies", "harbor", "dancer"]


def test_undo_of_add_gallery_removes_it_and_frees_the_name(museum):
    museum.add_gallery("south")
    museum.undo()
    assert museum.get_galleries() == ["east", "west", "north"]
    with pytest.raises(KeyError):
        museum.get_artworks("south")
    museum.add_gallery("south")
    assert museum.get_galleries() == ["east", "west", "north", "south"]


def test_undo_through_a_name_that_was_closed_and_added_again(museum):
    museum.add_gallery("south")
    museum.hang("bridge", "south")
    museum.close_gallery("south", "north")
    museum.add_gallery("south")  # a new, empty south
    museum.hang("comet", "south")
    museum.undo()  # the comet
    museum.undo()  # the new south
    assert museum.get_galleries() == ["east", "west", "north"]
    museum.undo()  # the close: the old south comes back with the bridge
    assert museum.get_galleries() == ["east", "west", "north", "south"]
    assert museum.get_artworks("south") == ["bridge"]
    assert museum.get_artworks("north") == []
    museum.undo()  # the bridge
    museum.undo()  # the first south
    assert museum.get_galleries() == ["east", "west", "north"]


# --- what is and is not recorded ----------------------------------------------


def test_each_undo_goes_one_call_further_back():
    m = Museum()
    calls = [
        lambda: m.add_gallery("east"),
        lambda: m.add_gallery("west"),
        lambda: m.hang("lilies", "east"),
        lambda: m.hang("harbor", "east"),
        lambda: m.hang("storm", "west"),
        lambda: m.add_gallery("north"),
        lambda: m.hang("dancer", "east"),
        lambda: m.swap_artworks("harbor", "storm"),
        lambda: m.move_artwork("lilies", "north"),
        lambda: m.take_down("dancer"),
        lambda: m.swap_artworks("storm", "lilies"),
        lambda: m.close_gallery("west", "north"),
        lambda: m.hang("dancer", "east"),
        lambda: m.close_gallery("east", "north"),
        lambda: m.add_gallery("east"),
    ]
    states = [state(m)]
    for call in calls:
        call()
        states.append(state(m))
    assert m.get_galleries() == ["north", "east"]
    assert m.get_artworks("north") == ["storm", "harbor", "lilies", "dancer"]
    for expected in reversed(states[:-1]):
        m.undo()
        assert state(m) == expected
    with pytest.raises(MuseumError):
        m.undo()
    assert m.get_galleries() == []


def test_failed_calls_are_not_recorded(museum):
    museum.hang("bridge", "north")
    for call in (
        lambda: museum.add_gallery("east"),
        lambda: museum.hang("lilies", "north"),
        lambda: museum.hang("comet", "south"),
        lambda: museum.take_down("comet"),
        lambda: museum.move_artwork("harbor", "east"),
        lambda: museum.swap_artworks("harbor", "comet"),
        lambda: museum.close_gallery("east", "east"),
        lambda: museum.close_gallery("south", "east"),
    ):
        with pytest.raises((KeyError, ValueError, MuseumError)):
            call()
    museum.undo()  # the bridge
    assert museum.get_artworks("north") == []
    assert museum.get_artworks("east") == ["lilies", "harbor", "dancer"]


def test_get_calls_are_not_recorded(museum):
    museum.hang("bridge", "north")
    museum.get_artworks("north")
    museum.get_galleries()
    museum.undo()
    assert museum.get_artworks("north") == []
    assert museum.get_artworks("west") == ["storm"]


def test_there_is_no_redo():
    m = Museum()
    m.add_gallery("east")
    m.hang("lilies", "east")
    m.undo()
    m.undo()
    assert m.get_galleries() == []
    with pytest.raises(MuseumError):
        m.undo()


def test_new_calls_after_an_undo_are_undone_first(museum):
    museum.take_down("harbor")
    museum.undo()
    museum.move_artwork("dancer", "north")
    museum.undo()
    assert museum.get_artworks("east") == ["lilies", "harbor", "dancer"]
    museum.undo()  # the storm from the fixture
    assert museum.get_artworks("west") == []
    assert museum.get_artworks("east") == ["lilies", "harbor", "dancer"]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    m = Museum()
    with pytest.raises(MuseumError):
        m.undo()
    m.add_gallery("east")
    m.undo()
    with pytest.raises(MuseumError):
        m.undo()
    assert m.get_galleries() == []
    m.add_gallery("east")
    m.hang("lilies", "east")
    assert m.get_artworks("east") == ["lilies"]


def test_the_whole_fixture_can_be_undone(museum):
    for _ in range(7):
        museum.undo()
    assert museum.get_galleries() == []
    with pytest.raises(MuseumError):
        museum.undo()


def test_undo_restores_what_a_later_call_checks(museum):
    museum.swap_artworks("storm", "dancer")
    museum.undo()
    with pytest.raises(ValueError):
        museum.move_artwork("dancer", "east")
    museum.move_artwork("storm", "east")
    assert museum.get_artworks("east") == ["lilies", "harbor", "dancer", "storm"]
