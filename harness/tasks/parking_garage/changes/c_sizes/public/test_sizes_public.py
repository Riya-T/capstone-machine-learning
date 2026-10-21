"""Public checks for the c_sizes change (vehicle and level sizes). Shown to
the editor, never to the writer.

Usage (with garage.py importable, e.g. in the sandbox):
    python -m pytest changes/c_sizes/public/test_sizes_public.py
"""

import pytest
from garage import Garage


def test_large_vehicles_skip_levels_that_are_too_small():
    gar = Garage()
    gar.add_level("P1", 2, max_size="small")
    gar.add_level("P2", 2)
    assert gar.enter("AAA", 1, size="large") == "P2"
    assert gar.get_free_spots("P1") == 2
    assert gar.get_max_size("P1") == "small"
    assert gar.get_size("AAA") == "large"


def test_the_defaults_are_a_large_level_and_a_medium_vehicle():
    gar = Garage()
    gar.add_level("P1", 1)
    assert gar.enter("AAA", 1) == "P1"
    assert gar.get_max_size("P1") == "large"
    assert gar.get_size("AAA") == "medium"


def test_unknown_sizes_are_rejected():
    gar = Garage()
    with pytest.raises(ValueError):
        gar.add_level("P1", 1, max_size="huge")
    assert gar.get_levels() == []
    gar.add_level("P1", 1)
    with pytest.raises(ValueError):
        gar.enter("AAA", 1, size="tiny")
    assert gar.get_free_spots("P1") == 1
