"""Public checks for the c_size_table change (adjustable sizes and fees).
Shown to the editor, never to the writer.

Usage (with lockers.py importable, e.g. in the sandbox):
    python -m pytest changes/c_size_table/public/test_size_table_public.py
"""

import pytest
from lockers import LockerRoom


def test_table_defaults_to_the_three_sizes():
    r = LockerRoom()
    assert r.get_sizes() == ["small", "medium", "large"]
    r.add_locker("M1", "medium")
    assert r.get_fee("M1") == 300


def test_table_of_my_own_sizes():
    r = LockerRoom(size_table={"s": 100, "m": 250, "l": 400})
    r.add_locker("L1", "l")
    r.add_locker("S1", "s")
    assert r.store("coat", "m") == "L1"
    assert r.get_takings() == 400
    with pytest.raises(ValueError):
        r.add_locker("X1", "small")


def test_table_fee_for_one_locker():
    r = LockerRoom()
    r.add_locker("S1", "small", fee=50)
    r.store("hat", "small")
    assert r.get_fee("S1") == 50
    assert r.get_takings() == 50
