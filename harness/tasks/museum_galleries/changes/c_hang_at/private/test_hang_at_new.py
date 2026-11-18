"""Hidden tests for the c_hang_at change (where new artworks go). Never shown
to the writer or the editor.

Usage (with museum.py importable, e.g. in the sandbox):
    python -m pytest changes/c_hang_at/private/test_hang_at_new.py
"""

import pytest
from museum import Museum, MuseumError


def make(**kwargs):
    m = Museum(**kwargs)
    for name in ["east", "west", "north"]:
        m.add_gallery(name)
    return m


def state(m):
    return [(g, m.get_artworks(g), m.get_hang_at(g)) for g in m.get_galleries()]


# --- the setting ----------------------------------------------------------------


def test_the_default_is_end():
    m = make()
    assert [m.get_hang_at(g) for g in m.get_galleries()] == ["end", "end", "end"]


def test_the_museum_value_applies_to_every_new_gallery():
    m = make(hang_at="start")
    assert [m.get_hang_at(g) for g in m.get_galleries()] == ["start", "start", "start"]
    m = make(hang_at="end")
    assert m.get_hang_at("north") == "end"


@pytest.mark.parametrize("value", ["middle", "START", "", None, 1])
def test_invalid_museum_values_are_rejected(value):
    with pytest.raises(ValueError):
        Museum(hang_at=value)


def test_set_hang_at_changes_only_that_gallery():
    m = make()
    m.set_hang_at("west", "start")
    assert [m.get_hang_at(g) for g in m.get_galleries()] == ["end", "start", "end"]
    m.set_hang_at("west", "end")
    assert m.get_hang_at("west") == "end"


@pytest.mark.parametrize("value", ["middle", "Start", None])
def test_set_hang_at_rejects_invalid_values_and_changes_nothing(value):
    m = make()
    m.set_hang_at("east", "start")
    with pytest.raises(ValueError):
        m.set_hang_at("east", value)
    assert m.get_hang_at("east") == "start"


def test_galleries_not_in_use_raise_key_error():
    m = make()
    m.close_gallery("north", "east")
    for call in (
        lambda: m.set_hang_at("south", "start"),
        lambda: m.get_hang_at("south"),
        lambda: m.set_hang_at("north", "start"),
        lambda: m.get_hang_at("north"),
    ):
        with pytest.raises(KeyError):
            call()


def test_a_gallery_added_again_does_not_keep_the_closed_setting():
    m = make()
    m.set_hang_at("north", "start")
    m.close_gallery("north", "east")
    m.add_gallery("north")
    assert m.get_hang_at("north") == "end"
    m = make(hang_at="start")
    m.set_hang_at("north", "end")
    m.close_gallery("north", "east")
    m.add_gallery("north")
    assert m.get_hang_at("north") == "start"


# --- putting artworks in at the start ---------------------------------------------


def test_hang_at_the_start_of_one_gallery():
    m = make()
    m.set_hang_at("east", "start")
    for artwork in ["lilies", "harbor", "dancer"]:
        m.hang(artwork, "east")
    m.hang("storm", "west")
    m.hang("comet", "west")
    assert m.get_artworks("east") == ["dancer", "harbor", "lilies"]
    assert m.get_artworks("west") == ["storm", "comet"]


def test_move_artwork_into_a_start_gallery_puts_it_first():
    m = make()
    for artwork in ["lilies", "harbor", "dancer"]:
        m.hang(artwork, "east")
    m.hang("storm", "west")
    m.set_hang_at("west", "start")
    m.move_artwork("harbor", "west")
    assert m.get_artworks("west") == ["harbor", "storm"]
    assert m.get_artworks("east") == ["lilies", "dancer"]
    m.move_artwork("storm", "east")  # east still hangs at the end
    assert m.get_artworks("east") == ["lilies", "dancer", "storm"]


def test_close_gallery_into_a_start_gallery_keeps_the_moved_order():
    m = make()
    for artwork in ["lilies", "harbor", "dancer"]:
        m.hang(artwork, "east")
    m.hang("storm", "west")
    m.hang("comet", "west")
    m.set_hang_at("west", "start")
    assert m.close_gallery("east", "west") == 3
    assert m.get_artworks("west") == ["lilies", "harbor", "dancer", "storm", "comet"]
    assert m.get_galleries() == ["west", "north"]


def test_the_setting_of_the_closed_gallery_does_not_matter():
    m = make()
    m.set_hang_at("east", "start")
    m.hang("lilies", "east")
    m.hang("harbor", "east")
    m.hang("storm", "west")
    assert m.close_gallery("east", "west") == 2
    assert m.get_artworks("west") == ["storm", "harbor", "lilies"]


def test_take_down_and_swap_are_not_affected():
    m = make(hang_at="start")
    for artwork in ["lilies", "harbor", "dancer"]:
        m.hang(artwork, "east")
    m.hang("storm", "west")
    m.take_down("harbor")
    assert m.get_artworks("east") == ["dancer", "lilies"]
    m.swap_artworks("lilies", "storm")
    assert m.get_artworks("east") == ["dancer", "storm"]
    assert m.get_artworks("west") == ["lilies"]


def test_changing_the_setting_does_not_rearrange_artworks():
    m = make()
    m.hang("lilies", "east")
    m.hang("harbor", "east")
    m.set_hang_at("east", "start")
    assert m.get_artworks("east") == ["lilies", "harbor"]
    m.hang("dancer", "east")
    assert m.get_artworks("east") == ["dancer", "lilies", "harbor"]
    m.set_hang_at("east", "end")
    m.hang("storm", "east")
    assert m.get_artworks("east") == ["dancer", "lilies", "harbor", "storm"]


def test_existing_rules_still_apply_in_a_start_gallery():
    m = make(hang_at="start")
    m.hang("lilies", "east")
    before = state(m)
    with pytest.raises(MuseumError):
        m.hang("lilies", "west")
    with pytest.raises(ValueError):
        m.move_artwork("lilies", "east")
    with pytest.raises(ValueError):
        m.close_gallery("east", "east")
    with pytest.raises(KeyError):
        m.hang("storm", "south")
    assert state(m) == before
