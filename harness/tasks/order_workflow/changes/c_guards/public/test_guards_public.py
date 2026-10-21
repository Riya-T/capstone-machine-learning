"""Public checks for the c_guards change (transition guards). Shown to the
editor, never to the writer.

Usage (with workflow.py importable, e.g. in the sandbox):
    python -m pytest changes/c_guards/public/test_guards_public.py
"""

import pytest
from workflow import GuardFailed, OrderWorkflow


def test_an_order_must_be_fully_paid_before_it_is_paid():
    wf = OrderWorkflow(guarded=True)
    wf.create_order("o1", 1000)
    wf.record_payment("o1", 400)
    with pytest.raises(GuardFailed):
        wf.move("o1", "paid")
    wf.record_payment("o1", 600)
    assert wf.get_paid("o1") == 1000
    wf.move("o1", "paid")
    assert wf.get_state("o1") == "paid"


def test_an_order_needs_an_address_before_shipping():
    wf = OrderWorkflow(guarded=True)
    wf.create_order("o1", 1000)
    wf.record_payment("o1", 1000)
    wf.move("o1", "paid")
    with pytest.raises(GuardFailed):
        wf.move("o1", "shipped")
    wf.set_address("o1", "1 Main St")
    assert wf.get_address("o1") == "1 Main St"
    wf.move("o1", "shipped")
    assert wf.get_state("o1") == "shipped"


def test_without_guards_moves_work_as_before():
    wf = OrderWorkflow()
    wf.create_order("o1", 1000)
    wf.move("o1", "paid")
    wf.move("o1", "shipped")
    assert wf.get_state("o1") == "shipped"
    assert wf.get_paid("o1") == 0
    assert wf.get_address("o1") == ""
