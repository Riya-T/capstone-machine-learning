"""Public checks for workflow.py.

Usage (with workflow.py importable, e.g. in the sandbox):
    python -m pytest public/test_workflow_public.py
"""

import pytest
from workflow import InvalidTransition, OrderWorkflow


@pytest.fixture
def flow():
    wf = OrderWorkflow()
    wf.create_order("o1", 2500)
    wf.create_order("o2", 900)
    return wf


def test_a_new_order_starts_in_new(flow):
    assert flow.get_state("o1") == "new"
    assert flow.get_total("o1") == 2500
    assert flow.get_orders() == ["o1", "o2"]


def test_an_order_moves_along_the_happy_path(flow):
    flow.move("o1", "paid")
    flow.move("o1", "shipped")
    flow.move("o1", "delivered")
    assert flow.get_state("o1") == "delivered"


def test_skipping_a_step_raises(flow):
    with pytest.raises(InvalidTransition):
        flow.move("o1", "shipped")
    assert flow.get_state("o1") == "new"


def test_orders_in_a_state_are_listed_in_creation_order(flow):
    flow.move("o2", "paid")
    flow.move("o1", "paid")
    assert flow.get_orders_in("paid") == ["o1", "o2"]
    assert flow.get_orders_in("new") == []


def test_totals_must_be_positive(flow):
    with pytest.raises(ValueError):
        flow.create_order("o3", -5)
    assert flow.get_orders() == ["o1", "o2"]


def test_unknown_order_raises_key_error(flow):
    with pytest.raises(KeyError):
        flow.get_state("o9")
    with pytest.raises(KeyError):
        flow.move("o9", "paid")
