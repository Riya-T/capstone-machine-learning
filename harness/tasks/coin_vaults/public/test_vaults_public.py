"""Public checks for vaults.py.

Usage (with vaults.py importable, e.g. in the sandbox):
    python -m pytest public/test_vaults_public.py
"""

import pytest
from vaults import NotEnoughCoins, Vaults


@pytest.fixture
def vaults():
    v = Vaults()
    v.add_vault("till")
    v.add_vault("safe")
    return v


def test_deposits_and_withdrawals_change_the_count(vaults):
    vaults.deposit("till", 50, 5)
    vaults.deposit("till", 50, 2)
    vaults.withdraw("till", 50, 3)
    assert vaults.get_count("till", 50) == 4
    assert vaults.get_count("till", 10) == 0


def test_withdrawing_more_than_the_vault_holds_raises(vaults):
    vaults.deposit("till", 20, 5)
    with pytest.raises(NotEnoughCoins):
        vaults.withdraw("till", 20, 6)
    assert vaults.get_count("till", 20) == 5


def test_a_denomination_that_is_not_accepted_is_rejected(vaults):
    with pytest.raises(ValueError):
        vaults.deposit("till", 3, 1)
    assert vaults.get_denominations("till") == []


def test_consolidate_moves_every_denomination_and_returns_how_many(vaults):
    vaults.deposit("till", 50, 4)
    vaults.deposit("till", 10, 3)
    vaults.deposit("safe", 50, 1)
    assert vaults.consolidate("till", "safe") == 7
    assert vaults.get_denominations("till") == []
    assert vaults.get_denominations("safe") == [10, 50]
    assert vaults.get_count("safe", 50) == 5
    assert vaults.get_vaults() == ["till", "safe"]


def test_a_closed_vault_is_gone(vaults):
    vaults.deposit("till", 100, 2)
    vaults.deposit("safe", 100, 1)
    assert vaults.close_vault("till", "safe") == 2
    assert vaults.get_vaults() == ["safe"]
    assert vaults.get_count("safe", 100) == 3
    with pytest.raises(KeyError):
        vaults.get_count("till", 100)
    with pytest.raises(KeyError):
        vaults.deposit("till", 100, 1)


def test_closing_an_empty_vault_returns_0(vaults):
    vaults.deposit("till", 5, 2)
    assert vaults.close_vault("safe", "till") == 0
    assert vaults.get_vaults() == ["till"]
    assert vaults.get_count("till", 5) == 2
