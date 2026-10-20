"""Public checks for the c_fees change (fees on money leaving an account).
Shown to the editor, never to the writer.

Usage (with ledger.py importable, e.g. in the sandbox):
    python -m pytest changes/c_fees/public/test_fees_public.py
"""

from ledger import Ledger


def test_a_withdrawal_pays_the_fee():
    led = Ledger(fee=25)
    led.open_account("alice")
    led.deposit("alice", 1000)
    led.withdraw("alice", 100)
    assert led.get_balance("alice") == 875
    assert led.get_history("alice") == [("deposit", 1000), ("withdrawal", 100), ("fee", 25)]
    assert led.get_total_fees() == 25


def test_without_a_fee_nothing_is_charged():
    led = Ledger()
    led.open_account("alice")
    led.deposit("alice", 100)
    led.withdraw("alice", 40)
    assert led.get_balance("alice") == 60
    assert led.get_history("alice") == [("deposit", 100), ("withdrawal", 40)]
    assert led.get_total_fees() == 0
