"""Hidden tests for the c_lock change (locked envelopes). Never shown to the
writer or the editor.

Usage (with envelopes.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lock/private/test_lock_new.py
"""

import pytest
from envelopes import Budget, BudgetError, EnvelopeLocked, NotEnoughMoney


@pytest.fixture
def budget():
    bud = Budget()
    bud.add_envelope("food")
    bud.add_envelope("rent")
    bud.add_income(10000)
    bud.allocate("rent", 4000)
    return bud


def state(bud):
    return (
        bud.get_unassigned(),
        {n: (bud.get_balance(n), bud.is_locked(n)) for n in bud.get_envelopes()},
    )


def test_envelopes_start_unlocked(budget):
    assert not budget.is_locked("food")
    assert not budget.is_locked("rent")


def test_locking_or_unlocking_twice_is_harmless(budget):
    budget.lock("rent")
    budget.lock("rent")
    assert budget.is_locked("rent")
    assert not budget.is_locked("food")
    budget.unlock("rent")
    budget.unlock("rent")
    assert not budget.is_locked("rent")


@pytest.mark.parametrize("method", ["lock", "unlock", "is_locked"])
@pytest.mark.parametrize("name", ["travel", None, 1])
def test_locking_a_missing_envelope_raises_key_error(budget, method, name):
    before = state(budget)
    with pytest.raises(KeyError):
        getattr(budget, method)(name)
    assert state(budget) == before


def test_spending_from_a_locked_envelope_changes_nothing(budget):
    budget.lock("rent")
    before = state(budget)
    with pytest.raises(EnvelopeLocked):
        budget.spend("rent", 100)
    assert state(budget) == before


def test_allocating_to_a_locked_envelope_changes_nothing(budget):
    budget.lock("rent")
    before = state(budget)
    with pytest.raises(EnvelopeLocked):
        budget.allocate("rent", 100)
    assert state(budget) == before


def test_other_envelopes_are_not_affected(budget):
    budget.lock("rent")
    budget.allocate("food", 1000)
    budget.spend("food", 250)
    assert budget.get_balance("food") == 750
    assert budget.get_unassigned() == 5000


def test_locked_envelopes_still_report_and_list(budget):
    budget.lock("rent")
    assert budget.get_balance("rent") == 4000
    assert budget.get_envelopes() == ["food", "rent"]


def test_locking_changes_no_money(budget):
    before = (budget.get_unassigned(), budget.get_balance("rent"), budget.get_balance("food"))
    budget.lock("rent")
    budget.lock("food")
    budget.unlock("food")
    assert (budget.get_unassigned(), budget.get_balance("rent"), budget.get_balance("food")) == before


def test_locked_is_reported_before_missing_money(budget):
    budget.lock("food")  # food holds 0
    with pytest.raises(EnvelopeLocked):
        budget.spend("food", 1)
    with pytest.raises(EnvelopeLocked):
        budget.allocate("food", 10**6)


def test_bad_input_is_reported_before_locked(budget):
    budget.lock("rent")
    with pytest.raises(ValueError):
        budget.spend("rent", -1)
    with pytest.raises(ValueError):
        budget.allocate("rent", 0)
    with pytest.raises(KeyError):
        budget.spend("travel", 10)


def test_an_unlocked_envelope_works_normally_again(budget):
    budget.lock("rent")
    budget.unlock("rent")
    budget.spend("rent", 1500)
    budget.allocate("rent", 500)
    assert budget.get_balance("rent") == 3000
    with pytest.raises(NotEnoughMoney):
        budget.spend("rent", 3001)


def test_envelope_locked_is_a_budget_error_but_not_not_enough_money():
    assert issubclass(EnvelopeLocked, BudgetError)
    assert not issubclass(EnvelopeLocked, NotEnoughMoney)
