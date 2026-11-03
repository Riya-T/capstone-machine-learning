"""Public checks for the c_reopen change (reopening resolved tickets). Shown
to the editor, never to the writer.

Usage (with desk.py importable, e.g. in the sandbox):
    python -m pytest changes/c_reopen/public/test_reopen_public.py
"""

import pytest
from desk import DeskError, TicketDesk


def test_reopening_puts_the_ticket_back_with_its_agent():
    d = TicketDesk()
    d.add_agent("kim")
    d.open_ticket("T1", 3)
    d.open_ticket("T2", 1)
    d.assign("T1", "kim")
    d.assign("T2", "kim")
    d.resolve("T1")
    assert d.get_queue("kim") == ["T2"]
    d.reopen("T1")
    assert d.get_queue("kim") == ["T2", "T1"]
    assert d.get_reopen_count("T1") == 1


def test_a_resolved_ticket_stays_on_the_desk():
    d = TicketDesk()
    d.add_agent("kim")
    d.open_ticket("T1", 3)
    d.assign("T1", "kim")
    d.resolve("T1")
    assert d.get_priority("T1") == 3
    with pytest.raises(DeskError):
        d.open_ticket("T1", 2)
    with pytest.raises(DeskError):
        d.assign("T1", "kim")


def test_only_resolved_tickets_can_be_reopened():
    d = TicketDesk()
    d.add_agent("kim")
    d.open_ticket("T1", 3)
    with pytest.raises(DeskError):
        d.reopen("T1")
    d.assign("T1", "kim")
    with pytest.raises(DeskError):
        d.reopen("T1")
    assert d.get_reopen_count("T1") == 0
