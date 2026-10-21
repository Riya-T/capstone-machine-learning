"""Public checks for the c_priority change (queries by status and priority).
Shown to the editor, never to the writer.

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
    d.assign("T1", "kim")
    d.assign("T4", "kim")
    d.assign("T2", "lee")
    d.resolve("T4")
    return d


def test_queue_puts_the_highest_priority_first_then_opening_order(desk):
    assert desk.get_queue() == ["T2", "T1", "T3"]
    assert desk.get_queue("kim") == ["T1"]
    assert desk.get_queue(min_priority=3) == ["T2"]


def test_tickets_can_be_filtered_by_status(desk):
    assert desk.get_tickets(status="open") == ["T3"]
    assert desk.get_tickets(status="assigned") == ["T1", "T2"]
    assert desk.get_tickets("kim", status="resolved") == ["T4"]
    with pytest.raises(ValueError):
        desk.get_tickets(status="closed")


def test_priority_counts_cover_unresolved_tickets(desk):
    assert desk.get_priority_counts() == [(5, 1), (2, 2)]
