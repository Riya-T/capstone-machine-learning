"""Public checks for envelopes.py.

Usage (with envelopes.py importable, e.g. in the sandbox):
    python -m pytest public/test_envelopes_public.py
"""

import pytest
from envelopes import Budget, NotEnoughMoney


@pytest.fixture
def budget():
    bud = Budget()
    bud.add_envelope("food")
    bud.add_envelope("rent")
    bud.add_income(100000)
    return bud


def test_allocating_moves_money_out_of_unassigned(budget):
    budget.allocate("food", 30000)
    budget.allocate("rent", 50000)
    assert budget.get_balance("food") == 30000
    assert budget.get_balance("rent") == 50000
    assert budget.get_unassigned() == 20000


def test_spending_reduces_the_envelope_only(budget):
    budget.allocate("food", 30000)
    budget.spend("food", 1250)
    assert budget.get_balance("food") == 28750
    assert budget.get_unassigned() == 70000


def test_spending_more_than_the_envelope_holds_raises(budget):
    budget.allocate("food", 1000)
    with pytest.raises(NotEnoughMoney):
        budget.spend("food", 1500)
    assert budget.get_balance("food") == 1000


def test_allocating_more_than_is_unassigned_raises(budget):
    with pytest.raises(NotEnoughMoney):
        budget.allocate("rent", 100001)
    assert budget.get_unassigned() == 100000
    assert budget.get_balance("rent") == 0


def test_an_envelope_that_does_not_exist_raises_key_error(budget):
    with pytest.raises(KeyError):
        budget.get_balance("travel")
    with pytest.raises(KeyError):
        budget.allocate("travel", 100)


def test_amounts_must_be_positive(budget):
    with pytest.raises(ValueError):
        budget.add_income(0)
    with pytest.raises(ValueError):
        budget.allocate("food", -50)
    assert budget.get_envelopes() == ["food", "rent"]
