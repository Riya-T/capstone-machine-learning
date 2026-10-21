"""Hidden tests for the c_move change (moves and all-or-nothing allocation).
Never shown to the writer or the editor.

Usage (with envelopes.py importable, e.g. in the sandbox):
    python -m pytest changes/c_move/private/test_move_new.py
"""

import pytest
from envelopes import Budget, NotEnoughMoney

BAD_AMOUNTS = [0, -5, 1.5, "10", None]


@pytest.fixture
def budget():
    bud = Budget()
    bud.add_envelope("food")
    bud.add_envelope("fun")
    bud.add_envelope("rent")
    bud.add_income(10000)
    bud.allocate("food", 3000)
    return bud


def state(bud):
    return (bud.get_unassigned(), {n: bud.get_balance(n) for n in bud.get_envelopes()})


# --- move -------------------------------------------------------------------


def test_move_leaves_unassigned_money_alone(budget):
    budget.move("food", "fun", 1000)
    assert budget.get_balance("food") == 2000
    assert budget.get_balance("fun") == 1000
    assert budget.get_balance("rent") == 0
    assert budget.get_unassigned() == 7000


def test_the_whole_envelope_can_be_moved(budget):
    budget.move("food", "rent", 3000)
    assert budget.get_balance("food") == 0
    assert budget.get_balance("rent") == 3000


def test_moving_more_than_the_source_holds_changes_nothing(budget):
    before = state(budget)
    with pytest.raises(NotEnoughMoney):
        budget.move("food", "fun", 3001)
    assert state(budget) == before


def test_moving_into_the_same_envelope_is_rejected(budget):
    before = state(budget)
    with pytest.raises(ValueError):
        budget.move("food", "food", 100)
    assert state(budget) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda bud: bud.move("travel", "fun", 100),
        lambda bud: bud.move("food", "travel", 100),
        lambda bud: bud.move(None, "fun", 100),
        lambda bud: bud.move("food", 1, 100),
    ],
)
def test_moving_with_a_missing_envelope_raises_key_error(budget, call):
    before = state(budget)
    with pytest.raises(KeyError):
        call(budget)
    assert state(budget) == before


@pytest.mark.parametrize("amount", BAD_AMOUNTS)
def test_moving_an_invalid_amount_is_rejected(budget, amount):
    before = state(budget)
    with pytest.raises(ValueError):
        budget.move("food", "fun", amount)
    assert state(budget) == before


def test_move_error_order(budget):
    with pytest.raises(KeyError):
        budget.move("travel", "travel", -1)  # missing source before everything
    with pytest.raises(KeyError):
        budget.move("food", "travel", -1)  # missing destination before bad amount
    with pytest.raises(ValueError):
        budget.move("food", "food", -1)  # bad amount and same name: ValueError
    with pytest.raises(ValueError):
        budget.move("food", "food", 10**6)  # same name before missing money


# --- allocate_many ----------------------------------------------------------


def test_allocate_many_can_use_all_unassigned_money(budget):
    budget.allocate_many({"fun": 2000, "rent": 5000})
    assert budget.get_unassigned() == 0
    assert budget.get_balance("fun") == 2000
    assert budget.get_balance("rent") == 5000
    assert budget.get_balance("food") == 3000


def test_allocate_many_with_one_envelope_or_none(budget):
    budget.allocate_many({"rent": 500})
    assert budget.get_balance("rent") == 500
    before = state(budget)
    budget.allocate_many({})
    assert state(budget) == before


def test_allocate_many_fails_whole_when_the_total_is_too_much(budget):
    before = state(budget)
    with pytest.raises(NotEnoughMoney):
        budget.allocate_many({"fun": 4000, "rent": 3001})
    assert state(budget) == before


def test_allocate_many_fails_whole_on_a_missing_envelope(budget):
    before = state(budget)
    with pytest.raises(KeyError):
        budget.allocate_many({"fun": 100, "travel": 100})
    with pytest.raises(KeyError):
        budget.allocate_many({"fun": 100, None: 100})
    assert state(budget) == before


@pytest.mark.parametrize("amount", BAD_AMOUNTS)
def test_allocate_many_fails_whole_on_a_bad_amount(budget, amount):
    before = state(budget)
    with pytest.raises(ValueError):
        budget.allocate_many({"fun": 100, "rent": amount})
    assert state(budget) == before


def test_allocate_many_error_order(budget):
    with pytest.raises(KeyError):
        budget.allocate_many({"fun": -1, "travel": 10**6})  # any missing name first
    with pytest.raises(ValueError):
        budget.allocate_many({"fun": 10**6, "rent": -1})  # bad amount before missing money
