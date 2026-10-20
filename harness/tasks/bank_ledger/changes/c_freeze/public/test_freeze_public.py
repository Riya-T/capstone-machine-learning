"""Public checks for the c_freeze change (frozen accounts). Shown to the
editor, never to the writer.

Usage (with ledger.py importable, e.g. in the sandbox):
    python -m pytest changes/c_freeze/public/test_freeze_public.py
"""

import pytest
from ledger import AccountFrozen, Ledger


def test_a_frozen_account_cannot_withdraw():
    led = Ledger()
    led.open_account("alice")
    led.deposit("alice", 100)
    led.freeze("alice")
    assert led.is_frozen("alice")
    with pytest.raises(AccountFrozen):
        led.withdraw("alice", 10)
    led.unfreeze("alice")
    led.withdraw("alice", 10)
    assert led.get_balance("alice") == 90


def test_deposits_still_work_while_frozen():
    led = Ledger()
    led.open_account("alice")
    led.freeze("alice")
    led.deposit("alice", 50)
    assert led.get_balance("alice") == 50
