"""Hidden tests for the c_overdraft change (overdraft limits). Never shown to
the writer or the editor.

Usage (with ledger.py importable, e.g. in the sandbox):
    python -m pytest changes/c_overdraft/private/test_overdraft_new.py
"""

import pytest
from ledger import InsufficientFunds, Ledger, LedgerError

BAD_LIMITS = [-1, 1.5, "100", True, None]


@pytest.fixture
def ledger():
    led = Ledger()
    led.open_account("alice", overdraft_limit=500)
    led.open_account("bob")
    return led


def state(led):
    return {a: (led.get_balance(a), led.get_history(a)) for a in led.get_accounts()}


def test_the_default_limit_is_zero(ledger):
    assert ledger.get_overdraft_limit("bob") == 0
    with pytest.raises(InsufficientFunds):
        ledger.withdraw("bob", 1)


def test_the_balance_can_reach_exactly_minus_the_limit(ledger):
    ledger.withdraw("alice", 200)
    ledger.withdraw("alice", 300)
    assert ledger.get_balance("alice") == -500
    before = state(ledger)
    with pytest.raises(InsufficientFunds):
        ledger.withdraw("alice", 1)
    assert state(ledger) == before


def test_transfers_can_use_the_overdraft(ledger):
    ledger.transfer("alice", "bob", 450)
    assert (ledger.get_balance("alice"), ledger.get_balance("bob")) == (-450, 450)
    assert ledger.get_history("alice") == [("transfer_out", 450)]
    before = state(ledger)
    with pytest.raises(InsufficientFunds):
        ledger.transfer("alice", "bob", 51)
    assert state(ledger) == before


def test_deposits_pay_back_the_overdraft(ledger):
    ledger.withdraw("alice", 400)
    ledger.deposit("alice", 450)
    assert ledger.get_balance("alice") == 50


@pytest.mark.parametrize("limit", BAD_LIMITS)
def test_invalid_limits_are_rejected_when_opening(limit):
    led = Ledger()
    with pytest.raises(ValueError):
        led.open_account("alice", overdraft_limit=limit)
    assert led.get_accounts() == []


def test_accounts_that_are_not_open_raise_key_error(ledger):
    with pytest.raises(KeyError):
        ledger.get_overdraft_limit("carol")
    with pytest.raises(KeyError):
        ledger.set_overdraft_limit("carol", 10)


def test_set_overdraft_limit_replaces_the_limit(ledger):
    ledger.set_overdraft_limit("bob", 200)
    ledger.withdraw("bob", 150)
    assert ledger.get_balance("bob") == -150
    ledger.set_overdraft_limit("bob", 150)  # exactly covers the debt
    assert ledger.get_overdraft_limit("bob") == 150
    with pytest.raises(InsufficientFunds):
        ledger.withdraw("bob", 1)


def test_a_limit_smaller_than_the_debt_is_rejected(ledger):
    ledger.withdraw("alice", 300)
    before = state(ledger)
    with pytest.raises(LedgerError):
        ledger.set_overdraft_limit("alice", 299)
    assert ledger.get_overdraft_limit("alice") == 500
    assert state(ledger) == before


@pytest.mark.parametrize("limit", BAD_LIMITS)
def test_invalid_limits_are_rejected_when_setting(ledger, limit):
    with pytest.raises(ValueError):
        ledger.set_overdraft_limit("alice", limit)
    assert ledger.get_overdraft_limit("alice") == 500


def test_an_account_that_is_not_open_is_reported_before_a_bad_limit(ledger):
    with pytest.raises(KeyError):
        ledger.set_overdraft_limit("carol", -1)


def test_a_bad_limit_is_reported_before_the_debt_check(ledger):
    ledger.withdraw("alice", 300)
    with pytest.raises(ValueError):
        ledger.set_overdraft_limit("alice", -1)
