"""Public checks for the c_rollback change (rolling back a move). Shown to
the editor, never to the writer.

Usage (with workflow.py importable, e.g. in the sandbox):
    python -m pytest changes/c_rollback/public/test_rollback_public.py
"""

import pytest
from workflow import InvalidTransition, OrderWorkflow, WorkflowError


def test_rollback_undoes_moves_one_at_a_time():
    wf = OrderWorkflow()
    wf.create_order("o1", 500)
    wf.move("o1", "paid")
    wf.move("o1", "cancelled")
    wf.rollback("o1")
    assert wf.get_state("o1") == "paid"
    wf.rollback("o1")
    assert wf.get_state("o1") == "new"
    with pytest.raises(WorkflowError):
        wf.rollback("o1")


def test_a_delivery_cannot_be_rolled_back():
    wf = OrderWorkflow()
    wf.create_order("o1", 500)
    for s in ["paid", "shipped", "delivered"]:
        wf.move("o1", s)
    with pytest.raises(InvalidTransition):
        wf.rollback("o1")
    assert wf.get_state("o1") == "delivered"
