"""Hidden tests for the c_freeze change (frozen accounts). Never shown to the
writer or the editor.

Usage (with ledger.py importable, e.g. in the sandbox):
    python -m pytest changes/c_freeze/private/test_freeze_new.py
"""

import pytest
from ledger import AccountFrozen, InsufficientFunds, Ledger, LedgerError


@pytest.fixture
def ledger():
    led = Ledger()
    led.open_account("alice")
    led.open_account("bob")
    led.deposit("alice", 500)
    return led


def state(led):
    return {a: (led.get_balance(a), led.get_history(a)) for a in led.get_accounts()}


def test_accounts_start_unfrozen(ledger):
    assert not ledger.is_frozen("alice")
    assert not ledger.is_frozen("bob")


def test_freezing_or_unfreezing_twice_is_harmless(ledger):
    ledger.freeze("alice")
    ledger.freeze("alice")
    assert ledger.is_frozen("alice")
    ledger.unfreeze("alice")
    ledger.unfreeze("alice")
    assert not ledger.is_frozen("alice")
    assert not ledger.is_frozen("bob")


@pytest.mark.parametrize("method", ["freeze", "unfreeze", "is_frozen"])
def test_accounts_that_are_not_open_raise_key_error(ledger, method):
    with pytest.raises(KeyError):
        getattr(ledger, method)("carol")


def test_a_withdrawal_from_a_frozen_account_changes_nothing(ledger):
    ledger.freeze("alice")
    before = state(ledger)
    with pytest.raises(AccountFrozen):
        ledger.withdraw("alice", 100)
    assert state(ledger) == before


def test_transfers_to_a_frozen_account_are_refused(ledger):
    ledger.freeze("bob")
    before = state(ledger)
    with pytest.raises(AccountFrozen):
        ledger.transfer("alice", "bob", 100)
    assert state(ledger) == before


def test_transfers_from_a_frozen_account_are_refused(ledger):
    ledger.freeze("alice")
    before = state(ledger)
    with pytest.raises(AccountFrozen):
        ledger.transfer("alice", "bob", 100)
    assert state(ledger) == before


def test_frozen_is_reported_before_missing_funds(ledger):
    ledger.freeze("bob")
    with pytest.raises(AccountFrozen):
        ledger.withdraw("bob", 100)
    with pytest.raises(AccountFrozen):
        ledger.transfer("bob", "alice", 100)


def test_bad_input_is_reported_before_frozen(ledger):
    ledger.freeze("alice")
    with pytest.raises(ValueError):
        ledger.withdraw("alice", -1)
    with pytest.raises(ValueError):
        ledger.transfer("alice", "alice", 5)
    with pytest.raises(KeyError):
        ledger.transfer("alice", "carol", 5)


def test_account_frozen_is_a_ledger_error_but_not_insufficient_funds():
    assert issubclass(AccountFrozen, LedgerError)
    assert not issubclass(AccountFrozen, InsufficientFunds)


def test_freezing_adds_nothing_to_history(ledger):
    ledger.freeze("alice")
    ledger.unfreeze("alice")
    assert ledger.get_history("alice") == [("deposit", 500)]


def test_an_unfrozen_account_works_normally(ledger):
    ledger.freeze("alice")
    ledger.unfreeze("alice")
    ledger.transfer("alice", "bob", 200)
    assert (ledger.get_balance("alice"), ledger.get_balance("bob")) == (300, 200)
