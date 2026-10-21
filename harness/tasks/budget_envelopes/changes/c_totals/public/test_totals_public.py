"""Public checks for the c_totals change (spending totals). Shown to the
editor, never to the writer.

Usage (with envelopes.py importable, e.g. in the sandbox):
    python -m pytest changes/c_totals/public/test_totals_public.py
"""

from envelopes import Budget


def test_spent_totals_per_envelope_and_overall():
    bud = Budget()
    bud.add_envelope("food")
    bud.add_envelope("fun")
    bud.add_income(10000)
    bud.allocate("food", 6000)
    bud.allocate("fun", 2000)
    bud.spend("food", 1250)
    bud.spend("food", 750)
    bud.spend("fun", 500)
    assert bud.get_spent("food") == 2000
    assert bud.get_spent("fun") == 500
    assert bud.get_total_spent() == 2500
    assert bud.get_total_income() == 10000
    assert bud.get_top_spenders() == ["food", "fun"]


def test_allocating_is_not_spending():
    bud = Budget()
    bud.add_envelope("food")
    bud.add_income(5000)
    bud.allocate("food", 3000)
    assert bud.get_spent("food") == 0
    assert bud.get_total_spent() == 0
    assert bud.get_top_spenders() == ["food"]
