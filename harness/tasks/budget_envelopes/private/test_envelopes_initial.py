"""Hidden tests for the initial budget_envelopes spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with envelopes.py importable, e.g. in the sandbox):
    python -m pytest private/test_envelopes_initial.py
"""

import pytest
from envelopes import Budget, BudgetError, NotEnoughMoney

BAD_AMOUNTS = [0, -5, 1.5, "10", None]


@pytest.fixture
def budget():
    bud = Budget()
    bud.add_envelope("food")
    bud.add_envelope("rent")
    bud.add_income(100000)
    return bud


def state(bud):
    """Unassigned money and every balance, to check a failed call changed nothing."""
    return (bud.get_unassigned(), {n: bud.get_balance(n) for n in bud.get_envelopes()})


# --- envelopes --------------------------------------------------------------


def test_a_new_budget_is_empty():
    bud = Budget()
    assert bud.get_unassigned() == 0
    assert bud.get_envelopes() == []


def test_a_new_envelope_holds_nothing(budget):
    assert budget.get_balance("food") == 0
    assert budget.get_balance("rent") == 0


def test_envelopes_are_listed_in_creation_order():
    bud = Budget()
    for name in ["travel", "food", "bills"]:
        bud.add_envelope(name)
    assert bud.get_envelopes() == ["travel", "food", "bills"]


@pytest.mark.parametrize("bad_name", [""])
def test_invalid_envelope_names_are_rejected(bad_name):
    bud = Budget()
    with pytest.raises(ValueError):
        bud.add_envelope(bad_name)
    assert bud.get_envelopes() == []


def test_creating_an_existing_envelope_is_rejected_and_keeps_its_money(budget):
    budget.allocate("food", 5000)
    before = state(budget)
    with pytest.raises(BudgetError):
        budget.add_envelope("food")
    assert state(budget) == before
    assert budget.get_envelopes() == ["food", "rent"]


@pytest.mark.parametrize(
    "call",
    [
        lambda bud: bud.allocate("travel", 10),
        lambda bud: bud.spend("travel", 10),
        lambda bud: bud.get_balance("travel"),
        lambda bud: bud.get_balance(None),
        lambda bud: bud.allocate(1, 10),
        lambda bud: bud.spend(None, 10),
    ],
)
def test_envelopes_that_do_not_exist_raise_key_error(budget, call):
    budget.allocate("food", 500)
    before = state(budget)
    with pytest.raises(KeyError):
        call(budget)
    assert state(budget) == before


# --- money ------------------------------------------------------------------


def test_income_accumulates_as_unassigned():
    bud = Budget()
    bud.add_income(2500)
    bud.add_income(1500)
    assert bud.get_unassigned() == 4000


def test_allocations_move_money_into_envelopes(budget):
    budget.allocate("food", 30000)
    budget.allocate("food", 10000)
    budget.allocate("rent", 55000)
    assert budget.get_balance("food") == 40000
    assert budget.get_balance("rent") == 55000
    assert budget.get_unassigned() == 5000


def test_all_unassigned_money_can_be_allocated(budget):
    budget.allocate("rent", 100000)
    assert budget.get_unassigned() == 0
    assert budget.get_balance("rent") == 100000


def test_over_allocating_raises_and_changes_nothing(budget):
    budget.allocate("food", 40000)
    before = state(budget)
    with pytest.raises(NotEnoughMoney):
        budget.allocate("rent", 60001)
    assert state(budget) == before


def test_spending_takes_money_out_of_the_envelope(budget):
    budget.allocate("food", 30000)
    budget.spend("food", 1250)
    budget.spend("food", 750)
    assert budget.get_balance("food") == 28000
    assert budget.get_unassigned() == 70000


def test_the_whole_envelope_can_be_spent(budget):
    budget.allocate("food", 30000)
    budget.spend("food", 30000)
    assert budget.get_balance("food") == 0


def test_overspending_raises_and_changes_nothing(budget):
    budget.allocate("food", 30000)
    before = state(budget)
    with pytest.raises(NotEnoughMoney):
        budget.spend("food", 30001)
    assert state(budget) == before


def test_spending_from_an_empty_envelope_raises(budget):
    with pytest.raises(NotEnoughMoney):
        budget.spend("rent", 1)
    assert budget.get_unassigned() == 100000


def test_unassigned_money_cannot_be_spent_directly(budget):
    budget.allocate("food", 1000)
    with pytest.raises(NotEnoughMoney):
        budget.spend("food", 1001)
    assert budget.get_unassigned() == 99000
    assert budget.get_balance("food") == 1000


@pytest.mark.parametrize("amount", BAD_AMOUNTS)
@pytest.mark.parametrize(
    "call",
    [
        lambda bud, a: bud.add_income(a),
        lambda bud, a: bud.allocate("food", a),
        lambda bud, a: bud.spend("food", a),
    ],
    ids=["add_income", "allocate", "spend"],
)
def test_invalid_amounts_are_rejected(budget, call, amount):
    budget.allocate("food", 500)
    before = state(budget)
    with pytest.raises(ValueError):
        call(budget, amount)
    assert state(budget) == before


def test_a_missing_envelope_is_reported_before_a_bad_amount(budget):
    with pytest.raises(KeyError):
        budget.allocate("travel", -1)
    with pytest.raises(KeyError):
        budget.spend("travel", 0)


def test_a_bad_amount_is_reported_before_missing_money(budget):
    # rent holds 0, so 1.5 is also more than it can cover.
    with pytest.raises(ValueError):
        budget.spend("rent", 1.5)
    bud = Budget()
    bud.add_envelope("food")
    with pytest.raises(ValueError):
        bud.allocate("food", "10")


def test_not_enough_money_is_a_budget_error():
    assert issubclass(NotEnoughMoney, BudgetError)


def test_budgets_do_not_share_money():
    first, second = Budget(), Budget()
    first.add_envelope("food")
    first.add_income(500)
    assert second.get_unassigned() == 0
    assert second.get_envelopes() == []
    second.add_envelope("food")
    assert second.get_balance("food") == 0
