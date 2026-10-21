"""Public checks for the c_report change (usage figures). Shown to the
editor, never to the writer.

Usage (with garage.py importable, e.g. in the sandbox):
    python -m pytest changes/c_report/public/test_report_public.py
"""

from garage import Garage


def test_the_report_counts_parked_vehicles_and_completed_stays():
    gar = Garage()
    gar.add_level("P1", 2)
    gar.add_level("P2", 1)
    gar.enter("AAA", 0)
    gar.enter("BBB", 10)
    gar.enter("CCC", 20)
    gar.leave("AAA", 30)
    assert gar.get_report() == [("P1", 1, 1, 30), ("P2", 1, 0, 0)]


def test_peak_is_the_most_vehicles_parked_at_once():
    gar = Garage()
    gar.add_level("P1", 3)
    gar.add_level("P2", 1)
    gar.enter("AAA", 0)
    gar.enter("BBB", 1)
    gar.leave("AAA", 2)
    gar.leave("BBB", 3)
    gar.enter("CCC", 4)
    assert gar.get_peak("P1") == 2
    assert gar.get_peak("P2") == 0


def test_an_unused_garage_reports_zeros():
    gar = Garage()
    gar.add_level("P1", 2)
    gar.add_level("P2", 1)
    assert gar.get_report() == [("P1", 0, 0, 0), ("P2", 0, 0, 0)]
