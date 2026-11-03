"""Public checks for the c_priority change (queries by priority and resolved
tickets). Shown to the editor, never to the writer.

Usage (with desk.py importable, e.g. in the sandbox):
    python -m pytest changes/c_priority/public/test_priority_public.py
"""

import pytest
from desk import TicketDesk


@pytest.fixture
def desk():
    d = TicketDesk()
    d.add_agent("kim")
    d.add_agent("lee")
    d.open_ticket("T1", 2)
    d.open_ticket("T2", 5)
    d.open_ticket("T3", 2)
    d.open_ticket("T4", 9)
    d.assign("T3", "kim")
    d.assign("T1", "kim")
    d.assign("T4", "kim")
    d.assign("T2", "lee")
    d.resolve("T4")
    return d


def test_by_priority_puts_the_highest_priority_first(desk):
    assert desk.get_by_priority() == ["T2", "T1", "T3"]
    assert desk.get_by_priority("kim") == ["T3", "T1"]
    assert desk.get_by_priority(min_priority=3) == ["T2"]


def test_resolved_tickets_are_listed_by_agent(desk):
    assert desk.get_resolved() == ["T4"]
    assert desk.get_resolved("kim") == ["T4"]
    assert desk.get_resolved("lee") == []


def test_priority_counts_cover_unresolved_tickets(desk):
    assert desk.get_priority_counts() == [(5, 1), (2, 2)]
