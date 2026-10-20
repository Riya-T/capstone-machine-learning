"""Public checks for ledger.py.

Usage (with ledger.py importable, e.g. in the sandbox):
    python -m pytest public/test_ledger_public.py
"""

import pytest
from ledger import InsufficientFunds, Ledger


@pytest.fixture
def ledger():
    led = Ledger()
    led.open_account("alice")
    led.open_account("bob")
    return led


def test_deposit_then_balance(ledger):
    ledger.deposit("alice", 1000)
    assert ledger.get_balance("alice") == 1000


def test_withdrawing_more_than_the_balance_raises(ledger):
    ledger.deposit("alice", 100)
    with pytest.raises(InsufficientFunds):
        ledger.withdraw("alice", 150)
    assert ledger.get_balance("alice") == 100


def test_transfer_moves_money_between_accounts(ledger):
    ledger.deposit("alice", 300)
    ledger.transfer("alice", "bob", 120)
    assert ledger.get_balance("alice") == 180
    assert ledger.get_balance("bob") == 120


def test_history_records_each_movement(ledger):
    ledger.deposit("alice", 300)
    ledger.transfer("alice", "bob", 120)
    assert ledger.get_history("alice") == [("deposit", 300), ("transfer_out", 120)]
    assert ledger.get_history("bob") == [("transfer_in", 120)]


def test_amounts_must_be_positive(ledger):
    with pytest.raises(ValueError):
        ledger.deposit("alice", 0)
    with pytest.raises(ValueError):
        ledger.deposit("alice", -50)


def test_unknown_account_raises_key_error(ledger):
    with pytest.raises(KeyError):
        ledger.get_balance("carol")
