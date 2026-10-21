"""Public checks for the c_thresholds change (adjustable alert limits).
Shown to the editor, never to the writer.

Usage (with spending.py importable, e.g. in the sandbox):
    python -m pytest changes/c_thresholds/public/test_thresholds_public.py
"""

from spending import SpendingTracker


def test_threshold_default_is_unchanged():
    tr = SpendingTracker()
    assert tr.get_threshold("food") == 50000


def test_threshold_from_the_constructor_is_used():
    tr = SpendingTracker(alert_threshold=1000)
    tr.add_account("alice")
    tr.record_payment("alice", 1, "food", 1500)
    assert tr.get_threshold("food") == 1000
    assert tr.get_alerts("alice", 1) == ["food"]


def test_threshold_for_one_category_replaces_the_default():
    tr = SpendingTracker()
    tr.set_category_threshold("rent", 200000)
    tr.add_account("alice")
    tr.record_payment("alice", 1, "rent", 150000)
    tr.record_payment("alice", 1, "food", 60000)
    assert tr.get_threshold("rent") == 200000
    assert tr.get_alerts("alice", 1) == ["food"]
