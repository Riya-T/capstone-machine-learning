"""Hidden tests for the initial tour_itineraries spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with tours.py importable, e.g. in the sandbox):
    python -m pytest private/test_tours_initial.py
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
    """Every tour in order with its cities in order, to check that a failed
    call changed nothing."""
    return [(t, p.get_cities(t)) for t in p.get_tours()]


FIXTURE = [
    ("coast", ["lisbon", "porto", "lyon"]),
    ("alps", ["zurich", "lyon", "milan"]),
    ("lakes", ["geneva", "milan"]),
]


# --- tours --------------------------------------------------------------------


def test_a_new_planner_has_no_tours():
    assert TourPlanner().get_tours() == []


def test_a_new_tour_has_no_cities():
    p = TourPlanner()
    p.add_tour("coast")
    assert p.get_cities("coast") == []


def test_tours_are_listed_in_the_order_added():
    p = TourPlanner()
    for name in ["lakes", "coast", "alps"]:
        p.add_tour(name)
    assert p.get_tours() == ["lakes", "coast", "alps"]


def test_adding_a_name_in_use_is_rejected(planner):
    with pytest.raises(TourError):
        planner.add_tour("alps")
    assert state(planner) == FIXTURE


NOT_IN_USE = [
    lambda p, t: p.add_city(t, "rome"),
    lambda p, t: p.remove_city(t, "milan"),
    lambda p, t: p.merge_tours(t, "coast"),
    lambda p, t: p.merge_tours("coast", t),
    lambda p, t: p.get_cities(t),
]


@pytest.mark.parametrize("call", NOT_IN_USE)
def test_tours_that_were_never_added_raise_key_error(planner, call):
    with pytest.raises(KeyError):
        call(planner, "nordic")
    assert state(planner) == FIXTURE


@pytest.mark.parametrize("call", NOT_IN_USE)
def test_a_merged_tour_is_not_in_use(planner, call):
    planner.merge_tours("alps", "lakes")
    before = state(planner)
    with pytest.raises(KeyError):
        call(planner, "lakes")
    assert state(planner) == before


def test_a_merged_name_can_be_added_again_as_a_new_tour(planner):
    planner.merge_tours("coast", "lakes")
    planner.add_tour("lakes")
    assert planner.get_tours() == ["coast", "alps", "lakes"]
    assert planner.get_cities("lakes") == []
    assert planner.get_cities("coast") == ["lisbon", "porto", "lyon", "geneva", "milan"]


# --- adding and removing cities -----------------------------------------------


def test_cities_are_listed_in_the_order_added(planner):
    assert state(planner) == FIXTURE


def test_the_same_city_can_be_on_several_tours(planner):
    planner.add_city("lakes", "lyon")
    assert planner.get_cities("lakes") == ["geneva", "milan", "lyon"]
    assert planner.get_cities("coast") == ["lisbon", "porto", "lyon"]


def test_adding_a_city_already_on_the_tour_is_rejected(planner):
    with pytest.raises(TourError):
        planner.add_city("alps", "zurich")
    with pytest.raises(TourError):
        planner.add_city("alps", "milan")
    assert state(planner) == FIXTURE


def test_remove_city_keeps_the_order_of_the_others(planner):
    planner.remove_city("alps", "lyon")
    assert planner.get_cities("alps") == ["zurich", "milan"]
    assert planner.get_cities("coast") == ["lisbon", "porto", "lyon"]
    planner.remove_city("alps", "zurich")
    assert planner.get_cities("alps") == ["milan"]


def test_removing_a_city_not_on_the_tour_is_rejected(planner):
    with pytest.raises(TourError):
        planner.remove_city("lakes", "lyon")
    with pytest.raises(TourError):
        planner.remove_city("coast", "rome")
    assert state(planner) == FIXTURE


def test_a_removed_city_can_be_added_again_at_the_end(planner):
    planner.remove_city("coast", "lisbon")
    planner.add_city("coast", "lisbon")
    assert planner.get_cities("coast") == ["porto", "lyon", "lisbon"]


def test_the_last_city_of_a_tour_can_be_removed(planner):
    planner.remove_city("lakes", "geneva")
    planner.remove_city("lakes", "milan")
    assert planner.get_cities("lakes") == []
    assert planner.get_tours() == ["coast", "alps", "lakes"]


# --- cancelling a city --------------------------------------------------------


def test_cancel_city_removes_it_from_every_tour_that_has_it(planner):
    assert planner.cancel_city("milan") == 2
    assert state(planner) == [
        ("coast", ["lisbon", "porto", "lyon"]),
        ("alps", ["zurich", "lyon"]),
        ("lakes", ["geneva"]),
    ]


def test_cancel_city_keeps_the_order_of_the_other_cities(planner):
    assert planner.cancel_city("lyon") == 2
    assert planner.get_cities("coast") == ["lisbon", "porto"]
    assert planner.get_cities("alps") == ["zurich", "milan"]


def test_cancel_city_on_one_tour(planner):
    assert planner.cancel_city("porto") == 1
    assert planner.get_cities("coast") == ["lisbon", "lyon"]


def test_cancelling_a_city_on_no_tour_changes_nothing(planner):
    assert planner.cancel_city("rome") == 0
    assert state(planner) == FIXTURE


def test_a_cancelled_city_can_be_added_again(planner):
    planner.cancel_city("lyon")
    planner.add_city("alps", "lyon")
    assert planner.get_cities("alps") == ["zurich", "milan", "lyon"]
    assert planner.get_cities("coast") == ["lisbon", "porto"]


# --- merging tours ------------------------------------------------------------


def test_merge_appends_the_new_cities_in_order_and_removes_second(planner):
    assert planner.merge_tours("coast", "alps") == 2
    assert state(planner) == [
        ("coast", ["lisbon", "porto", "lyon", "zurich", "milan"]),
        ("lakes", ["geneva", "milan"]),
    ]


def test_merge_skips_cities_first_already_has(planner):
    assert planner.merge_tours("alps", "lakes") == 1
    assert planner.get_cities("alps") == ["zurich", "lyon", "milan", "geneva"]
    assert planner.get_tours() == ["coast", "alps"]


def test_merge_into_an_empty_tour(planner):
    planner.add_tour("nordic")
    assert planner.merge_tours("nordic", "lakes") == 2
    assert planner.get_cities("nordic") == ["geneva", "milan"]
    assert planner.get_tours() == ["coast", "alps", "nordic"]


def test_merging_an_empty_tour_adds_nothing(planner):
    planner.add_tour("nordic")
    assert planner.merge_tours("coast", "nordic") == 0
    assert state(planner) == FIXTURE


def test_merging_a_tour_whose_cities_first_all_has(planner):
    planner.add_tour("nordic")
    planner.add_city("nordic", "lyon")
    planner.add_city("nordic", "lisbon")
    assert planner.merge_tours("coast", "nordic") == 0
    assert state(planner) == FIXTURE


def test_the_other_tours_keep_their_order_after_a_merge(planner):
    planner.merge_tours("lakes", "coast")
    assert planner.get_tours() == ["alps", "lakes"]
    assert planner.get_cities("lakes") == ["geneva", "milan", "lisbon", "porto", "lyon"]


def test_merging_a_tour_into_itself_is_rejected(planner):
    with pytest.raises(ValueError):
        planner.merge_tours("alps", "alps")
    assert state(planner) == FIXTURE


# --- general ------------------------------------------------------------------


def test_planners_do_not_share_tours():
    first, second = TourPlanner(), TourPlanner()
    first.add_tour("coast")
    first.add_city("coast", "lisbon")
    assert second.get_tours() == []
    second.add_tour("coast")
    assert second.get_cities("coast") == []
    assert second.cancel_city("lisbon") == 0
    assert first.get_cities("coast") == ["lisbon"]
