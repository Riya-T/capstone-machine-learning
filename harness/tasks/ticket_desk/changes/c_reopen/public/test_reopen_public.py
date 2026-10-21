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
    d.assign("T1", "kim")
    d.resolve("T1")
    d.reopen("T1")
    assert d.get_status("T1") == "assigned"
    assert d.get_tickets("kim") == ["T1"]
    assert d.get_reopen_count("T1") == 1


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
