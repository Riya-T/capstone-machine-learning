"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with tours.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
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
    return p  # 11 calls


def state(p):
    return [(t, p.get_cities(t)) for t in p.get_tours()]


# --- each call can be undone --------------------------------------------------


def test_undo_of_add_city(planner):
    before = state(planner)
    planner.add_city("lakes", "lyon")
    planner.undo()
    assert state(planner) == before
    planner.add_city("lakes", "lyon")
    assert planner.get_cities("lakes") == ["geneva", "milan", "lyon"]


def test_undo_of_remove_city_puts_it_back_in_place(planner):
    before = state(planner)
    planner.remove_city("coast", "porto")
    planner.undo()
    assert state(planner) == before
    assert planner.get_cities("coast") == ["lisbon", "porto", "lyon"]


def test_undo_of_removing_the_first_city(planner):
    before = state(planner)
    planner.remove_city("alps", "zurich")
    planner.undo()
    assert state(planner) == before


def test_a_city_put_back_is_on_the_tour_again(planner):
    planner.remove_city("coast", "porto")
    planner.undo()
    with pytest.raises(TourError):
        planner.add_city("coast", "porto")
    planner.remove_city("coast", "porto")
    assert planner.get_cities("coast") == ["lisbon", "lyon"]


def test_undo_of_cancel_city_restores_every_tour(planner):
    before = state(planner)
    assert planner.cancel_city("lyon") == 2
    planner.undo()
    assert state(planner) == before
    assert planner.get_cities("coast") == ["lisbon", "porto", "lyon"]
    assert planner.get_cities("alps") == ["zurich", "lyon", "milan"]


def test_undo_of_cancel_city_that_emptied_a_tour(planner):
    planner.remove_city("lakes", "geneva")
    before = state(planner)
    assert planner.cancel_city("milan") == 2
    planner.undo()
    assert state(planner) == before
    assert planner.get_cities("lakes") == ["milan"]


def test_undo_of_merge_tours_brings_second_back(planner):
    before = state(planner)
    assert planner.merge_tours("coast", "alps") == 2
    planner.undo()
    assert state(planner) == before
    assert planner.get_tours() == ["coast", "alps", "lakes"]
    assert planner.get_cities("coast") == ["lisbon", "porto", "lyon"]


def test_undo_of_merge_tours_keeps_second_in_its_place(planner):
    planner.add_tour("nordic")
    planner.add_city("nordic", "oslo")
    before = state(planner)
    planner.merge_tours("nordic", "coast")
    assert planner.get_tours() == ["alps", "lakes", "nordic"]
    planner.undo()
    assert planner.get_tours() == ["coast", "alps", "lakes", "nordic"]
    assert state(planner) == before


def test_undo_of_a_merge_that_added_nothing(planner):
    planner.add_tour("nordic")
    planner.add_city("nordic", "milan")
    before = state(planner)
    assert planner.merge_tours("lakes", "nordic") == 0
    planner.undo()
    assert state(planner) == before
    assert planner.get_cities("nordic") == ["milan"]


def test_a_tour_brought_back_is_in_use_again(planner):
    planner.merge_tours("alps", "lakes")
    planner.undo()
    with pytest.raises(TourError):
        planner.add_tour("lakes")
    planner.add_city("lakes", "como")
    assert planner.get_cities("lakes") == ["geneva", "milan", "como"]
    assert planner.merge_tours("coast", "lakes") == 3
    assert planner.get_tours() == ["coast", "alps"]


def test_undo_of_add_tour_removes_it_and_frees_the_name(planner):
    planner.add_tour("nordic")
    planner.undo()
    assert planner.get_tours() == ["coast", "alps", "lakes"]
    with pytest.raises(KeyError):
        planner.get_cities("nordic")
    planner.add_tour("nordic")
    assert planner.get_tours() == ["coast", "alps", "lakes", "nordic"]


def test_undo_through_a_name_that_was_merged_and_added_again(planner):
    planner.merge_tours("alps", "lakes")
    planner.add_tour("lakes")  # a new lakes with no cities
    planner.add_city("lakes", "como")
    planner.undo()  # como
    planner.undo()  # the new lakes
    assert planner.get_tours() == ["coast", "alps"]
    planner.undo()  # the merge: the old lakes comes back
    assert planner.get_tours() == ["coast", "alps", "lakes"]
    assert planner.get_cities("lakes") == ["geneva", "milan"]
    assert planner.get_cities("alps") == ["zurich", "lyon", "milan"]


# --- what is and is not recorded ----------------------------------------------


def test_each_undo_goes_one_call_further_back():
    p = TourPlanner()
    calls = [
        lambda: p.add_tour("coast"),
        lambda: p.add_tour("alps"),
        lambda: p.add_city("coast", "lisbon"),
        lambda: p.add_city("coast", "lyon"),
        lambda: p.add_city("alps", "lyon"),
        lambda: p.add_city("coast", "porto"),
        lambda: p.add_tour("lakes"),
        lambda: p.add_city("lakes", "milan"),
        lambda: p.add_city("alps", "milan"),
        lambda: p.remove_city("coast", "lisbon"),
        lambda: p.cancel_city("lyon"),
        lambda: p.add_city("coast", "lyon"),
        lambda: p.merge_tours("lakes", "coast"),
        lambda: p.add_city("lakes", "geneva"),
        lambda: p.merge_tours("alps", "lakes"),
        lambda: p.add_tour("coast"),
    ]
    states = [state(p)]
    for call in calls:
        call()
        states.append(state(p))
    assert p.get_tours() == ["alps", "coast"]
    assert p.get_cities("alps") == ["milan", "porto", "lyon", "geneva"]
    for expected in reversed(states[:-1]):
        p.undo()
        assert state(p) == expected
    with pytest.raises(TourError):
        p.undo()
    assert p.get_tours() == []


def test_failed_calls_are_not_recorded(planner):
    planner.add_city("lakes", "como")
    for call in (
        lambda: planner.add_tour("coast"),
        lambda: planner.add_city("coast", "porto"),
        lambda: planner.add_city("nordic", "oslo"),
        lambda: planner.remove_city("lakes", "lyon"),
        lambda: planner.merge_tours("alps", "alps"),
        lambda: planner.merge_tours("nordic", "alps"),
    ):
        with pytest.raises((KeyError, ValueError, TourError)):
            call()
    planner.undo()  # como
    assert planner.get_cities("lakes") == ["geneva", "milan"]
    assert planner.get_cities("coast") == ["lisbon", "porto", "lyon"]


def test_get_calls_are_not_recorded(planner):
    planner.remove_city("alps", "milan")
    planner.get_cities("alps")
    planner.get_tours()
    planner.undo()
    assert planner.get_cities("alps") == ["zurich", "lyon", "milan"]
    assert planner.get_cities("lakes") == ["geneva", "milan"]


def test_there_is_no_redo():
    p = TourPlanner()
    p.add_tour("coast")
    p.add_city("coast", "lisbon")
    p.undo()
    p.undo()
    assert p.get_tours() == []
    with pytest.raises(TourError):
        p.undo()


def test_new_calls_after_an_undo_are_undone_first(planner):
    planner.cancel_city("milan")
    planner.undo()
    planner.remove_city("coast", "lyon")
    planner.undo()
    assert planner.get_cities("coast") == ["lisbon", "porto", "lyon"]
    planner.undo()  # milan on lakes, from the fixture
    assert planner.get_cities("lakes") == ["geneva"]
    assert planner.get_cities("alps") == ["zurich", "lyon", "milan"]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    p = TourPlanner()
    with pytest.raises(TourError):
        p.undo()
    p.add_tour("coast")
    p.undo()
    with pytest.raises(TourError):
        p.undo()
    assert p.get_tours() == []
    p.add_tour("coast")
    p.add_city("coast", "lisbon")
    assert p.get_cities("coast") == ["lisbon"]


def test_the_whole_fixture_can_be_undone(planner):
    for _ in range(11):
        planner.undo()
    assert planner.get_tours() == []
    with pytest.raises(TourError):
        planner.undo()
