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


def test_a_new_ticket_has_its_priority_and_no_agent(desk):
    assert desk.get_priority("T1") == 2
    assert desk.get_queue("kim") == []
    assert desk.get_queue("lee") == []


def test_a_queue_keeps_the_order_the_agent_got_the_tickets(desk):
    desk.assign("T2", "kim")
    desk.assign("T1", "kim")
    assert desk.get_queue("kim") == ["T2", "T1"]


def test_reassigning_moves_the_ticket_to_the_end_of_the_new_queue(desk):
    desk.assign("T1", "kim")
    desk.assign("T2", "lee")
    desk.reassign("T1", "lee")
    assert desk.get_queue("kim") == []
    assert desk.get_queue("lee") == ["T2", "T1"]


def test_resolving_takes_the_ticket_out_of_the_queue(desk):
    desk.assign("T1", "kim")
    desk.assign("T2", "kim")
    desk.resolve("T1")
    assert desk.get_queue("kim") == ["T2"]


def test_a_ticket_with_no_agent_cannot_be_resolved_or_reassigned(desk):
    with pytest.raises(DeskError):
        desk.resolve("T1")
    with pytest.raises(DeskError):
        desk.reassign("T1", "kim")
    desk.assign("T1", "kim")
    assert desk.get_queue("kim") == ["T1"]


def test_bad_priorities_and_unknown_ids(desk):
    with pytest.raises(ValueError):
        desk.open_ticket("T3", 0)
    with pytest.raises(ValueError):
        desk.open_ticket("T3", -1)
    with pytest.raises(KeyError):
        desk.get_priority("T9")
    with pytest.raises(KeyError):
        desk.get_queue("max")
