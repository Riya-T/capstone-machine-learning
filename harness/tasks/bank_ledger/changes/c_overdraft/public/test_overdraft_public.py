"""Public checks for the c_overdraft change (overdraft limits). Shown to the
editor, never to the writer.

Usage (with ledger.py importable, e.g. in the sandbox):
    python -m pytest changes/c_overdraft/public/test_overdraft_public.py
"""

import pytest
from ledger import InsufficientFunds, Ledger


def test_withdrawing_into_the_overdraft():
    led = Ledger()
    led.open_account("alice", overdraft_limit=500)
    led.withdraw("alice", 300)
    assert led.get_balance("alice") == -300
    assert led.get_overdraft_limit("alice") == 500


def test_going_past_the_limit_raises():
    led = Ledger()
    led.open_account("alice", overdraft_limit=100)
    with pytest.raises(InsufficientFunds):
        led.withdraw("alice", 101)
    assert led.get_balance("alice") == 0
