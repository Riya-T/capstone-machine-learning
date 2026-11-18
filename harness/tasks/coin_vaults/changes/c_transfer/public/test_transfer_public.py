"""Public checks for the c_transfer change (atomic_operation). Shown to the
editor, never to the writer.

Usage (with vaults.py importable, e.g. in the sandbox):
    python -m pytest changes/c_transfer/public/test_transfer_public.py
"""

import pytest
from vaults import NotEnoughCoins, Vaults


@pytest.fixture
def vaults():
    v = Vaults()
    v.add_vault("till")
    v.add_vault("safe")
    v.deposit("till", 50, 4)
    v.deposit("till", 10, 3)
    return v


def test_transfer_makes_every_move_and_returns_the_total(vaults):
    assert vaults.transfer([("till", "safe", 50, 2), ("till", "safe", 10, 3)]) == 5
    assert vaults.get_count("till", 50) == 2
    assert vaults.get_denominations("till") == [50]
    assert vaults.get_denominations("safe") == [10, 50]


def test_a_failing_move_cancels_the_whole_transfer(vaults):
    with pytest.raises(NotEnoughCoins):
        vaults.transfer([("till", "safe", 50, 2), ("till", "safe", 10, 9)])
    assert vaults.get_count("till", 50) == 4
    assert vaults.get_denominations("safe") == []
