"""Hidden tests for the c_priority change (queries by priority and resolved
tickets). Never shown to the writer or the editor.

Usage (with desk.py importable, e.g. in the sandbox):
    python -m pytest changes/c_priority/private/test_priority_new.py
"""

import pytest
from desk import TicketDesk

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
    d.assign("T3", "kim")
    d.assign("T5", "kim")
    d.assign("T1", "kim")
    d.assign("T2", "lee")
    return d  # kim's queue: T3, T5, T1; lee's: T2; T4 has no agent


def test_by_priority_orders_by_priority_then_opening_order(desk):
    assert desk.get_by_priority() == ["T2", "T5", "T1", "T3", "T4"]
    desk.open_ticket("T6", 7)
    assert desk.get_by_priority() == ["T2", "T5", "T6", "T1", "T3", "T4"]


def test_an_agents_tickets_break_ties_in_the_order_the_agent_got_them(desk):
    assert desk.get_by_priority("kim") == ["T5", "T3", "T1"]
    assert desk.get_by_priority("lee") == ["T2"]
    desk.add_agent("max")
    assert desk.get_by_priority("max") == []


def test_by_priority_follows_reassignment(desk):
    desk.reassign("T3", "lee")
    desk.reassign("T1", "lee")
    assert desk.get_by_priority("lee") == ["T2", "T3", "T1"]
    assert desk.get_by_priority("kim") == ["T5"]
    assert desk.get_by_priority() == ["T2", "T5", "T1", "T3", "T4"]


def test_by_priority_leaves_resolved_tickets_out(desk):
    desk.resolve("T2")
    desk.resolve("T1")
    assert desk.get_by_priority() == ["T5", "T3", "T4"]
    assert desk.get_by_priority("kim") == ["T5", "T3"]
    assert desk.get_by_priority("lee") == []


def test_by_priority_with_a_minimum_priority(desk):
    assert desk.get_by_priority(min_priority=3) == ["T2", "T5", "T1", "T3"]
    assert desk.get_by_priority(min_priority=7) == ["T2", "T5"]
    assert desk.get_by_priority(min_priority=8) == []
    assert desk.get_by_priority("kim", min_priority=4) == ["T5"]
    assert desk.get_by_priority("kim", 3) == ["T5", "T3", "T1"]


@pytest.mark.parametrize("value", BAD_MIN_PRIORITIES)
def test_invalid_minimum_priorities_are_rejected(desk, value):
    with pytest.raises(ValueError):
        desk.get_by_priority(min_priority=value)
    with pytest.raises(ValueError):
        desk.get_by_priority("kim", min_priority=value)


def test_by_priority_rejects_unknown_agents_first(desk):
    with pytest.raises(KeyError):
        desk.get_by_priority("max")
    with pytest.raises(KeyError):
        desk.get_by_priority("max", min_priority=0)
    with pytest.raises(KeyError):
        desk.get_by_priority(1)


def test_priority_counts_highest_first(desk):
    assert desk.get_priority_counts() == [(7, 2), (3, 2), (1, 1)]
    desk.resolve("T2")
    desk.resolve("T5")
    assert desk.get_priority_counts() == [(3, 2), (1, 1)]


def test_resolved_tickets_are_listed_in_opening_order(desk):
    assert desk.get_resolved() == []
    desk.resolve("T3")
    desk.resolve("T1")
    assert desk.get_resolved() == ["T1", "T3"]
    assert desk.get_resolved("kim") == ["T1", "T3"]
    assert desk.get_resolved("lee") == []


def test_resolved_tickets_stay_with_the_agent_who_resolved_them(desk):
    desk.reassign("T1", "lee")
    desk.resolve("T1")
    desk.resolve("T2")
    assert desk.get_resolved("lee") == ["T1", "T2"]
    assert desk.get_resolved("kim") == []
    assert desk.get_queue("lee") == []


def test_get_resolved_rejects_unknown_agents(desk):
    with pytest.raises(KeyError):
        desk.get_resolved("max")
    with pytest.raises(KeyError):
        desk.get_resolved(1)


def test_queries_change_nothing(desk):
    desk.resolve("T3")
    desk.get_by_priority()
    desk.get_by_priority("kim", min_priority=5)
    desk.get_priority_counts()
    desk.get_resolved("kim")
    assert desk.get_queue("kim") == ["T5", "T1"]
    assert desk.get_queue("lee") == ["T2"]
    assert desk.get_resolved() == ["T3"]
    assert desk.get_by_priority() == ["T2", "T5", "T1", "T4"]


def test_queries_on_an_empty_desk():
    d = TicketDesk()
    assert d.get_priority_counts() == []
    assert d.get_by_priority() == []
    assert d.get_resolved() == []


def test_a_reopened_ticket_is_no_longer_resolved(desk):
    desk.resolve("T1")
    desk.resolve("T5")
    assert desk.get_resolved("kim") == ["T1", "T5"]
    assert desk.get_priority_counts() == [(7, 1), (3, 1), (1, 1)]
    desk.reopen("T1")
    assert desk.get_resolved() == ["T5"]
    assert desk.get_resolved("kim") == ["T5"]
    assert desk.get_by_priority("kim") == ["T3", "T1"]
    assert desk.get_by_priority() == ["T2", "T1", "T3", "T4"]
    assert desk.get_priority_counts() == [(7, 1), (3, 2), (1, 1)]
