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
    for name in ["alice", "bob", "carol", "dave"]:
        trk.add_user(name)
    trk.record_iou("alice", "bob", 1000)
    trk.record_iou("bob", "alice", 400)
    trk.record_iou("carol", "alice", 100)
    trk.record_iou("alice", "dave", 150)
    return trk


def test_net_owed_cancels_the_two_directions(tracker):
    assert tracker.get_net_owed("alice", "bob") == 600
    assert tracker.get_net_owed("bob", "alice") == -600
    assert tracker.get_net_owed("alice", "carol") == -100


def test_net_debts_list_each_pair_once(tracker):
    assert tracker.get_net_debts() == [
        ("alice", "bob", 600),
        ("alice", "dave", 150),
        ("carol", "alice", 100),
    ]
    # get_owed still counts each direction on its own.
    assert tracker.get_owed("alice", "bob") == 1000
    assert tracker.get_owed("bob", "alice") == 400


def test_debtors_and_creditors_come_from_the_net_positions(tracker):
    # alice 600 - 100 + 150 = 650, bob -600, carol 100, dave -150
    assert tracker.get_debtors() == ["bob", "dave"]
    assert tracker.get_creditors() == ["alice", "carol"]


def test_the_lists_are_sorted_by_amount_not_by_user(tracker):
    tracker.record_iou("dave", "carol", 900)
    # alice 650, bob -600, carol 100 - 900 = -800, dave -150 + 900 = 750
    assert tracker.get_net_debts() == [
        ("dave", "carol", 900),
        ("alice", "bob", 600),
        ("alice", "dave", 150),
        ("carol", "alice", 100),
    ]
    assert tracker.get_creditors() == ["dave", "alice"]
    assert tracker.get_debtors() == ["carol", "bob"]
