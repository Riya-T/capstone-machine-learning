"""Hidden tests for the c_move_cities change (moving several cities as one
call). Never shown to the writer or the editor.

Usage (with tours.py importable, e.g. in the sandbox):
    python -m pytest changes/c_move_cities/private/test_move_cities_new.py
"""

import pytest
from tours import TourError, TourPlanner


@pytest.fixture
def planner():
    p = TourPlanner()
    for name in ["coast", "alps", "lakes"]:
        p.add_tour(name)
    for city in ["lisbon", "porto", "lyon"]:
        p.add_city("coast", city)
    for city in ["zurich", "lyon", "milan"]:
        p.add_city("alps", city)
    for city in ["geneva", "milan"]:
        p.add_city("lakes", city)
    return p


def state(p):
    return [(t, p.get_cities(t)) for t in p.get_tours()]


# --- successful calls ---------------------------------------------------------


def test_one_city_moves_to_the_end_of_target(planner):
    planner.move_cities("coast", "lakes", ["porto"])
    assert planner.get_cities("coast") == ["lisbon", "lyon"]
    assert planner.get_cities("lakes") == ["geneva", "milan", "porto"]


def test_cities_are_added_in_the_order_of_the_list(planner):
    planner.move_cities("alps", "coast", ["milan", "zurich"])
    assert planner.get_cities("alps") == ["lyon"]
    assert planner.get_cities("coast") == ["lisbon", "porto", "lyon", "milan", "zurich"]


def test_every_city_can_move_and_source_stays(planner):
    planner.move_cities("lakes", "coast", ["geneva", "milan"])
    assert planner.get_cities("lakes") == []
    assert planner.get_tours() == ["coast", "alps", "lakes"]
    assert planner.get_cities("coast") == ["lisbon", "porto", "lyon", "geneva", "milan"]


def test_a_city_can_move_to_an_empty_tour(planner):
    planner.add_tour("nordic")
    planner.move_cities("alps", "nordic", ["lyon", "zurich"])
    assert planner.get_cities("nordic") == ["lyon", "zurich"]
    assert planner.get_cities("alps") == ["milan"]


def test_other_tours_are_not_touched(planner):
    planner.move_cities("alps", "lakes", ["lyon"])
    assert planner.get_cities("coast") == ["lisbon", "porto", "lyon"]
    assert planner.get_cities("lakes") == ["geneva", "milan", "lyon"]


def test_moved_cities_behave_like_any_other(planner):
    planner.move_cities("coast", "lakes", ["lisbon", "porto"])
    with pytest.raises(TourError):
        planner.add_city("lakes", "porto")
    planner.add_city("coast", "porto")
    assert planner.cancel_city("porto") == 2
    assert planner.get_cities("lakes") == ["geneva", "milan", "lisbon"]


# --- failed calls change nothing ----------------------------------------------


@pytest.mark.parametrize(
    "call",
    [
        lambda p: p.move_cities("nordic", "coast", ["lisbon"]),
        lambda p: p.move_cities("coast", "nordic", ["lisbon"]),
    ],
    ids=["source", "target"],
)
def test_tours_not_in_use_raise_key_error(planner, call):
    before = state(planner)
    with pytest.raises(KeyError):
        call(planner)
    assert state(planner) == before


def test_a_merged_tour_is_not_in_use(planner):
    planner.merge_tours("alps", "lakes")
    before = state(planner)
    with pytest.raises(KeyError):
        planner.move_cities("lakes", "coast", ["geneva"])
    assert state(planner) == before


def test_the_same_tour_on_both_sides_raises_value_error(planner):
    before = state(planner)
    with pytest.raises(ValueError):
        planner.move_cities("coast", "coast", ["lisbon"])
    assert state(planner) == before


@pytest.mark.parametrize(
    "cities",
    [
        ["rome"],
        ["lisbon", "rome"],
        ["porto", "lisbon", "zurich"],
        ["lisbon", "lyon"],
        ["porto", "porto"],
        ["lisbon", "porto", "lisbon"],
    ],
    ids=[
        "not_on_source",
        "second_not_on_source",
        "third_not_on_source",
        "already_on_target",
        "listed_twice",
        "listed_twice_later",
    ],
)
def test_a_bad_city_raises_tour_error_and_nothing_moves(planner, cities):
    before = state(planner)
    with pytest.raises(TourError):
        planner.move_cities("coast", "alps", cities)
    assert state(planner) == before


def test_the_planner_works_normally_after_a_failed_call(planner):
    with pytest.raises(TourError):
        planner.move_cities("coast", "lakes", ["lisbon", "porto", "rome"])
    planner.move_cities("coast", "lakes", ["lisbon", "porto"])
    assert planner.get_cities("coast") == ["lyon"]
    assert planner.get_cities("lakes") == ["geneva", "milan", "lisbon", "porto"]
