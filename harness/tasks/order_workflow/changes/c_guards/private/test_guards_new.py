"""Hidden tests for the c_guards change (transition guards). Never shown to
the writer or the editor.

Usage (with workflow.py importable, e.g. in the sandbox):
    python -m pytest changes/c_guards/private/test_guards_new.py
"""

import pytest
from workflow import GuardFailed, InvalidTransition, OrderWorkflow, WorkflowError

BAD_AMOUNTS = [0, -5, 1.5, "10", None]


@pytest.fixture
def flow():
    wf = OrderWorkflow(guarded=True)
    wf.create_order("o1", 1000)
    wf.create_order("o2", 500)
    return wf


def state(wf):
    return {
        o: (wf.get_state(o), wf.get_history(o), wf.get_paid(o), wf.get_address(o))
        for o in wf.get_orders()
    }


def pay_and_address(wf, order_id):
    wf.record_payment(order_id, wf.get_total(order_id) - wf.get_paid(order_id))
    wf.set_address(order_id, "1 Main St")


def test_a_new_order_has_no_payments_and_no_address(flow):
    assert flow.get_paid("o1") == 0
    assert flow.get_address("o1") == ""


def test_payments_may_reach_but_never_pass_the_total(flow):
    flow.record_payment("o1", 300)
    flow.record_payment("o1", 700)
    assert flow.get_paid("o1") == 1000
    before = state(flow)
    with pytest.raises(ValueError):
        flow.record_payment("o1", 1)
    assert state(flow) == before
    flow.record_payment("o2", 200)
    with pytest.raises(ValueError):
        flow.record_payment("o2", 301)
    assert flow.get_paid("o2") == 200
    flow.record_payment("o2", 300)
    assert flow.get_paid("o2") == 500


@pytest.mark.parametrize("amount", BAD_AMOUNTS)
def test_invalid_payment_amounts_are_rejected(flow, amount):
    before = state(flow)
    with pytest.raises(ValueError):
        flow.record_payment("o1", amount)
    assert state(flow) == before


def test_moves_refused_by_a_guard_change_nothing(flow):
    flow.record_payment("o1", 999)
    before = state(flow)
    with pytest.raises(GuardFailed):
        flow.move("o1", "paid")
    assert state(flow) == before
    flow.record_payment("o1", 1)
    flow.move("o1", "paid")
    before = state(flow)
    with pytest.raises(GuardFailed):
        flow.move("o1", "shipped")
    assert state(flow) == before


def test_cancelling_and_delivering_are_not_guarded(flow):
    flow.move("o2", "cancelled")
    assert flow.get_state("o2") == "cancelled"
    flow.record_payment("o2", 100)  # payments may be recorded in any state
    assert flow.get_paid("o2") == 100
    pay_and_address(flow, "o1")
    for s in ["paid", "shipped", "delivered"]:
        flow.move("o1", s)
    assert flow.get_history("o1") == ["new", "paid", "shipped", "delivered"]


def test_the_address_can_be_set_and_replaced_while_new_or_paid(flow):
    flow.set_address("o1", "9 Elm Rd")
    flow.record_payment("o1", 1000)
    flow.move("o1", "paid")
    flow.move("o1", "shipped")
    assert flow.get_address("o1") == "9 Elm Rd"
    flow.set_address("o2", "1 Main St")
    flow.record_payment("o2", 500)
    flow.move("o2", "paid")
    flow.set_address("o2", "2 Side St")
    assert flow.get_address("o2") == "2 Side St"


@pytest.mark.parametrize("path", [["paid", "shipped"], ["paid", "shipped", "delivered"], ["cancelled"]])
def test_the_address_is_fixed_after_shipping_or_cancelling(flow, path):
    pay_and_address(flow, "o1")
    for s in path:
        flow.move("o1", s)
    before = state(flow)
    with pytest.raises(WorkflowError):
        flow.set_address("o1", "3 New St")
    assert state(flow) == before


@pytest.mark.parametrize("address", ["", None])
def test_invalid_addresses_are_rejected(flow, address):
    flow.set_address("o2", "1 Main St")
    before = state(flow)
    with pytest.raises(ValueError):
        flow.set_address("o1", address)
    with pytest.raises(ValueError):
        flow.set_address("o2", address)
    assert flow.get_address("o1") == ""
    assert flow.get_address("o2") == "1 Main St"
    assert state(flow) == before


def test_guarded_moves_still_follow_the_allowed_paths(flow):
    pay_and_address(flow, "o1")
    before = state(flow)
    with pytest.raises(InvalidTransition):
        flow.move("o1", "shipped")  # paid and addressed, but still "new"
    assert state(flow) == before
    flow.record_payment("o2", 500)
    flow.move("o2", "cancelled")
    with pytest.raises(InvalidTransition):
        flow.move("o2", "paid")  # fully paid, but cancelled is final
    assert flow.get_state("o2") == "cancelled"


@pytest.mark.parametrize("method", ["get_paid", "get_address"])
@pytest.mark.parametrize("order_id", ["o9", None, 1])
def test_orders_that_do_not_exist_raise_key_error(flow, method, order_id):
    before = state(flow)
    with pytest.raises(KeyError):
        getattr(flow, method)(order_id)
    with pytest.raises(KeyError):
        flow.record_payment(order_id, 100)
    with pytest.raises(KeyError):
        flow.set_address(order_id, "1 Main St")
    assert state(flow) == before


def test_guard_failed_is_a_workflow_error_but_not_an_invalid_transition():
    assert issubclass(GuardFailed, WorkflowError)
    assert not issubclass(GuardFailed, InvalidTransition)


def test_without_guards_payment_rules_still_apply():
    wf = OrderWorkflow(guarded=False)
    wf.create_order("o1", 100)
    with pytest.raises(ValueError):
        wf.record_payment("o1", 101)
    wf.move("o1", "paid")
    wf.move("o1", "shipped")
    with pytest.raises(WorkflowError):
        wf.set_address("o1", "1 Main St")


# can_move: one order in each situation that matters for a move, as
# (state, fully paid, has an address).
SITUATIONS = {
    "unpaid": ("new", False, False),
    "part_paid": ("new", False, True),
    "paid_up": ("new", True, False),
    "paid_no_address": ("paid", True, False),
    "paid_addressed": ("paid", True, True),
    "shipped": ("shipped", True, True),
    "delivered": ("delivered", True, True),
    "cancelled": ("cancelled", False, False),
}
TARGETS = ["new", "paid", "shipped", "delivered", "cancelled"]
PATHS = {
    ("new", "paid"),
    ("paid", "shipped"),
    ("shipped", "delivered"),
    ("new", "cancelled"),
    ("paid", "cancelled"),
}


def situations(guarded):
    wf = OrderWorkflow(guarded=guarded)
    for name in SITUATIONS:
        wf.create_order(name, 100)
    wf.record_payment("part_paid", 40)
    wf.set_address("part_paid", "1 Main St")
    wf.record_payment("paid_up", 100)
    for name in ["paid_no_address", "paid_addressed", "shipped", "delivered"]:
        wf.record_payment(name, 100)
        wf.move(name, "paid")
    for name in ["paid_addressed", "shipped", "delivered"]:
        wf.set_address(name, "2 Side St")
    wf.move("shipped", "shipped")
    wf.move("delivered", "shipped")
    wf.move("delivered", "delivered")
    wf.move("cancelled", "cancelled")
    return wf


def move_would_succeed(name, target, guarded):
    state, paid_up, addressed = SITUATIONS[name]
    if (state, target) not in PATHS:
        return False
    if guarded and target == "paid" and not paid_up:
        return False
    if guarded and target == "shipped" and not addressed:
        return False
    return True


@pytest.mark.parametrize("guarded", [True, False])
def test_can_move_follows_the_paths_and_the_guards(guarded):
    wf = situations(guarded)
    for name in SITUATIONS:
        for target in TARGETS:
            want = move_would_succeed(name, target, guarded)
            assert bool(wf.can_move(name, target)) == want, (name, target)


def test_can_move_changes_nothing():
    wf = situations(True)
    before = state(wf), {o: wf.get_move_count(o) for o in wf.get_orders()}
    for name in SITUATIONS:
        for target in TARGETS:
            wf.can_move(name, target)
    assert (state(wf), {o: wf.get_move_count(o) for o in wf.get_orders()}) == before


def test_can_move_follows_payments_and_addresses_as_they_change(flow):
    assert not flow.can_move("o1", "paid")
    flow.record_payment("o1", 999)
    assert not flow.can_move("o1", "paid")
    flow.record_payment("o1", 1)
    assert flow.can_move("o1", "paid")
    flow.move("o1", "paid")
    assert not flow.can_move("o1", "shipped")
    assert flow.can_move("o1", "cancelled")
    flow.set_address("o1", "1 Main St")
    assert flow.can_move("o1", "shipped")
    flow.move("o1", "shipped")
    assert flow.can_move("o1", "delivered")
    assert not flow.can_move("o1", "cancelled")
    assert not flow.can_move("o1", "shipped")


@pytest.mark.parametrize("order_id", ["o9", None, 1])
def test_can_move_raises_key_error_for_orders_that_do_not_exist(flow, order_id):
    with pytest.raises(KeyError):
        flow.can_move(order_id, "cancelled")


@pytest.mark.parametrize("name", ["", "Paid", "refunded", None])
def test_can_move_rejects_unknown_state_names(flow, name):
    with pytest.raises(ValueError):
        flow.can_move("o1", name)
