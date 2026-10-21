"""Hidden tests for the c_report change (usage figures). Never shown to the
writer or the editor.

Usage (with garage.py importable, e.g. in the sandbox):
    python -m pytest changes/c_report/private/test_report_new.py
"""

import pytest
from garage import Garage, GarageFull


@pytest.fixture
def garage():
    gar = Garage()
    gar.add_level("P1", 2)
    gar.add_level("P2", 1)
    gar.add_level("P3", 3)
    return gar


def test_the_report_lists_every_level_in_the_order_added(garage):
    assert [row[0] for row in garage.get_report()] == ["P1", "P2", "P3"]
    assert garage.get_report() == [("P1", 0, 0, 0), ("P2", 0, 0, 0), ("P3", 0, 0, 0)]


def test_minutes_add_up_over_the_stays_on_a_level(garage):
    garage.enter("AAA", 0)
    garage.enter("BBB", 5)
    garage.leave("AAA", 30)
    garage.leave("BBB", 50)
    assert garage.get_report()[0] == ("P1", 0, 2, 75)


def test_a_stay_counts_for_the_level_the_vehicle_was_parked_on(garage):
    garage.enter("AAA", 0)
    garage.enter("BBB", 0)
    garage.enter("CCC", 10)  # P2
    garage.leave("CCC", 25)
    assert garage.get_report() == [("P1", 2, 0, 0), ("P2", 0, 1, 15), ("P3", 0, 0, 0)]


def test_a_returning_vehicle_counts_one_stay_per_visit(garage):
    garage.enter("AAA", 0)
    garage.leave("AAA", 10)
    garage.enter("AAA", 20)
    garage.leave("AAA", 25)
    assert garage.get_report()[0] == ("P1", 0, 2, 15)


def test_a_zero_minute_stay_still_counts(garage):
    garage.enter("AAA", 7)
    garage.leave("AAA", 7)
    assert garage.get_report()[0] == ("P1", 0, 1, 0)


def test_parked_follows_the_vehicles_on_the_level_now(garage):
    garage.enter("AAA", 0)
    garage.enter("BBB", 0)
    assert garage.get_report()[0][1] == 2
    garage.leave("BBB", 1)
    assert garage.get_report()[0][1] == 1


def test_peak_grows_only_when_vehicles_overlap(garage):
    garage.enter("AAA", 0)
    garage.leave("AAA", 1)
    garage.enter("BBB", 2)
    garage.leave("BBB", 3)
    assert garage.get_peak("P1") == 1
    garage.enter("CCC", 4)
    garage.enter("DDD", 5)
    assert garage.get_peak("P1") == 2
    assert garage.get_peak("P2") == 0


def test_peak_never_goes_down(garage):
    garage.enter("AAA", 0)
    garage.enter("BBB", 0)
    garage.leave("AAA", 1)
    garage.leave("BBB", 1)
    assert garage.get_peak("P1") == 2
    assert garage.get_report()[0][1] == 0


def test_peak_is_tracked_per_level(garage):
    garage.enter("AAA", 0)
    garage.enter("BBB", 0)
    garage.enter("CCC", 0)  # P2
    garage.enter("DDD", 0)  # P3
    garage.leave("CCC", 1)
    assert (garage.get_peak("P1"), garage.get_peak("P2"), garage.get_peak("P3")) == (2, 1, 1)


@pytest.mark.parametrize("level_id", ["P9", None, 1])
def test_peak_of_a_missing_level_raises_key_error(garage, level_id):
    with pytest.raises(KeyError):
        garage.get_peak(level_id)


def test_failed_calls_change_no_figure():
    gar = Garage()
    gar.add_level("P1", 1)
    gar.enter("AAA", 10)
    report, peak = gar.get_report(), gar.get_peak("P1")
    for call in (
        lambda: gar.enter("BBB", 11),
        lambda: gar.enter("", 11),
        lambda: gar.leave("AAA", 5),
        lambda: gar.leave("ZZZ", 20),
    ):
        with pytest.raises((GarageFull, ValueError, KeyError)):
            call()
    assert gar.get_report() == report == [("P1", 1, 0, 0)]
    assert gar.get_peak("P1") == peak == 1
