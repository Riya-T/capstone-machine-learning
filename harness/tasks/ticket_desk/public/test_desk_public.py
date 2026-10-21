"""Public checks for desk.py.

Usage (with desk.py importable, e.g. in the sandbox):
    python -m pytest public/test_desk_public.py
"""

import pytest
from desk import DeskError, TicketDesk


@pytest.fixture
def desk():
    d = TicketDesk()
    d.add_agent("kim")
    d.add_agent("lee")
    d.open_ticket("T1", 2)
    d.open_ticket("T2", 5)
    return d


def test_a_new_ticket_is_open(desk):
    assert desk.get_status("T1") == "open"
    assert desk.get_priority("T1") == 2
    assert desk.get_tickets() == ["T1", "T2"]


def test_assign_then_resolve(desk):
    desk.assign("T1", "kim")
    assert desk.get_status("T1") == "assigned"
    assert desk.get_tickets("kim") == ["T1"]
    desk.resolve("T1")
    assert desk.get_status("T1") == "resolved"
    assert desk.get_tickets("kim") == []
    assert desk.get_tickets() == ["T1", "T2"]


def test_reassigning_moves_the_ticket(desk):
    desk.assign("T1", "kim")
    desk.assign("T1", "lee")
    assert desk.get_tickets("kim") == []
    assert desk.get_tickets("lee") == ["T1"]


def test_an_open_ticket_cannot_be_resolved(desk):
    with pytest.raises(DeskError):
        desk.resolve("T1")
    assert desk.get_status("T1") == "open"


def test_priorities_must_be_positive(desk):
    with pytest.raises(ValueError):
        desk.open_ticket("T3", 0)
    with pytest.raises(ValueError):
        desk.open_ticket("T3", -1)


def test_unknown_ticket_raises_key_error(desk):
    with pytest.raises(KeyError):
        desk.get_status("T9")
