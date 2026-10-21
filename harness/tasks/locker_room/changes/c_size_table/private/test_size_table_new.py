"""Hidden tests for the c_size_table change (adjustable sizes and fees).
Never shown to the writer or the editor.

Usage (with lockers.py importable, e.g. in the sandbox):
    python -m pytest changes/c_size_table/private/test_size_table_new.py
"""

import pytest
from lockers import LockerError, LockerRoom, NoLockerFree

FIVE = {"xs": 100, "s": 150, "m": 250, "l": 400, "xl": 600}
BAD_FEES = [-1, 2.5, "100", True]


def test_table_names_are_listed_smallest_first():
    assert LockerRoom(size_table=FIVE).get_sizes() == ["xs", "s", "m", "l", "xl"]
    assert LockerRoom(size_table={"only": 0}).get_sizes() == ["only"]


def test_table_order_decides_what_fits():
    r = LockerRoom(size_table=FIVE)
    for locker_id, size in [("XL1", "xl"), ("M1", "m"), ("S1", "s"), ("L1", "l")]:
        r.add_locker(locker_id, size)
    assert r.store("pen", "xs") == "S1"
    assert r.store("cup", "s") == "M1"
    assert r.store("bag", "m") == "L1"
    assert r.store("rug", "s") == "XL1"
    assert r.get_takings() == 150 + 250 + 400 + 600
    with pytest.raises(NoLockerFree):
        r.store("box", "xs")


def test_table_order_need_not_be_alphabetical():
    r = LockerRoom(size_table={"zeta": 10, "alpha": 20})
    r.add_locker("A", "alpha")
    r.add_locker("Z", "zeta")
    assert r.store("one", "zeta") == "Z"
    assert r.store("two", "zeta") == "A"
    with pytest.raises(NoLockerFree):
        r.store("three", "alpha")


def test_table_fees_need_not_grow_with_size():
    r = LockerRoom(size_table={"small": 500, "large": 0})
    r.add_locker("L1", "large")
    r.add_locker("S1", "small")
    r.store("hat", "small")
    r.store("box", "small")
    assert r.get_takings() == 500
    assert (r.get_fee("S1"), r.get_fee("L1")) == (500, 0)


def test_table_without_the_old_sizes_rejects_them():
    r = LockerRoom(size_table={"cubby": 75})
    with pytest.raises(ValueError):
        r.add_locker("C1", "small")
    r.add_locker("C1", "cubby")
    with pytest.raises(ValueError):
        r.store("hat", "large")
    assert r.get_free_lockers() == ["C1"]
    assert r.get_takings() == 0


@pytest.mark.parametrize(
    "table",
    [
        {},
        [("small", 200)],
        "small",
        {"": 100},
        {1: 100},
        {"small": -1},
        {"small": 1.5},
        {"small": "200"},
        {"small": True},
        {"small": None},
    ],
)
def test_table_must_be_valid(table):
    with pytest.raises(ValueError):
        LockerRoom(size_table=table)


def test_table_fee_of_one_locker_is_charged_instead_of_the_table():
    r = LockerRoom()
    r.add_locker("S1", "small", fee=0)
    r.add_locker("S2", "small", fee=None)
    r.add_locker("M1", "medium", fee=1000)
    r.store("a", "small")
    r.store("b", "small")
    r.store("c", "small")
    assert r.get_takings() == 0 + 200 + 1000
    assert [r.get_fee(x) for x in ["S1", "S2", "M1"]] == [0, 200, 1000]


@pytest.mark.parametrize("fee", BAD_FEES)
def test_table_fee_of_one_locker_must_be_valid(fee):
    r = LockerRoom()
    with pytest.raises(ValueError):
        r.add_locker("S1", "small", fee=fee)
    assert r.get_free_lockers() == []
    with pytest.raises(KeyError):
        r.get_fee("S1")


def test_table_errors_of_add_locker_come_in_order():
    r = LockerRoom()
    r.add_locker("S1", "small", fee=10)
    with pytest.raises(ValueError):
        r.add_locker("S1", "small", fee=-5)
    with pytest.raises(LockerError):
        r.add_locker("S1", "large", fee=99)
    assert r.get_fee("S1") == 10
    assert r.get_free_lockers() == ["S1"]


@pytest.mark.parametrize("locker_id", ["Q7", None, 1])
def test_table_fee_needs_a_known_locker(locker_id):
    r = LockerRoom()
    r.add_locker("S1", "small")
    with pytest.raises(KeyError):
        r.get_fee(locker_id)


def test_table_of_one_room_does_not_affect_another():
    first = LockerRoom(size_table={"box": 1})
    second = LockerRoom()
    assert second.get_sizes() == ["small", "medium", "large"]
    second.add_locker("S1", "small")
    assert second.get_fee("S1") == 200
    assert first.get_sizes() == ["box"]
