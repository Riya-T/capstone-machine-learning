"""Hidden tests for the initial coin_vaults spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with vaults.py importable, e.g. in the sandbox):
    python -m pytest private/test_vaults_initial.py
"""

import pytest
from vaults import NotEnoughCoins, VaultError, Vaults

ACCEPTED = [1, 2, 5, 10, 20, 50, 100, 200]


@pytest.fixture
def vaults():
    v = Vaults()
    for name in ["till", "safe", "bank"]:
        v.add_vault(name)
    v.deposit("till", 50, 5)
    v.deposit("till", 10, 2)
    return v


def state(v):
    """Every vault in order with its denominations and counts, to check that
    a failed call changed nothing."""
    return [(n, [(d, v.get_count(n, d)) for d in v.get_denominations(n)]) for n in v.get_vaults()]


# --- vaults -----------------------------------------------------------------


def test_a_new_vault_is_empty():
    v = Vaults()
    v.add_vault("till")
    assert v.get_denominations("till") == []
    assert v.get_count("till", 50) == 0


def test_a_new_object_has_no_vaults():
    assert Vaults().get_vaults() == []


def test_vaults_are_listed_in_the_order_added():
    v = Vaults()
    for name in ["safe", "till", "bank"]:
        v.add_vault(name)
    assert v.get_vaults() == ["safe", "till", "bank"]


def test_adding_a_name_in_use_is_rejected(vaults):
    before = state(vaults)
    with pytest.raises(VaultError):
        vaults.add_vault("till")
    assert state(vaults) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda v: v.deposit("cellar", 50, 1),
        lambda v: v.consolidate("cellar", "safe"),
        lambda v: v.consolidate("till", "cellar"),
        lambda v: v.close_vault("cellar", "safe"),
        lambda v: v.close_vault("till", "cellar"),
        lambda v: v.get_count("cellar", 50),
        lambda v: v.get_denominations("cellar"),
    ],
)
def test_vaults_that_were_never_added_raise_key_error(vaults, call):
    before = state(vaults)
    with pytest.raises(KeyError):
        call(vaults)
    assert state(vaults) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda v: v.deposit("bank", 50, 1),
        lambda v: v.consolidate("bank", "safe"),
        lambda v: v.consolidate("till", "bank"),
        lambda v: v.close_vault("bank", "safe"),
        lambda v: v.close_vault("till", "bank"),
        lambda v: v.get_count("bank", 50),
        lambda v: v.get_denominations("bank"),
    ],
)
def test_a_closed_vault_is_not_in_use(vaults, call):
    vaults.close_vault("bank", "safe")  # bank is empty
    before = state(vaults)
    with pytest.raises(KeyError):
        call(vaults)
    assert state(vaults) == before


# --- deposits and withdrawals -------------------------------------------------


def test_deposits_and_withdrawals_add_up(vaults):
    vaults.deposit("till", 50, 3)
    vaults.withdraw("till", 50, 6)
    vaults.deposit("safe", 50, 1)
    assert vaults.get_count("till", 50) == 2
    assert vaults.get_count("safe", 50) == 1
    assert vaults.get_count("till", 10) == 2


def test_every_accepted_denomination_can_be_deposited():
    v = Vaults()
    v.add_vault("till")
    for d in reversed(ACCEPTED):
        v.deposit("till", d, 1)
    assert v.get_denominations("till") == ACCEPTED


@pytest.mark.parametrize("denomination", [3, 25, 500, 0, -50])
def test_other_denominations_are_rejected(vaults, denomination):
    before = state(vaults)
    with pytest.raises(ValueError):
        vaults.deposit("till", denomination, 1)
    assert state(vaults) == before


def test_denominations_are_listed_smallest_first(vaults):
    for d in [200, 1, 50, 5]:
        vaults.deposit("safe", d, 2)
    assert vaults.get_denominations("safe") == [1, 5, 50, 200]


def test_every_coin_of_a_denomination_can_be_withdrawn(vaults):
    vaults.withdraw("till", 10, 2)
    assert vaults.get_count("till", 10) == 0
    assert vaults.get_denominations("till") == [50]


def test_withdrawing_more_than_the_vault_holds_changes_nothing(vaults):
    before = state(vaults)
    with pytest.raises(NotEnoughCoins):
        vaults.withdraw("till", 10, 3)
    with pytest.raises(NotEnoughCoins):
        vaults.withdraw("till", 20, 1)
    with pytest.raises(NotEnoughCoins):
        vaults.withdraw("safe", 50, 1)
    assert state(vaults) == before


@pytest.mark.parametrize("count", [0, -3])
@pytest.mark.parametrize(
    "call",
    [lambda v, c: v.deposit("till", 50, c), lambda v, c: v.withdraw("till", 50, c)],
    ids=["deposit", "withdraw"],
)
def test_counts_of_0_or_less_are_rejected(vaults, call, count):
    before = state(vaults)
    with pytest.raises(ValueError):
        call(vaults, count)
    assert state(vaults) == before


# --- consolidating --------------------------------------------------------------


def test_consolidate_moves_every_denomination(vaults):
    vaults.deposit("safe", 50, 1)
    vaults.deposit("safe", 1, 4)
    assert vaults.consolidate("till", "safe") == 7
    assert vaults.get_denominations("till") == []
    assert vaults.get_denominations("safe") == [1, 10, 50]
    assert vaults.get_count("safe", 50) == 6
    assert vaults.get_count("safe", 10) == 2
    assert vaults.get_count("safe", 1) == 4
    assert vaults.get_vaults() == ["till", "safe", "bank"]


def test_consolidating_an_empty_vault_moves_nothing(vaults):
    before = state(vaults)
    assert vaults.consolidate("bank", "till") == 0
    assert state(vaults) == before


def test_a_consolidated_vault_stays_in_use(vaults):
    vaults.consolidate("till", "bank")
    vaults.deposit("till", 5, 1)
    assert vaults.get_denominations("till") == [5]
    assert vaults.get_denominations("bank") == [10, 50]
    assert vaults.consolidate("bank", "till") == 7
    assert vaults.get_count("till", 50) == 5


# --- closing -----------------------------------------------------------------------


def test_close_vault_moves_every_coin_and_closes_it(vaults):
    vaults.deposit("bank", 50, 2)
    assert vaults.close_vault("till", "bank") == 7
    assert vaults.get_vaults() == ["safe", "bank"]
    assert vaults.get_count("bank", 50) == 7
    assert vaults.get_count("bank", 10) == 2


def test_closing_an_empty_vault_moves_nothing(vaults):
    assert vaults.close_vault("safe", "till") == 0
    assert vaults.get_vaults() == ["till", "bank"]
    assert vaults.get_count("till", 50) == 5


def test_the_other_vaults_keep_their_order_after_a_close(vaults):
    vaults.add_vault("cellar")
    vaults.close_vault("safe", "cellar")
    assert vaults.get_vaults() == ["till", "bank", "cellar"]
    vaults.close_vault("till", "bank")
    assert vaults.get_vaults() == ["bank", "cellar"]


@pytest.mark.parametrize(
    "call",
    [
        lambda v: v.consolidate("till", "till"),
        lambda v: v.close_vault("till", "till"),
        lambda v: v.consolidate("bank", "bank"),
    ],
    ids=["consolidate", "close_vault", "consolidate_empty"],
)
def test_the_same_vault_on_both_sides_is_rejected(vaults, call):
    before = state(vaults)
    with pytest.raises(ValueError):
        call(vaults)
    assert state(vaults) == before


# --- general ---------------------------------------------------------------------


def test_not_enough_coins_is_a_vault_error():
    assert issubclass(NotEnoughCoins, VaultError)


def test_objects_do_not_share_vaults():
    first, second = Vaults(), Vaults()
    first.add_vault("till")
    first.deposit("till", 50, 3)
    assert second.get_vaults() == []
    second.add_vault("till")
    assert second.get_count("till", 50) == 0
