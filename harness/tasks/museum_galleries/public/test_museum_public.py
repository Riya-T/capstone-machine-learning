"""Public checks for museum.py.

Usage (with museum.py importable, e.g. in the sandbox):
    python -m pytest public/test_museum_public.py
"""

import pytest
from museum import Museum, MuseumError


@pytest.fixture
def museum():
    m = Museum()
    m.add_gallery("east")
    m.add_gallery("west")
    m.hang("lilies", "east")
    m.hang("harbor", "east")
    m.hang("dancer", "east")
    m.hang("storm", "west")
    return m


def test_artworks_and_galleries_are_listed_in_order(museum):
    assert museum.get_galleries() == ["east", "west"]
    assert museum.get_artworks("east") == ["lilies", "harbor", "dancer"]
    assert museum.get_artworks("west") == ["storm"]


def test_an_artwork_name_can_hang_only_once(museum):
    with pytest.raises(MuseumError):
        museum.hang("harbor", "west")
    assert museum.get_artworks("west") == ["storm"]


def test_take_down_keeps_the_order_of_the_others(museum):
    museum.take_down("harbor")
    assert museum.get_artworks("east") == ["lilies", "dancer"]
    museum.hang("harbor", "west")
    assert museum.get_artworks("west") == ["storm", "harbor"]


def test_move_artwork_hangs_it_at_the_end(museum):
    museum.move_artwork("lilies", "west")
    assert museum.get_artworks("east") == ["harbor", "dancer"]
    assert museum.get_artworks("west") == ["storm", "lilies"]


def test_swap_artworks_trades_places(museum):
    museum.swap_artworks("harbor", "storm")
    assert museum.get_artworks("east") == ["lilies", "storm", "dancer"]
    assert museum.get_artworks("west") == ["harbor"]


def test_close_gallery_moves_everything_and_closes_it(museum):
    assert museum.close_gallery("east", "west") == 3
    assert museum.get_galleries() == ["west"]
    assert museum.get_artworks("west") == ["storm", "lilies", "harbor", "dancer"]
    with pytest.raises(KeyError):
        museum.get_artworks("east")
