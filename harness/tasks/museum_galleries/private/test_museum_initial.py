"""Hidden tests for the initial museum_galleries spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with museum.py importable, e.g. in the sandbox):
    python -m pytest private/test_museum_initial.py
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
    """Every gallery in order with its artworks in order, to check that a
    failed call changed nothing."""
    return [(g, m.get_artworks(g)) for g in m.get_galleries()]


# --- galleries ----------------------------------------------------------------


def test_a_new_museum_has_no_galleries():
    assert Museum().get_galleries() == []


def test_a_new_gallery_is_empty():
    m = Museum()
    m.add_gallery("east")
    assert m.get_artworks("east") == []


def test_galleries_are_listed_in_the_order_added():
    m = Museum()
    for name in ["west", "north", "east"]:
        m.add_gallery(name)
    assert m.get_galleries() == ["west", "north", "east"]


def test_adding_a_name_in_use_is_rejected(museum):
    before = state(museum)
    with pytest.raises(MuseumError):
        museum.add_gallery("west")
    assert state(museum) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda m: m.hang("bridge", "south"),
        lambda m: m.move_artwork("lilies", "south"),
        lambda m: m.close_gallery("south", "east"),
        lambda m: m.close_gallery("east", "south"),
        lambda m: m.get_artworks("south"),
    ],
)
def test_galleries_that_are_not_in_use_raise_key_error(museum, call):
    before = state(museum)
    with pytest.raises(KeyError):
        call(museum)
    assert state(museum) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda m: m.hang("bridge", "north"),
        lambda m: m.move_artwork("lilies", "north"),
        lambda m: m.close_gallery("north", "east"),
        lambda m: m.close_gallery("east", "north"),
        lambda m: m.get_artworks("north"),
    ],
)
def test_a_closed_gallery_is_not_in_use(museum, call):
    museum.close_gallery("north", "west")  # north is empty
    before = state(museum)
    with pytest.raises(KeyError):
        call(museum)
    assert state(museum) == before


def test_a_closed_name_can_be_added_again_as_a_new_empty_gallery(museum):
    museum.close_gallery("north", "west")  # north is empty
    museum.add_gallery("north")
    assert museum.get_galleries() == ["east", "west", "north"]
    assert museum.get_artworks("north") == []
    museum.hang("bridge", "north")
    assert museum.get_artworks("north") == ["bridge"]
    assert museum.get_artworks("west") == ["storm"]


# --- hanging and taking down --------------------------------------------------


def test_artworks_are_listed_in_the_order_hung(museum):
    assert museum.get_artworks("east") == ["lilies", "harbor", "dancer"]
    assert museum.get_artworks("west") == ["storm"]
    assert museum.get_artworks("north") == []


def test_a_name_that_already_hangs_is_rejected(museum):
    before = state(museum)
    with pytest.raises(MuseumError):
        museum.hang("harbor", "east")
    with pytest.raises(MuseumError):
        museum.hang("harbor", "north")
    assert state(museum) == before


def test_take_down_keeps_the_order_of_the_others(museum):
    museum.take_down("harbor")
    assert museum.get_artworks("east") == ["lilies", "dancer"]
    museum.take_down("lilies")
    assert museum.get_artworks("east") == ["dancer"]


def test_the_last_artwork_of_a_gallery_can_be_taken_down(museum):
    museum.take_down("storm")
    assert museum.get_artworks("west") == []
    assert museum.get_galleries() == ["east", "west", "north"]


def test_a_taken_down_name_can_be_hung_again(museum):
    museum.take_down("lilies")
    museum.hang("lilies", "west")
    assert museum.get_artworks("west") == ["storm", "lilies"]
    assert museum.get_artworks("east") == ["harbor", "dancer"]


# --- moving and swapping ------------------------------------------------------


def test_move_artwork_hangs_it_at_the_end_of_the_other_gallery(museum):
    museum.move_artwork("lilies", "west")
    assert museum.get_artworks("east") == ["harbor", "dancer"]
    assert museum.get_artworks("west") == ["storm", "lilies"]


def test_move_artwork_into_an_empty_gallery(museum):
    museum.move_artwork("harbor", "north")
    assert museum.get_artworks("north") == ["harbor"]
    assert museum.get_artworks("east") == ["lilies", "dancer"]


def test_moving_an_artwork_to_its_own_gallery_is_rejected(museum):
    before = state(museum)
    with pytest.raises(ValueError):
        museum.move_artwork("harbor", "east")
    assert state(museum) == before


def test_swap_between_galleries(museum):
    museum.swap_artworks("harbor", "storm")
    assert museum.get_artworks("east") == ["lilies", "storm", "dancer"]
    assert museum.get_artworks("west") == ["harbor"]


def test_swap_in_the_other_order_gives_the_same_result(museum):
    museum.swap_artworks("storm", "lilies")
    assert museum.get_artworks("east") == ["storm", "harbor", "dancer"]
    assert museum.get_artworks("west") == ["lilies"]


def test_swap_within_a_gallery(museum):
    museum.swap_artworks("lilies", "dancer")
    assert museum.get_artworks("east") == ["dancer", "harbor", "lilies"]
    assert museum.get_artworks("west") == ["storm"]


@pytest.mark.parametrize(
    "call",
    [
        lambda m: m.take_down("bridge"),
        lambda m: m.move_artwork("bridge", "west"),
        lambda m: m.swap_artworks("bridge", "storm"),
        lambda m: m.swap_artworks("storm", "bridge"),
    ],
)
def test_artworks_that_do_not_hang_raise_key_error(museum, call):
    before = state(museum)
    with pytest.raises(KeyError):
        call(museum)
    assert state(museum) == before


def test_a_taken_down_artwork_no_longer_hangs(museum):
    museum.take_down("storm")
    before = state(museum)
    for call in (
        lambda: museum.take_down("storm"),
        lambda: museum.move_artwork("storm", "north"),
        lambda: museum.swap_artworks("storm", "lilies"),
    ):
        with pytest.raises(KeyError):
            call()
    assert state(museum) == before


# --- closing ------------------------------------------------------------------


def test_close_gallery_moves_every_artwork_in_order_and_closes_it(museum):
    assert museum.close_gallery("east", "west") == 3
    assert museum.get_galleries() == ["west", "north"]
    assert museum.get_artworks("west") == ["storm", "lilies", "harbor", "dancer"]


def test_closing_into_an_empty_gallery(museum):
    assert museum.close_gallery("west", "north") == 1
    assert museum.get_galleries() == ["east", "north"]
    assert museum.get_artworks("north") == ["storm"]


def test_closing_an_empty_gallery_moves_nothing(museum):
    assert museum.close_gallery("north", "east") == 0
    assert museum.get_galleries() == ["east", "west"]
    assert museum.get_artworks("east") == ["lilies", "harbor", "dancer"]


def test_the_other_galleries_keep_their_order_after_a_close(museum):
    museum.add_gallery("south")
    museum.close_gallery("west", "south")
    assert museum.get_galleries() == ["east", "north", "south"]


def test_closing_a_gallery_into_itself_is_rejected(museum):
    before = state(museum)
    with pytest.raises(ValueError):
        museum.close_gallery("east", "east")
    with pytest.raises(ValueError):
        museum.close_gallery("north", "north")
    assert state(museum) == before


def test_artworks_from_a_closed_gallery_still_hang(museum):
    museum.close_gallery("west", "east")
    museum.move_artwork("storm", "north")
    assert museum.get_artworks("east") == ["lilies", "harbor", "dancer"]
    assert museum.get_artworks("north") == ["storm"]
    with pytest.raises(MuseumError):
        museum.hang("storm", "east")


# --- general ------------------------------------------------------------------


def test_museums_do_not_share_galleries():
    first, second = Museum(), Museum()
    first.add_gallery("east")
    first.hang("lilies", "east")
    assert second.get_galleries() == []
    second.add_gallery("east")
    second.hang("lilies", "east")
    assert second.get_artworks("east") == ["lilies"]
