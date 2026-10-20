"""Hidden tests for the c_fees change (fees on money leaving an account).
Never shown to the writer or the editor.

Usage (with ledger.py importable, e.g. in the sandbox):
    python -m pytest changes/c_fees/private/test_fees_new.py
"""

import pytest
from ledger import InsufficientFunds, Ledger


@pytest.fixture
def ledger():
    led = Ledger(fee=10)
    led.open_account("alice")
    led.open_account("bob")
    led.deposit("alice", 1000)
    return led


def state(led):
    return {a: (led.get_balance(a), led.get_history(a)) for a in led.get_accounts()}


def test_the_sender_alone_pays_the_transfer_fee(ledger):
    ledger.transfer("alice", "bob", 300)
    assert (ledger.get_balance("alice"), ledger.get_balance("bob")) == (690, 300)
    assert ledger.get_history("alice") == [("deposit", 1000), ("transfer_out", 300), ("fee", 10)]
    assert ledger.get_history("bob") == [("transfer_in", 300)]


def test_deposits_are_free(ledger):
    ledger.deposit("bob", 50)
    assert ledger.get_balance("bob") == 50
    assert ledger.get_history("bob") == [("deposit", 50)]
    assert ledger.get_total_fees() == 0


def test_total_fees_adds_up_over_all_accounts(ledger):
    ledger.withdraw("alice", 100)
    ledger.transfer("alice", "bob", 100)
    ledger.withdraw("bob", 50)
    assert ledger.get_total_fees() == 30
    assert ledger.get_balance("bob") == 40


def test_the_amount_and_the_fee_must_both_be_covered(ledger):
    before = state(ledger)
    with pytest.raises(InsufficientFunds):
        ledger.withdraw("alice", 991)
    with pytest.raises(InsufficientFunds):
        ledger.transfer("alice", "bob", 991)
    assert state(ledger) == before
    assert ledger.get_total_fees() == 0
    ledger.withdraw("alice", 990)
    assert ledger.get_balance("alice") == 0


def test_the_fee_counts_against_the_overdraft_limit():
    led = Ledger(fee=10)
    led.open_account("alice", overdraft_limit=50)
    led.withdraw("alice", 40)
    assert led.get_balance("alice") == -50
    with pytest.raises(InsufficientFunds):
        led.withdraw("alice", 1)
    assert led.get_balance("alice") == -50


def test_failed_calls_charge_no_fee(ledger):
    for call in (
        lambda: ledger.withdraw("alice", 0),
        lambda: ledger.transfer("alice", "alice", 5),
        lambda: ledger.withdraw("carol", 5),
    ):
        with pytest.raises((ValueError, KeyError)):
            call()
    assert ledger.get_total_fees() == 0
    assert ledger.get_history("alice") == [("deposit", 1000)]


@pytest.mark.parametrize("fee", [-1, 2.5, "10", True, None])
def test_invalid_fees_are_rejected(fee):
    with pytest.raises(ValueError):
        Ledger(fee=fee)


def test_a_zero_fee_adds_no_history_entries():
    led = Ledger(fee=0)
    led.open_account("alice")
    led.open_account("bob")
    led.deposit("alice", 100)
    led.transfer("alice", "bob", 30)
    assert led.get_history("alice") == [("deposit", 100), ("transfer_out", 30)]
    assert led.get_total_fees() == 0
