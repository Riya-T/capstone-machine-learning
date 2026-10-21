"""Hidden tests for the c_priority change (queries by status and priority).
Never shown to the writer or the editor.

Usage (with desk.py importable, e.g. in the sandbox):
    python -m pytest changes/c_priority/private/test_priority_new.py
"""

import pytest
from desk import TicketDesk

BAD_STATUSES = ["closed", "", 1, "Open"]
BAD_MIN_PRIORITIES = [0, -1, 1.5, "2", None]


@pytest.fixture
def desk():
    d = TicketDesk()
    d.add_agent("kim")
    d.add_agent("lee")
    d.open_ticket("T1", 3)
    d.open_ticket("T2", 7)
    d.open_ticket("T3", 3)
    d.open_ticket("T4", 1)
    d.open_ticket("T5", 7)
    d.assign("T1", "kim")
    d.assign("T2", "lee")
    d.assign("T3", "kim")
    d.assign("T5", "kim")
    return d


def test_status_filter_without_an_agent(desk):
    assert desk.get_tickets(status="open") == ["T4"]
    assert desk.get_tickets(status="assigned") == ["T1", "T2", "T3", "T5"]
    assert desk.get_tickets(status="resolved") == []
    desk.resolve("T3")
    assert desk.get_tickets(status="assigned") == ["T1", "T2", "T5"]
    assert desk.get_tickets(status="resolved") == ["T3"]


def test_status_none_lists_everything(desk):
    desk.resolve("T1")
    assert desk.get_tickets(status=None) == ["T1", "T2", "T3", "T4", "T5"]
    assert desk.get_tickets("kim", status=None) == ["T3", "T5"]


def test_status_filter_with_an_agent(desk):
    desk.resolve("T1")
    assert desk.get_tickets("kim", status="assigned") == ["T3", "T5"]
    assert desk.get_tickets("kim", status="resolved") == ["T1"]
    assert desk.get_tickets("kim", status="open") == []
    assert desk.get_tickets("lee", status="resolved") == []


def test_resolved_tickets_stay_with_the_agent_who_resolved_them(desk):
    desk.assign("T1", "lee")
    desk.resolve("T1")
    desk.resolve("T2")
    assert desk.get_tickets("lee", status="resolved") == ["T1", "T2"]
    assert desk.get_tickets("kim", status="resolved") == []
    assert desk.get_tickets("lee") == []


@pytest.mark.parametrize("status", BAD_STATUSES)
def test_invalid_statuses_are_rejected(desk, status):
    with pytest.raises(ValueError):
        desk.get_tickets(status=status)
    with pytest.raises(ValueError):
        desk.get_tickets("kim", status=status)


def test_an_unknown_agent_is_reported_before_a_bad_status(desk):
    with pytest.raises(KeyError):
        desk.get_tickets("max", status="closed")
    with pytest.raises(KeyError):
        desk.get_tickets("max", status="open")


def test_queue_orders_by_priority_then_opening_order(desk):
    assert desk.get_queue() == ["T2", "T5", "T1", "T3", "T4"]
    desk.open_ticket("T6", 7)
    assert desk.get_queue() == ["T2", "T5", "T6", "T1", "T3", "T4"]


def test_queue_leaves_resolved_tickets_out(desk):
    desk.resolve("T2")
    desk.resolve("T1")
    assert desk.get_queue() == ["T5", "T3", "T4"]
    assert desk.get_queue("kim") == ["T5", "T3"]


def test_queue_for_an_agent(desk):
    assert desk.get_queue("kim") == ["T5", "T1", "T3"]
    assert desk.get_queue("lee") == ["T2"]
    desk.add_agent("max")
    assert desk.get_queue("max") == []


def test_queue_with_a_minimum_priority(desk):
    assert desk.get_queue(min_priority=3) == ["T2", "T5", "T1", "T3"]
    assert desk.get_queue(min_priority=7) == ["T2", "T5"]
    assert desk.get_queue(min_priority=8) == []
    assert desk.get_queue("kim", min_priority=4) == ["T5"]
    assert desk.get_queue("kim", 3) == ["T5", "T1", "T3"]


@pytest.mark.parametrize("value", BAD_MIN_PRIORITIES)
def test_invalid_minimum_priorities_are_rejected(desk, value):
    with pytest.raises(ValueError):
        desk.get_queue(min_priority=value)
    with pytest.raises(ValueError):
        desk.get_queue("kim", min_priority=value)


def test_queue_rejects_unknown_agents_first(desk):
    with pytest.raises(KeyError):
        desk.get_queue("max")
    with pytest.raises(KeyError):
        desk.get_queue("max", min_priority=0)
    with pytest.raises(KeyError):
        desk.get_queue(1)


def test_priority_counts_highest_first(desk):
    assert desk.get_priority_counts() == [(7, 2), (3, 2), (1, 1)]
    desk.resolve("T2")
    desk.resolve("T5")
    assert desk.get_priority_counts() == [(3, 2), (1, 1)]


def test_priority_counts_of_an_empty_desk():
    d = TicketDesk()
    assert d.get_priority_counts() == []
    assert d.get_queue() == []
