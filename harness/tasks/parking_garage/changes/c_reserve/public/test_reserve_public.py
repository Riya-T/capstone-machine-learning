"""Public checks for the c_reserve change (reserved spots). Shown to the
editor, never to the writer.

Usage (with garage.py importable, e.g. in the sandbox):
    python -m pytest changes/c_reserve/public/test_reserve_public.py
"""

import pytest
from garage import Garage


def test_a_reserved_spot_is_not_free_for_others():
    gar = Garage()
    gar.add_level("P1", 1)
    gar.add_level("P2", 1)
    gar.reserve("P1", "AAA")
    assert gar.get_free_spots("P1") == 0
    assert gar.has_reservation("AAA")
    assert gar.get_reserved("P1") == ["AAA"]
    assert gar.enter("BBB", 1) == "P2"


def test_the_reserved_vehicle_parks_on_its_level():
    gar = Garage()
    gar.add_level("P1", 2)
    gar.add_level("P2", 1)
    gar.reserve("P2", "AAA")
    assert gar.enter("AAA", 1) == "P2"
    assert not gar.has_reservation("AAA")
    assert gar.get_reserved("P2") == []
    assert gar.get_free_spots("P2") == 0
    assert gar.get_vehicles("P2") == ["AAA"]


def test_cancelling_makes_the_spot_free_again():
    gar = Garage()
    gar.add_level("P1", 1)
    gar.reserve("P1", "AAA")
    gar.cancel_reservation("AAA")
    assert gar.get_free_spots("P1") == 1
    assert not gar.has_reservation("AAA")
    with pytest.raises(KeyError):
        gar.cancel_reservation("AAA")
