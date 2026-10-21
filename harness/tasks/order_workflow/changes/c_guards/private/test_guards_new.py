"""Hidden tests for the c_guards change (transition guards). Never shown to
the writer or the editor.

Usage (with workflow.py importable, e.g. in the sandbox):
    python -m pytest changes/c_guards/private/test_guards_new.py
"""

import pytest
from workflow import GuardFailed, InvalidTransition, OrderWorkflow, WorkflowError

BAD_AMOUNTS = [0, -5, 1.5, "10", True, None]


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


@pytest.mark.parametrize("address", ["", None, 5])
def test_invalid_addresses_are_rejected(flow, address):
    with pytest.raises(ValueError):
        flow.set_address("o1", address)
    assert flow.get_address("o1") == ""
    flow.move("o2", "cancelled")  # a bad address is reported before the state check
    with pytest.raises(ValueError):
        flow.set_address("o2", address)


def test_an_invalid_transition_is_reported_before_a_guard(flow):
    with pytest.raises(InvalidTransition):
        flow.move("o1", "shipped")
    flow.move("o2", "cancelled")
    with pytest.raises(InvalidTransition):
        flow.move("o2", "paid")


@pytest.mark.parametrize("method", ["get_paid", "get_address"])
@pytest.mark.parametrize("order_id", ["o9", None, 1])
def test_orders_that_do_not_exist_raise_key_error(flow, method, order_id):
    with pytest.raises(KeyError):
        getattr(flow, method)(order_id)
    with pytest.raises(KeyError):
        flow.record_payment(order_id, -1)
    with pytest.raises(KeyError):
        flow.set_address(order_id, "")


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
