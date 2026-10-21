"""Public checks for the c_limit change (per-agent queue limits). Shown to
the editor, never to the writer.

Usage (with desk.py importable, e.g. in the sandbox):
    python -m pytest changes/c_limit/public/test_limit_public.py
"""

import pytest
from desk import AgentFull, TicketDesk


def test_a_full_agent_takes_no_more_tickets():
    d = TicketDesk()
    d.add_agent("kim", limit=1)
    d.open_ticket("T1", 1)
    d.open_ticket("T2", 1)
    d.assign("T1", "kim")
    with pytest.raises(AgentFull):
        d.assign("T2", "kim")
    assert d.get_tickets("kim") == ["T1"]
    assert d.get_status("T2") == "open"
    assert d.get_limit("kim") == 1


def test_agents_have_no_limit_by_default():
    d = TicketDesk()
    d.add_agent("kim")
    assert d.get_limit("kim") is None
    for n in range(5):
        d.open_ticket(f"T{n}", 1)
        d.assign(f"T{n}", "kim")
    assert len(d.get_tickets("kim")) == 5
