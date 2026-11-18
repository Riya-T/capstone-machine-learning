"""Hidden tests for the c_capacity change (validation_rule). Never shown to
the writer or the editor.

Usage (with vaults.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/private/test_capacity_new.py
"""

import pytest
from vaults import VaultError, VaultFull, Vaults


@pytest.fixture
def vaults():
    v = Vaults()
    v.add_vault("till", capacity=10)
    v.add_vault("safe")
    v.add_vault("bank", capacity=8)
    v.deposit("till", 50, 4)
    v.deposit("till", 10, 2)
    v.deposit("safe", 100, 5)
    return v


def state(v):
    return [(n, [(d, v.get_count(n, d)) for d in v.get_denominations(n)]) for n in v.get_vaults()]


# --- the capacity setting ---------------------------------------------------


def test_vaults_have_no_limit_by_default():
    v = Vaults()
    v.add_vault("till")
    assert v.get_capacity("till") is None
    v.deposit("till", 1, 5000)
    assert v.get_count("till", 1) == 5000


def test_capacity_can_be_none_explicitly():
    v = Vaults()
    v.add_vault("till", capacity=None)
    assert v.get_capacity("till") is None


def test_capacities_are_reported_per_vault(vaults):
    assert vaults.get_capacity("till") == 10
    assert vaults.get_capacity("safe") is None
    assert vaults.get_capacity("bank") == 8


@pytest.mark.parametrize("capacity", [0, -5])
def test_a_capacity_of_0_or_less_is_rejected(vaults, capacity):
    before = state(vaults)
    with pytest.raises(ValueError):
        vaults.add_vault("cellar", capacity=capacity)
    assert state(vaults) == before
    assert vaults.get_vaults() == ["till", "safe", "bank"]


def test_get_capacity_of_a_vault_not_in_use_raises(vaults):
    with pytest.raises(KeyError):
        vaults.get_capacity("cellar")
    vaults.close_vault("bank", "safe")
    with pytest.raises(KeyError):
        vaults.get_capacity("bank")


def test_vault_full_is_a_vault_error():
    assert issubclass(VaultFull, VaultError)


# --- deposits ---------------------------------------------------------------


def test_every_denomination_counts_against_the_capacity(vaults):
    vaults.deposit("till", 1, 4)
    assert vaults.get_count("till", 1) == 4
    with pytest.raises(VaultFull):
        vaults.deposit("till", 200, 1)


def test_a_deposit_over_the_capacity_changes_nothing(vaults):
    before = state(vaults)
    with pytest.raises(VaultFull):
        vaults.deposit("till", 50, 5)
    with pytest.raises(VaultFull):
        vaults.deposit("bank", 5, 9)
    assert state(vaults) == before


def test_coins_withdrawn_make_room_again(vaults):
    vaults.deposit("till", 5, 4)
    vaults.withdraw("till", 50, 3)
    vaults.deposit("till", 5, 3)
    assert vaults.get_count("till", 5) == 7
    with pytest.raises(VaultFull):
        vaults.deposit("till", 5, 1)


def test_withdraw_is_never_refused_for_capacity(vaults):
    vaults.deposit("till", 5, 4)
    vaults.withdraw("till", 5, 4)
    vaults.withdraw("till", 50, 4)
    assert vaults.get_denominations("till") == [10]


# --- consolidating and closing ----------------------------------------------


def test_consolidate_into_a_vault_with_room(vaults):
    assert vaults.consolidate("till", "bank") == 6
    assert vaults.get_count("bank", 50) == 4
    assert vaults.get_denominations("till") == []


def test_consolidate_may_fill_a_vault_exactly(vaults):
    vaults.deposit("bank", 1, 2)
    assert vaults.consolidate("till", "bank") == 6
    assert vaults.get_count("bank", 1) == 2


def test_consolidate_over_the_capacity_moves_nothing(vaults):
    vaults.deposit("bank", 1, 3)
    before = state(vaults)
    with pytest.raises(VaultFull):
        vaults.consolidate("till", "bank")
    with pytest.raises(VaultFull):
        vaults.consolidate("safe", "till")
    assert state(vaults) == before


def test_the_vault_the_coins_leave_is_not_checked(vaults):
    assert vaults.consolidate("till", "safe") == 6
    assert vaults.get_count("safe", 50) == 4


def test_close_vault_into_a_vault_with_room(vaults):
    assert vaults.close_vault("till", "bank") == 6
    assert vaults.get_vaults() == ["safe", "bank"]
    assert vaults.get_count("bank", 10) == 2


def test_close_vault_over_the_capacity_does_not_close(vaults):
    before = state(vaults)
    with pytest.raises(VaultFull):
        vaults.close_vault("safe", "till")
    assert state(vaults) == before
    assert vaults.get_vaults() == ["till", "safe", "bank"]


def test_closing_an_empty_vault_into_a_full_vault_is_allowed(vaults):
    vaults.deposit("till", 1, 4)
    assert vaults.close_vault("bank", "till") == 0
    assert vaults.get_vaults() == ["till", "safe"]
