"""Public checks for the c_net_query change (net views of the debts). Shown
to the editor, never to the writer.

Usage (with ious.py importable, e.g. in the sandbox):
    python -m pytest changes/c_net_query/public/test_net_query_public.py
"""

import pytest
from ious import IouTracker


@pytest.fixture
def tracker():
    trk = IouTracker()
    trk.add_user("alice")
    trk.add_user("bob")
    trk.add_user("carol")
    trk.record_iou("alice", "bob", 1000)
    trk.record_iou("bob", "alice", 400)
    trk.record_iou("carol", "alice", 100)
    return trk


def test_net_owed_cancels_the_two_directions(tracker):
    assert tracker.get_net_owed("alice", "bob") == 600
    assert tracker.get_net_owed("bob", "alice") == -600
    assert tracker.get_net_owed("alice", "carol") == -100


def test_net_owed_to_lists_only_users_who_owe_on_net(tracker):
    assert tracker.get_net_owed_to("alice") == [("bob", 600)]
    assert tracker.get_net_owed_to("bob") == []
    assert tracker.get_owed_to("bob") == [("alice", 400)]


def test_debtors_and_creditors_come_from_the_balances(tracker):
    assert tracker.get_debtors() == ["bob"]
    assert tracker.get_creditors() == ["alice", "carol"]
