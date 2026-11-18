"""Hidden tests for the c_locks change (locked galleries). Never shown to the
writer or the editor.

Usage (with museum.py importable, e.g. in the sandbox):
    python -m pytest changes/c_locks/private/test_locks_new.py
"""

import pytest
from museum import GalleryLocked, Museum, MuseumError


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


# --- locking and unlocking ----------------------------------------------------


def test_new_galleries_are_not_locked(museum):
    assert [museum.is_locked(g) for g in museum.get_galleries()] == [False, False, False]
    museum.add_gallery("south")
    assert museum.is_locked("south") is False


def test_lock_and_unlock(museum):
    museum.lock_gallery("west")
    assert museum.is_locked("west") is True
    assert museum.is_locked("east") is False
    museum.unlock_gallery("west")
    assert museum.is_locked("west") is False


def test_locking_twice_and_unlocking_an_unlocked_gallery_do_nothing(museum):
    museum.lock_gallery("west")
    museum.lock_gallery("west")
    assert museum.is_locked("west") is True
    museum.unlock_gallery("west")
    assert museum.is_locked("west") is False
    museum.unlock_gallery("north")
    assert museum.is_locked("north") is False
    assert state(museum) == [
        ("east", ["lilies", "harbor", "dancer"]),
        ("west", ["storm"]),
        ("north", []),
    ]


@pytest.mark.parametrize(
    "call",
    [
        lambda m: m.lock_gallery("south"),
        lambda m: m.unlock_gallery("south"),
        lambda m: m.is_locked("south"),
    ],
)
def test_galleries_not_in_use_raise_key_error(museum, call):
    with pytest.raises(KeyError):
        call(museum)


def test_a_closed_gallery_cannot_be_locked(museum):
    museum.close_gallery("north", "east")
    with pytest.raises(KeyError):
        museum.lock_gallery("north")


def test_gallery_locked_is_a_museum_error():
    assert issubclass(GalleryLocked, MuseumError)


# --- what a lock blocks -------------------------------------------------------


@pytest.mark.parametrize(
    "call",
    [
        lambda m: m.hang("bridge", "east"),
        lambda m: m.take_down("harbor"),
        lambda m: m.move_artwork("harbor", "north"),
        lambda m: m.move_artwork("storm", "east"),
        lambda m: m.swap_artworks("harbor", "storm"),
        lambda m: m.swap_artworks("storm", "lilies"),
        lambda m: m.swap_artworks("lilies", "dancer"),
        lambda m: m.close_gallery("east", "north"),
        lambda m: m.close_gallery("west", "east"),
        lambda m: m.close_gallery("north", "east"),
    ],
    ids=[
        "hang",
        "take_down",
        "move_out",
        "move_in",
        "swap_first",
        "swap_second",
        "swap_within",
        "close_locked",
        "close_into_locked",
        "close_empty_into_locked",
    ],
)
def test_calls_that_would_change_a_locked_gallery_are_rejected(museum, call):
    museum.lock_gallery("east")
    before = state(museum)
    with pytest.raises(GalleryLocked):
        call(museum)
    assert state(museum) == before


def test_closing_an_empty_locked_gallery_is_rejected(museum):
    museum.lock_gallery("north")
    with pytest.raises(GalleryLocked):
        museum.close_gallery("north", "west")
    assert museum.get_galleries() == ["east", "west", "north"]


# --- what a lock does not block -----------------------------------------------


def test_a_locked_gallery_can_still_be_listed(museum):
    museum.lock_gallery("east")
    assert museum.get_artworks("east") == ["lilies", "harbor", "dancer"]
    assert museum.get_galleries() == ["east", "west", "north"]
    museum.add_gallery("south")
    assert museum.get_galleries() == ["east", "west", "north", "south"]


def test_other_galleries_work_as_before(museum):
    museum.lock_gallery("east")
    museum.hang("bridge", "west")
    museum.move_artwork("storm", "north")
    museum.swap_artworks("bridge", "storm")
    assert museum.get_artworks("west") == ["storm"]
    assert museum.get_artworks("north") == ["bridge"]
    assert museum.close_gallery("west", "north") == 1
    assert museum.get_artworks("north") == ["bridge", "storm"]
    museum.take_down("bridge")
    assert museum.get_artworks("north") == ["storm"]
    assert museum.get_artworks("east") == ["lilies", "harbor", "dancer"]


def test_after_unlocking_everything_works_again(museum):
    museum.lock_gallery("east")
    museum.unlock_gallery("east")
    museum.take_down("harbor")
    museum.swap_artworks("lilies", "storm")
    museum.hang("bridge", "east")
    assert museum.get_artworks("east") == ["storm", "dancer", "bridge"]
    assert museum.close_gallery("east", "west") == 3
    assert museum.get_artworks("west") == ["lilies", "storm", "dancer", "bridge"]


def test_each_gallery_has_its_own_lock(museum):
    museum.lock_gallery("east")
    museum.lock_gallery("west")
    museum.unlock_gallery("east")
    museum.hang("bridge", "east")
    with pytest.raises(GalleryLocked):
        museum.hang("comet", "west")
    assert museum.get_artworks("east") == ["lilies", "harbor", "dancer", "bridge"]
    assert museum.get_artworks("west") == ["storm"]


def test_a_rejected_call_leaves_the_names_as_they_were(museum):
    museum.lock_gallery("west")
    with pytest.raises(GalleryLocked):
        museum.hang("bridge", "west")
    with pytest.raises(GalleryLocked):
        museum.take_down("storm")
    museum.hang("bridge", "north")
    with pytest.raises(MuseumError):
        museum.hang("storm", "north")
    assert museum.get_artworks("north") == ["bridge"]
