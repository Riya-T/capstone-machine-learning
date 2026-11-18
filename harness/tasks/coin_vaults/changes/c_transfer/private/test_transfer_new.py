"""Hidden tests for the c_transfer change (atomic_operation). Never shown to
the writer or the editor.

Usage (with vaults.py importable, e.g. in the sandbox):
    python -m pytest changes/c_transfer/private/test_transfer_new.py
"""

import pytest
from vaults import NotEnoughCoins, Vaults


@pytest.fixture
def vaults():
    v = Vaults()
    for name in ["till", "safe", "bank"]:
        v.add_vault(name)
    v.deposit("till", 50, 4)
    v.deposit("till", 10, 3)
    v.deposit("safe", 100, 2)
    return v


def state(v):
    return [(n, [(d, v.get_count(n, d)) for d in v.get_denominations(n)]) for n in v.get_vaults()]


# --- successful transfers ---------------------------------------------------


def test_a_single_move(vaults):
    assert vaults.transfer([("till", "bank", 50, 1)]) == 1
    assert vaults.get_count("till", 50) == 3
    assert vaults.get_count("bank", 50) == 1


def test_moves_between_several_vaults(vaults):
    total = vaults.transfer(
        [("till", "bank", 50, 2), ("safe", "till", 100, 1), ("till", "safe", 10, 3)]
    )
    assert total == 6
    assert state(vaults) == [
        ("till", [(50, 2), (100, 1)]),
        ("safe", [(10, 3), (100, 1)]),
        ("bank", [(50, 2)]),
    ]


def test_a_vault_may_pass_on_coins_it_received_earlier_in_the_list(vaults):
    assert vaults.transfer([("till", "bank", 50, 4), ("bank", "safe", 50, 3)]) == 7
    assert vaults.get_count("bank", 50) == 1
    assert vaults.get_count("safe", 50) == 3
    assert vaults.get_denominations("till") == [10]


def test_coins_taken_out_earlier_in_the_list_are_gone(vaults):
    with pytest.raises(NotEnoughCoins):
        vaults.transfer([("till", "bank", 10, 2), ("till", "safe", 10, 2)])
    assert vaults.get_count("till", 10) == 3


def test_every_coin_of_a_denomination_can_be_moved(vaults):
    vaults.transfer([("till", "bank", 10, 3)])
    assert vaults.get_denominations("till") == [50]
    assert vaults.get_denominations("bank") == [10]


def test_the_same_vaults_may_appear_in_several_moves(vaults):
    assert vaults.transfer([("till", "bank", 50, 1), ("till", "bank", 50, 1), ("bank", "till", 50, 2)]) == 4
    assert vaults.get_count("till", 50) == 4
    assert vaults.get_denominations("bank") == []


def test_an_empty_list_moves_nothing(vaults):
    before = state(vaults)
    assert vaults.transfer([]) == 0
    assert state(vaults) == before


def test_transfer_keeps_the_order_of_the_vaults(vaults):
    vaults.transfer([("safe", "till", 100, 2)])
    assert vaults.get_vaults() == ["till", "safe", "bank"]
    assert vaults.get_denominations("safe") == []


# --- failing transfers change nothing ---------------------------------------


@pytest.mark.parametrize(
    "bad_move, error",
    [
        (("till", "safe", 10, 9), NotEnoughCoins),
        (("till", "safe", 20, 1), NotEnoughCoins),
        (("till", "cellar", 50, 1), KeyError),
        (("cellar", "till", 50, 1), KeyError),
        (("till", "safe", 50, 0), ValueError),
        (("till", "safe", 50, -2), ValueError),
        (("till", "till", 50, 1), ValueError),
    ],
)
def test_a_failing_last_move_cancels_every_earlier_move(vaults, bad_move, error):
    before = state(vaults)
    with pytest.raises(error):
        vaults.transfer([("till", "bank", 50, 2), ("safe", "bank", 100, 1), bad_move])
    assert state(vaults) == before


def test_a_failing_first_move_changes_nothing(vaults):
    before = state(vaults)
    with pytest.raises(NotEnoughCoins):
        vaults.transfer([("bank", "till", 50, 1), ("till", "bank", 50, 1)])
    assert state(vaults) == before


def test_a_failing_middle_move_changes_nothing(vaults):
    before = state(vaults)
    with pytest.raises(NotEnoughCoins):
        vaults.transfer([("till", "bank", 50, 1), ("safe", "bank", 100, 3), ("till", "bank", 10, 1)])
    assert state(vaults) == before


def test_a_failed_transfer_leaves_the_vaults_usable(vaults):
    with pytest.raises(NotEnoughCoins):
        vaults.transfer([("till", "bank", 50, 4), ("till", "bank", 50, 1)])
    assert vaults.transfer([("till", "bank", 50, 4)]) == 4
    assert vaults.get_count("bank", 50) == 4
