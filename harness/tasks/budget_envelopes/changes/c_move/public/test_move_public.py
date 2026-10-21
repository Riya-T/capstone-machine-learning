"""Public checks for the c_move change (moves and all-or-nothing allocation).
Shown to the editor, never to the writer.

Usage (with envelopes.py importable, e.g. in the sandbox):
    python -m pytest changes/c_move/public/test_move_public.py
"""

import pytest
from envelopes import Budget, NotEnoughMoney


@pytest.fixture
def budget():
    bud = Budget()
    bud.add_envelope("food")
    bud.add_envelope("fun")
    bud.add_income(10000)
    return bud


def test_move_shifts_money_between_envelopes(budget):
    budget.allocate("food", 6000)
    budget.move("food", "fun", 1500)
    assert budget.get_balance("food") == 4500
    assert budget.get_balance("fun") == 1500
    assert budget.get_unassigned() == 4000


def test_allocate_many_takes_every_amount_from_unassigned(budget):
    budget.allocate_many({"food": 6000, "fun": 3000})
    assert budget.get_balance("food") == 6000
    assert budget.get_balance("fun") == 3000
    assert budget.get_unassigned() == 1000


def test_allocate_many_is_all_or_nothing(budget):
    with pytest.raises(NotEnoughMoney):
        budget.allocate_many({"food": 6000, "fun": 5000})
    assert budget.get_balance("food") == 0
    assert budget.get_balance("fun") == 0
    assert budget.get_unassigned() == 10000
