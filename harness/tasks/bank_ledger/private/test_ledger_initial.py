"""Hidden tests for the initial bank_ledger spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with ledger.py importable, e.g. in the sandbox):
    python -m pytest private/test_ledger_initial.py
"""

import pytest
from ledger import InsufficientFunds, Ledger, LedgerError

BAD_AMOUNTS = [0, -5, 1.5, "10", None]


@pytest.fixture
def ledger():
    led = Ledger()
    led.open_account("alice")
    led.open_account("bob")
    return led


def state(led):
    """Every balance and history, to check that a failed call changed nothing."""
    return {a: (led.get_balance(a), led.get_history(a)) for a in led.get_accounts()}


# --- accounts ---------------------------------------------------------------


def test_new_account_starts_empty(ledger):
    assert ledger.get_balance("alice") == 0
    assert ledger.get_history("alice") == []


def test_accounts_are_listed_in_opening_order():
    led = Ledger()
    for name in ["carol", "alice", "bob"]:
        led.open_account(name)
    assert led.get_accounts() == ["carol", "alice", "bob"]


@pytest.mark.parametrize("bad_id", [""])
def test_invalid_account_ids_are_rejected(bad_id):
    led = Ledger()
    with pytest.raises(ValueError):
        led.open_account(bad_id)
    assert led.get_accounts() == []


def test_opening_an_open_account_is_rejected(ledger):
    ledger.deposit("alice", 100)
    with pytest.raises(LedgerError):
        ledger.open_account("alice")
    assert ledger.get_balance("alice") == 100
    assert ledger.get_accounts() == ["alice", "bob"]


@pytest.mark.parametrize(
    "call",
    [
        lambda led: led.deposit("carol", 10),
        lambda led: led.withdraw("carol", 10),
        lambda led: led.get_balance("carol"),
        lambda led: led.get_history("carol"),
        lambda led: led.transfer("carol", "bob", 10),
        lambda led: led.transfer("alice", "carol", 10),
        lambda led: led.get_balance(None),
        lambda led: led.get_balance(1),
    ],
)
def test_accounts_that_are_not_open_raise_key_error(ledger, call):
    ledger.deposit("alice", 50)
    before = state(ledger)
    with pytest.raises(KeyError):
        call(ledger)
    assert state(ledger) == before


# --- moving money -----------------------------------------------------------


def test_deposits_and_withdrawals_change_the_balance(ledger):
    ledger.deposit("alice", 500)
    ledger.deposit("alice", 250)
    ledger.withdraw("alice", 100)
    assert ledger.get_balance("alice") == 650
    assert ledger.get_balance("bob") == 0


def test_the_whole_balance_can_be_withdrawn(ledger):
    ledger.deposit("alice", 300)
    ledger.withdraw("alice", 300)
    assert ledger.get_balance("alice") == 0


def test_overdrawing_raises_and_changes_nothing(ledger):
    ledger.deposit("alice", 300)
    before = state(ledger)
    with pytest.raises(InsufficientFunds):
        ledger.withdraw("alice", 301)
    assert state(ledger) == before


def test_transfer_moves_money(ledger):
    ledger.deposit("alice", 500)
    ledger.transfer("alice", "bob", 200)
    assert (ledger.get_balance("alice"), ledger.get_balance("bob")) == (300, 200)


def test_transferring_more_than_the_balance_raises_and_changes_nothing(ledger):
    ledger.deposit("alice", 100)
    before = state(ledger)
    with pytest.raises(InsufficientFunds):
        ledger.transfer("alice", "bob", 101)
    assert state(ledger) == before


def test_transfer_to_the_same_account_is_rejected(ledger):
    ledger.deposit("alice", 100)
    before = state(ledger)
    with pytest.raises(ValueError):
        ledger.transfer("alice", "alice", 50)
    assert state(ledger) == before


@pytest.mark.parametrize("amount", BAD_AMOUNTS)
@pytest.mark.parametrize(
    "call",
    [
        lambda led, a: led.deposit("alice", a),
        lambda led, a: led.withdraw("alice", a),
        lambda led, a: led.transfer("alice", "bob", a),
    ],
    ids=["deposit", "withdraw", "transfer"],
)
def test_invalid_amounts_are_rejected(ledger, call, amount):
    ledger.deposit("alice", 100)
    before = state(ledger)
    with pytest.raises(ValueError):
        call(ledger, amount)
    assert state(ledger) == before


def test_an_account_that_is_not_open_is_reported_before_a_bad_amount(ledger):
    with pytest.raises(KeyError):
        ledger.withdraw("carol", -1)
    with pytest.raises(KeyError):
        ledger.transfer("alice", "carol", -1)


def test_a_bad_amount_is_reported_before_missing_funds(ledger):
    # alice has 0, so 1.5 is also more than her balance.
    with pytest.raises(ValueError):
        ledger.withdraw("alice", 1.5)
    with pytest.raises(ValueError):
        ledger.transfer("alice", "bob", 1.5)


def test_same_account_is_reported_before_missing_funds(ledger):
    with pytest.raises(ValueError):
        ledger.transfer("alice", "alice", 10**6)


# --- history ----------------------------------------------------------------


def test_history_lists_every_movement_oldest_first(ledger):
    ledger.deposit("alice", 500)
    ledger.withdraw("alice", 120)
    ledger.transfer("alice", "bob", 80)
    ledger.transfer("bob", "alice", 30)
    assert ledger.get_history("alice") == [
        ("deposit", 500),
        ("withdrawal", 120),
        ("transfer_out", 80),
        ("transfer_in", 30),
    ]
    assert ledger.get_history("bob") == [("transfer_in", 80), ("transfer_out", 30)]


def test_failed_calls_add_nothing_to_history(ledger):
    ledger.deposit("alice", 10)
    for call in (
        lambda: ledger.withdraw("alice", 11),
        lambda: ledger.transfer("alice", "bob", 11),
        lambda: ledger.deposit("alice", 0),
        lambda: ledger.transfer("alice", "alice", 5),
    ):
        with pytest.raises((ValueError, LedgerError)):
            call()
    assert ledger.get_history("alice") == [("deposit", 10)]
    assert ledger.get_history("bob") == []


def test_insufficient_funds_is_a_ledger_error():
    assert issubclass(InsufficientFunds, LedgerError)


def test_ledgers_do_not_share_accounts():
    first, second = Ledger(), Ledger()
    first.open_account("alice")
    first.deposit("alice", 5)
    assert second.get_accounts() == []
    second.open_account("alice")
    assert second.get_balance("alice") == 0
