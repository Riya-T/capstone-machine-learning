"""Hidden tests for the c_move_many change (several moves as one call). Never
shown to the writer or the editor.

Usage (with museum.py importable, e.g. in the sandbox):
    python -m pytest changes/c_move_many/private/test_move_many_new.py
"""

import pytest
from museum import Museum


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


# --- successful calls ---------------------------------------------------------


def test_one_pair_works_like_move_artwork(museum):
    museum.move_many([("lilies", "west")])
    assert museum.get_artworks("east") == ["harbor", "dancer"]
    assert museum.get_artworks("west") == ["storm", "lilies"]


def test_pairs_are_applied_in_the_order_given(museum):
    museum.move_many([("dancer", "north"), ("lilies", "north"), ("storm", "north")])
    assert museum.get_artworks("north") == ["dancer", "lilies", "storm"]
    assert museum.get_artworks("east") == ["harbor"]
    assert museum.get_artworks("west") == []


def test_a_later_pair_can_move_an_artwork_moved_earlier(museum):
    museum.move_many([("harbor", "west"), ("harbor", "north")])
    assert museum.get_artworks("east") == ["lilies", "dancer"]
    assert museum.get_artworks("west") == ["storm"]
    assert museum.get_artworks("north") == ["harbor"]


def test_an_artwork_can_go_back_to_its_gallery_at_the_end(museum):
    museum.move_many([("lilies", "west"), ("lilies", "east")])
    assert museum.get_artworks("east") == ["harbor", "dancer", "lilies"]
    assert museum.get_artworks("west") == ["storm"]


def test_artworks_can_trade_galleries(museum):
    museum.move_many([("storm", "east"), ("harbor", "west")])
    assert museum.get_artworks("east") == ["lilies", "dancer", "storm"]
    assert museum.get_artworks("west") == ["harbor"]


def test_galleries_and_names_are_unchanged_by_moves(museum):
    museum.move_many([("storm", "north"), ("dancer", "west")])
    assert museum.get_galleries() == ["east", "west", "north"]
    museum.take_down("storm")
    museum.hang("storm", "east")
    assert museum.get_artworks("east") == ["lilies", "harbor", "storm"]


# --- failed calls change nothing ----------------------------------------------


@pytest.mark.parametrize(
    "moves",
    [
        [("harbor", "west"), ("lilies", "south")],
        [("harbor", "west"), ("bridge", "north")],
        [("storm", "north"), ("dancer", "west"), ("lilies", "south")],
        [("bridge", "west")],
    ],
    ids=["gallery_not_in_use", "artwork_not_hung", "third_pair", "first_pair"],
)
def test_a_pair_that_raises_key_error_changes_nothing(museum, moves):
    before = state(museum)
    with pytest.raises(KeyError):
        museum.move_many(moves)
    assert state(museum) == before


@pytest.mark.parametrize(
    "moves",
    [
        [("harbor", "east")],
        [("harbor", "west"), ("harbor", "west")],
        [("lilies", "north"), ("storm", "north"), ("lilies", "north")],
    ],
    ids=["own_gallery", "moved_there_already", "moved_there_earlier"],
)
def test_a_move_to_its_own_gallery_at_that_point_changes_nothing(museum, moves):
    before = state(museum)
    with pytest.raises(ValueError):
        museum.move_many(moves)
    assert state(museum) == before


def test_a_closed_gallery_is_not_in_use(museum):
    museum.close_gallery("north", "west")
    before = state(museum)
    with pytest.raises(KeyError):
        museum.move_many([("storm", "east"), ("lilies", "north")])
    assert state(museum) == before


def test_the_museum_works_normally_after_a_failed_call(museum):
    with pytest.raises(KeyError):
        museum.move_many([("lilies", "north"), ("harbor", "north"), ("dancer", "south")])
    museum.move_many([("dancer", "north"), ("harbor", "north")])
    assert museum.get_artworks("north") == ["dancer", "harbor"]
    assert museum.get_artworks("east") == ["lilies"]
    museum.move_artwork("lilies", "north")
    assert museum.get_artworks("north") == ["dancer", "harbor", "lilies"]
