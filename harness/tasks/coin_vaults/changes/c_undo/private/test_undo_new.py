"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with vaults.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
"""

import pytest
from vaults import NotEnoughCoins, VaultError, Vaults


@pytest.fixture
def vaults():
    v = Vaults()
    for name in ["till", "safe", "bank"]:
        v.add_vault(name)
    v.deposit("till", 50, 3)
    v.deposit("till", 10, 2)
    v.deposit("safe", 100, 4)
    return v


def state(v):
    return [(n, [(d, v.get_count(n, d)) for d in v.get_denominations(n)]) for n in v.get_vaults()]


# --- each call can be undone ------------------------------------------------


def test_undo_of_a_deposit_of_a_new_denomination(vaults):
    before = state(vaults)
    vaults.deposit("bank", 200, 2)
    vaults.undo()
    assert state(vaults) == before
    assert vaults.get_denominations("bank") == []


def test_undo_of_a_deposit_of_more_coins(vaults):
    vaults.deposit("till", 50, 5)
    vaults.undo()
    assert vaults.get_count("till", 50) == 3


def test_undo_of_a_withdrawal(vaults):
    before = state(vaults)
    vaults.withdraw("till", 50, 1)
    vaults.undo()
    assert state(vaults) == before


def test_undo_of_a_withdrawal_of_every_coin_of_a_denomination(vaults):
    before = state(vaults)
    vaults.withdraw("till", 10, 2)
    vaults.undo()
    assert state(vaults) == before
    assert vaults.get_denominations("till") == [10, 50]


def test_undo_of_consolidate_restores_both_vaults(vaults):
    before = state(vaults)
    assert vaults.consolidate("till", "safe") == 5
    vaults.undo()
    assert state(vaults) == before
    assert vaults.get_denominations("safe") == [100]


def test_undo_of_consolidate_into_an_empty_vault(vaults):
    before = state(vaults)
    vaults.consolidate("safe", "bank")
    vaults.undo()
    assert state(vaults) == before
    assert vaults.get_denominations("bank") == []


def test_undo_of_close_vault_brings_it_back_with_its_coins(vaults):
    before = state(vaults)
    assert vaults.close_vault("till", "bank") == 5
    vaults.undo()
    assert state(vaults) == before
    assert vaults.get_vaults() == ["till", "safe", "bank"]
    assert vaults.get_count("bank", 50) == 0


def test_undo_of_close_vault_keeps_its_place_in_the_list(vaults):
    vaults.add_vault("cellar")
    before = state(vaults)
    vaults.close_vault("safe", "cellar")
    assert vaults.get_vaults() == ["till", "bank", "cellar"]
    vaults.undo()
    assert vaults.get_vaults() == ["till", "safe", "bank", "cellar"]
    assert state(vaults) == before


def test_a_vault_brought_back_is_in_use_again(vaults):
    vaults.close_vault("till", "bank")
    vaults.undo()
    vaults.deposit("till", 50, 1)
    assert vaults.get_count("till", 50) == 4
    with pytest.raises(VaultError):
        vaults.add_vault("till")
    assert vaults.close_vault("till", "safe") == 6
    assert vaults.get_vaults() == ["safe", "bank"]


def test_undo_of_add_vault_removes_it_and_frees_the_name(vaults):
    vaults.add_vault("cellar")
    vaults.undo()
    assert vaults.get_vaults() == ["till", "safe", "bank"]
    with pytest.raises(KeyError):
        vaults.get_denominations("cellar")
    vaults.add_vault("cellar")
    assert vaults.get_vaults() == ["till", "safe", "bank", "cellar"]
    assert vaults.get_denominations("cellar") == []


def test_undo_of_two_closes_in_a_row(vaults):
    before = state(vaults)
    vaults.close_vault("till", "bank")
    vaults.close_vault("bank", "safe")
    assert vaults.get_vaults() == ["safe"]
    assert vaults.get_count("safe", 50) == 3
    vaults.undo()
    assert vaults.get_vaults() == ["safe", "bank"]
    assert vaults.get_count("bank", 50) == 3
    assert vaults.get_count("safe", 50) == 0
    vaults.undo()
    assert state(vaults) == before


# --- calls that move nothing ------------------------------------------------


def test_a_consolidate_of_nothing_is_still_a_call(vaults):
    vaults.deposit("bank", 5, 1)
    vaults.withdraw("bank", 5, 1)
    assert vaults.consolidate("bank", "till") == 0
    vaults.undo()  # the consolidate, which changed nothing
    assert vaults.get_denominations("bank") == []
    vaults.undo()  # the withdrawal
    assert vaults.get_count("bank", 5) == 1


def test_closing_an_empty_vault_can_be_undone(vaults):
    vaults.deposit("safe", 100, 1)
    assert vaults.close_vault("bank", "safe") == 0
    vaults.undo()
    assert vaults.get_vaults() == ["till", "safe", "bank"]
    assert vaults.get_count("safe", 100) == 5
    vaults.undo()
    assert vaults.get_count("safe", 100) == 4


# --- what is and is not recorded --------------------------------------------


def test_each_undo_goes_one_call_further_back():
    v = Vaults()
    calls = [
        lambda: v.add_vault("till"),
        lambda: v.add_vault("safe"),
        lambda: v.deposit("till", 50, 5),
        lambda: v.deposit("till", 10, 2),
        lambda: v.add_vault("bank"),
        lambda: v.deposit("safe", 100, 4),
        lambda: v.withdraw("till", 50, 1),
        lambda: v.consolidate("till", "bank"),
        lambda: v.close_vault("safe", "bank"),
        lambda: v.add_vault("cellar"),
        lambda: v.deposit("cellar", 1, 3),
        lambda: v.consolidate("bank", "cellar"),
        lambda: v.close_vault("cellar", "till"),
    ]
    states = [state(v)]
    for call in calls:
        call()
        states.append(state(v))
    assert v.get_vaults() == ["till", "bank"]
    assert v.get_count("till", 100) == 4
    assert v.get_count("till", 1) == 3
    for expected in reversed(states[:-1]):
        v.undo()
        assert state(v) == expected
    with pytest.raises(VaultError):
        v.undo()
    assert v.get_vaults() == []


def test_failed_calls_are_not_recorded(vaults):
    vaults.deposit("bank", 200, 2)
    for call in (
        lambda: vaults.withdraw("till", 50, 99),
        lambda: vaults.withdraw("till", 20, 1),
        lambda: vaults.consolidate("till", "till"),
        lambda: vaults.consolidate("till", "cellar"),
        lambda: vaults.close_vault("till", "till"),
        lambda: vaults.close_vault("cellar", "till"),
        lambda: vaults.add_vault("till"),
        lambda: vaults.deposit("cellar", 50, 1),
        lambda: vaults.deposit("till", 50, 0),
        lambda: vaults.deposit("till", 3, 1),
    ):
        with pytest.raises((ValueError, KeyError, VaultError)):
            call()
    vaults.undo()  # the deposit into bank
    assert vaults.get_denominations("bank") == []
    assert vaults.get_count("till", 50) == 3


def test_get_calls_are_not_recorded(vaults):
    vaults.deposit("bank", 200, 2)
    vaults.get_count("bank", 200)
    vaults.get_denominations("bank")
    vaults.get_vaults()
    vaults.undo()
    assert vaults.get_denominations("bank") == []
    assert vaults.get_count("safe", 100) == 4


def test_there_is_no_redo():
    v = Vaults()
    v.add_vault("till")
    v.deposit("till", 50, 3)
    v.undo()
    v.undo()
    assert v.get_vaults() == []
    with pytest.raises(VaultError):
        v.undo()


def test_new_calls_after_an_undo_are_undone_first(vaults):
    vaults.deposit("bank", 200, 2)
    vaults.undo()
    vaults.deposit("bank", 1, 1)
    vaults.undo()
    assert vaults.get_denominations("bank") == []
    vaults.undo()  # the deposit into safe in the fixture
    assert vaults.get_denominations("safe") == []
    assert vaults.get_denominations("till") == [10, 50]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    v = Vaults()
    with pytest.raises(VaultError):
        v.undo()
    v.add_vault("till")
    v.undo()
    with pytest.raises(VaultError):
        v.undo()
    assert v.get_vaults() == []
    v.add_vault("till")
    v.deposit("till", 50, 1)
    assert v.get_count("till", 50) == 1


def test_the_whole_fixture_can_be_undone(vaults):
    for _ in range(6):
        vaults.undo()
    assert vaults.get_vaults() == []
    with pytest.raises(VaultError):
        vaults.undo()


def test_undo_restores_counts_that_a_later_call_checks(vaults):
    vaults.withdraw("till", 50, 3)
    vaults.undo()
    assert vaults.consolidate("till", "bank") == 5
    assert vaults.get_count("bank", 50) == 3
    with pytest.raises(NotEnoughCoins):
        vaults.withdraw("till", 50, 1)
