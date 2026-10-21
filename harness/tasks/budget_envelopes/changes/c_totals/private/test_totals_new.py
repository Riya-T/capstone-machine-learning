"""Hidden tests for the c_totals change (spending totals). Never shown to the
writer or the editor.

Usage (with envelopes.py importable, e.g. in the sandbox):
    python -m pytest changes/c_totals/private/test_totals_new.py
"""

import pytest
from envelopes import Budget, NotEnoughMoney


@pytest.fixture
def budget():
    bud = Budget()
    bud.add_envelope("food")
    bud.add_envelope("fun")
    bud.add_envelope("rent")
    bud.add_income(10000)
    bud.allocate("food", 4000)
    bud.allocate("fun", 2000)
    return bud


def test_a_fresh_budget_has_spent_nothing(budget):
    assert budget.get_spent("food") == 0
    assert budget.get_total_spent() == 0
    assert budget.get_top_spenders() == ["food", "fun", "rent"]


def test_total_income_counts_every_add_income(budget):
    assert budget.get_total_income() == 10000
    budget.add_income(2500)
    assert budget.get_total_income() == 12500
    assert Budget().get_total_income() == 0


def test_spent_accumulates_per_envelope(budget):
    budget.spend("food", 1000)
    budget.spend("food", 500)
    budget.spend("fun", 300)
    assert budget.get_spent("food") == 1500
    assert budget.get_spent("fun") == 300
    assert budget.get_spent("rent") == 0
    assert budget.get_total_spent() == 1800


def test_spent_keeps_growing_after_more_allocations(budget):
    budget.spend("food", 4000)
    budget.allocate("food", 1000)
    budget.spend("food", 1000)
    assert budget.get_spent("food") == 5000
    assert budget.get_balance("food") == 0


def test_moving_money_is_not_spending(budget):
    budget.move("food", "fun", 1000)
    budget.allocate_many({"rent": 1000})
    assert budget.get_spent("food") == 0
    assert budget.get_spent("fun") == 0
    assert budget.get_total_spent() == 0


def test_money_adds_up(budget):
    budget.spend("food", 700)
    budget.move("fun", "rent", 500)
    budget.spend("rent", 200)
    held = sum(budget.get_balance(n) for n in budget.get_envelopes())
    assert budget.get_unassigned() + held + budget.get_total_spent() == budget.get_total_income()


def test_top_spenders_orders_by_spent_highest_first(budget):
    budget.allocate("rent", 3000)
    budget.spend("food", 100)
    budget.spend("fun", 900)
    budget.spend("rent", 500)
    assert budget.get_top_spenders() == ["fun", "rent", "food"]


def test_top_spenders_breaks_ties_by_creation_order(budget):
    budget.allocate("rent", 1000)
    budget.spend("rent", 300)
    budget.spend("fun", 300)
    assert budget.get_top_spenders() == ["fun", "rent", "food"]
    budget.spend("food", 300)
    assert budget.get_top_spenders() == ["food", "fun", "rent"]


def test_top_spenders_of_an_empty_budget_is_empty():
    assert Budget().get_top_spenders() == []


@pytest.mark.parametrize("name", ["travel", None, 1])
def test_spent_of_a_missing_envelope_raises_key_error(budget, name):
    with pytest.raises(KeyError):
        budget.get_spent(name)


def test_failed_calls_count_for_nothing(budget):
    budget.spend("fun", 100)
    with pytest.raises(NotEnoughMoney):
        budget.spend("fun", 10**6)
    with pytest.raises(ValueError):
        budget.spend("food", -1)
    with pytest.raises(ValueError):
        budget.add_income(0)
    assert budget.get_spent("fun") == 100
    assert budget.get_spent("food") == 0
    assert budget.get_total_spent() == 100
    assert budget.get_total_income() == 10000


def test_totals_are_per_budget(budget):
    budget.spend("food", 100)
    other = Budget()
    other.add_envelope("food")
    assert other.get_total_spent() == 0
    assert other.get_total_income() == 0
    assert other.get_spent("food") == 0
