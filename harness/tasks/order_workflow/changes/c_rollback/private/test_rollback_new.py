"""Hidden tests for the c_rollback change (rolling back a move). Never shown
to the writer or the editor.

Usage (with workflow.py importable, e.g. in the sandbox):
    python -m pytest changes/c_rollback/private/test_rollback_new.py
"""

import pytest
from workflow import InvalidTransition, OrderWorkflow, WorkflowError


@pytest.fixture
def flow():
    wf = OrderWorkflow()
    wf.create_order("o1", 2500)
    wf.create_order("o2", 900)
    return wf


def state(wf):
    return {o: (wf.get_state(o), wf.get_total(o)) for o in wf.get_orders()}


def test_a_cancelled_order_can_be_restored(flow):
    flow.move("o1", "cancelled")
    flow.rollback("o1")
    assert flow.get_state("o1") == "new"
    assert flow.get_orders_in("new") == ["o1", "o2"]
    assert flow.get_orders_in("cancelled") == []


def test_rollback_walks_back_through_every_move(flow):
    flow.move("o1", "paid")
    flow.move("o1", "shipped")
    flow.rollback("o1")
    assert flow.get_state("o1") == "paid"
    flow.rollback("o1")
    assert flow.get_state("o1") == "new"


def test_a_restored_order_can_take_another_path(flow):
    flow.move("o1", "paid")
    flow.move("o1", "cancelled")
    flow.rollback("o1")
    flow.move("o1", "shipped")
    flow.move("o1", "delivered")
    assert flow.get_state("o1") == "delivered"


def test_moves_after_a_rollback_can_be_rolled_back_too(flow):
    flow.move("o1", "cancelled")
    flow.rollback("o1")
    flow.move("o1", "paid")
    flow.move("o1", "cancelled")
    flow.rollback("o1")
    assert flow.get_state("o1") == "paid"
    flow.rollback("o1")
    assert flow.get_state("o1") == "new"
    with pytest.raises(WorkflowError):
        flow.rollback("o1")


def test_a_restored_order_follows_the_normal_rules(flow):
    flow.move("o1", "paid")
    flow.rollback("o1")
    with pytest.raises(InvalidTransition):
        flow.move("o1", "shipped")
    assert flow.get_state("o1") == "new"


def test_a_new_order_has_nothing_to_roll_back(flow):
    before = state(flow)
    with pytest.raises(WorkflowError):
        flow.rollback("o1")
    assert state(flow) == before


def test_rolling_back_a_delivery_is_refused_and_changes_nothing(flow):
    for s in ["paid", "shipped", "delivered"]:
        flow.move("o1", s)
    before = state(flow)
    with pytest.raises(InvalidTransition):
        flow.rollback("o1")
    assert state(flow) == before
    assert flow.get_orders_in("delivered") == ["o1"]


def test_a_shipped_order_can_be_rolled_back(flow):
    flow.move("o1", "paid")
    flow.move("o1", "shipped")
    flow.rollback("o1")
    assert flow.get_orders_in("paid") == ["o1"]
    assert flow.get_orders_in("shipped") == []


@pytest.mark.parametrize("order_id", ["o9", None, 1])
def test_orders_that_do_not_exist_raise_key_error(flow, order_id):
    before = state(flow)
    with pytest.raises(KeyError):
        flow.rollback(order_id)
    assert state(flow) == before


def test_rollback_only_affects_its_own_order(flow):
    flow.move("o1", "paid")
    flow.move("o2", "paid")
    flow.rollback("o2")
    assert flow.get_state("o1") == "paid"
    assert flow.get_state("o2") == "new"


def test_rollback_keeps_the_total(flow):
    flow.move("o1", "paid")
    flow.rollback("o1")
    assert flow.get_total("o1") == 2500


def test_a_failed_move_cannot_be_rolled_back(flow):
    with pytest.raises(InvalidTransition):
        flow.move("o1", "delivered")
    with pytest.raises(WorkflowError):
        flow.rollback("o1")
