"""Public checks for the c_history change (state history). Shown to the
editor, never to the writer.

Usage (with workflow.py importable, e.g. in the sandbox):
    python -m pytest changes/c_history/public/test_history_public.py
"""

from workflow import OrderWorkflow


def test_history_lists_every_state_oldest_first():
    wf = OrderWorkflow()
    wf.create_order("o1", 500)
    assert wf.get_history("o1") == ["new"]
    assert wf.get_move_count("o1") == 0
    wf.move("o1", "paid")
    wf.move("o1", "shipped")
    assert wf.get_history("o1") == ["new", "paid", "shipped"]
    assert wf.get_move_count("o1") == 2


def test_orders_that_passed_a_state_include_ones_that_left_it():
    wf = OrderWorkflow()
    wf.create_order("o1", 500)
    wf.create_order("o2", 700)
    wf.move("o2", "paid")
    wf.move("o2", "cancelled")
    wf.move("o1", "paid")
    assert wf.get_orders_that_passed("paid") == ["o1", "o2"]
    assert wf.get_orders_that_passed("cancelled") == ["o2"]
    assert wf.get_orders_that_passed("new") == ["o1", "o2"]
