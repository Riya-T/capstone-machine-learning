"""Hidden tests for the c_history change (state history). Never shown to the
writer or the editor.

Usage (with workflow.py importable, e.g. in the sandbox):
    python -m pytest changes/c_history/private/test_history_new.py
"""

import pytest
from workflow import InvalidTransition, OrderWorkflow, WorkflowError

STATES = ["new", "paid", "shipped", "delivered", "cancelled"]


@pytest.fixture
def flow():
    wf = OrderWorkflow()
    wf.create_order("o1", 2500)
    wf.create_order("o2", 900)
    wf.create_order("o3", 400)
    return wf


def record(wf):
    return {o: (wf.get_history(o), wf.get_move_count(o)) for o in wf.get_orders()}


def test_a_new_order_has_only_new_in_its_history(flow):
    assert flow.get_history("o2") == ["new"]
    assert flow.get_move_count("o2") == 0


def test_a_full_journey_is_recorded(flow):
    for s in ["paid", "shipped", "delivered"]:
        flow.move("o1", s)
    assert flow.get_history("o1") == ["new", "paid", "shipped", "delivered"]
    assert flow.get_move_count("o1") == 3
    assert flow.get_history("o2") == ["new"]


def test_the_last_history_entry_is_the_current_state(flow):
    flow.move("o1", "paid")
    flow.move("o1", "cancelled")
    assert flow.get_history("o1")[-1] == flow.get_state("o1") == "cancelled"
    assert flow.get_move_count("o1") == 2


@pytest.mark.parametrize(
    "call",
    [
        lambda wf: wf.move("o1", "delivered"),
        lambda wf: wf.move("o1", "paid"),
        lambda wf: wf.move("o1", "refunded"),
        lambda wf: wf.move("o9", "paid"),
        lambda wf: wf.create_order("o1", 100),
    ],
)
def test_failed_calls_leave_every_history_unchanged(flow, call):
    flow.move("o1", "paid")
    before = record(flow)
    with pytest.raises((KeyError, ValueError, WorkflowError)):
        call(flow)
    assert record(flow) == before


def test_a_final_order_refuses_moves_without_recording_them(flow):
    flow.move("o3", "cancelled")
    for s in STATES:
        with pytest.raises(InvalidTransition):
            flow.move("o3", s)
    assert flow.get_history("o3") == ["new", "cancelled"]
    assert flow.get_move_count("o3") == 1


def test_orders_that_passed_keep_creation_order(flow):
    flow.move("o3", "paid")
    flow.move("o1", "paid")
    flow.move("o1", "shipped")
    assert flow.get_orders_that_passed("paid") == ["o1", "o3"]
    assert flow.get_orders_that_passed("shipped") == ["o1"]
    assert flow.get_orders_that_passed("delivered") == []


def test_every_order_has_passed_new(flow):
    flow.move("o2", "cancelled")
    assert flow.get_orders_that_passed("new") == ["o1", "o2", "o3"]


def test_orders_that_passed_differs_from_orders_in(flow):
    flow.move("o1", "paid")
    flow.move("o1", "shipped")
    assert flow.get_orders_in("paid") == []
    assert flow.get_orders_that_passed("paid") == ["o1"]


@pytest.mark.parametrize("name", ["", "Paid", "refunded", None, 1])
def test_unknown_state_names_are_rejected(flow, name):
    with pytest.raises(ValueError):
        flow.get_orders_that_passed(name)


@pytest.mark.parametrize("order_id", ["o9", None, 1])
def test_orders_that_do_not_exist_raise_key_error(flow, order_id):
    with pytest.raises(KeyError):
        flow.get_history(order_id)
    with pytest.raises(KeyError):
        flow.get_move_count(order_id)


def test_queries_do_not_change_the_orders(flow):
    flow.move("o1", "paid")
    flow.get_history("o1")
    flow.get_orders_that_passed("paid")
    assert flow.get_state("o1") == "paid"
    flow.move("o1", "shipped")
    assert flow.get_history("o1") == ["new", "paid", "shipped"]
