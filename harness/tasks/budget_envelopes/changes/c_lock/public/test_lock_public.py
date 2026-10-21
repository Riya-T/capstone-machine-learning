"""Public checks for the c_lock change (locked envelopes). Shown to the
editor, never to the writer.

Usage (with envelopes.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lock/public/test_lock_public.py
"""

import pytest
from envelopes import Budget, EnvelopeLocked


def test_a_locked_envelope_refuses_spending_until_unlocked():
    bud = Budget()
    bud.add_envelope("rent")
    bud.add_income(50000)
    bud.allocate("rent", 45000)
    bud.lock("rent")
    assert bud.is_locked("rent")
    with pytest.raises(EnvelopeLocked):
        bud.spend("rent", 100)
    assert bud.get_balance("rent") == 45000
    bud.unlock("rent")
    bud.spend("rent", 100)
    assert bud.get_balance("rent") == 44900


def test_a_locked_envelope_refuses_allocations_too():
    bud = Budget()
    bud.add_envelope("rent")
    bud.add_income(50000)
    bud.lock("rent")
    with pytest.raises(EnvelopeLocked):
        bud.allocate("rent", 100)
    assert bud.get_unassigned() == 50000
    assert bud.get_balance("rent") == 0
