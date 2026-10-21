"""Hidden tests for the initial ticket_desk spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with desk.py importable, e.g. in the sandbox):
    python -m pytest private/test_desk_initial.py
"""

import pytest
from desk import DeskError, TicketDesk

BAD_PRIORITIES = [0, -4, 1.5, "3", None]
AGENTS = ["kim", "lee"]


@pytest.fixture
def desk():
    d = TicketDesk()
    for agent in AGENTS:
        d.add_agent(agent)
    d.open_ticket("T1", 2)
    d.open_ticket("T2", 5)
    d.open_ticket("T3", 1)
    return d


def state(d):
    """Every ticket's status and priority plus every queue, to check that a
    failed call changed nothing."""
    tickets = {t: (d.get_status(t), d.get_priority(t)) for t in d.get_tickets()}
    queues = {a: d.get_tickets(a) for a in AGENTS}
    return tickets, queues


# --- agents -----------------------------------------------------------------


@pytest.mark.parametrize("bad_id", [""])
def test_invalid_agent_ids_are_rejected(bad_id):
    d = TicketDesk()
    with pytest.raises(ValueError):
        d.add_agent(bad_id)


def test_adding_an_agent_twice_is_rejected(desk):
    desk.assign("T1", "kim")
    with pytest.raises(DeskError):
        desk.add_agent("kim")
    assert desk.get_tickets("kim") == ["T1"]


@pytest.mark.parametrize(
    "call",
    [
        lambda d: d.assign("T1", "max"),
        lambda d: d.get_tickets("max"),
        lambda d: d.assign("T1", 1),
        lambda d: d.get_tickets(1),
    ],
)
def test_agents_that_do_not_exist_raise_key_error(desk, call):
    before = state(desk)
    with pytest.raises(KeyError):
        call(desk)
    assert state(desk) == before


def test_a_new_agent_has_an_empty_queue(desk):
    assert desk.get_tickets("kim") == []
    assert desk.get_tickets("lee") == []


# --- opening tickets --------------------------------------------------------


def test_tickets_are_listed_in_opening_order():
    d = TicketDesk()
    for ticket in ["T7", "T2", "T5"]:
        d.open_ticket(ticket, 1)
    assert d.get_tickets() == ["T7", "T2", "T5"]


def test_a_new_ticket_is_open_with_its_priority(desk):
    assert desk.get_status("T2") == "open"
    assert desk.get_priority("T2") == 5
    assert desk.get_priority("T3") == 1


@pytest.mark.parametrize("bad_id", [""])
def test_invalid_ticket_ids_are_rejected(desk, bad_id):
    with pytest.raises(ValueError):
        desk.open_ticket(bad_id, 1)
    assert desk.get_tickets() == ["T1", "T2", "T3"]


@pytest.mark.parametrize("priority", BAD_PRIORITIES)
def test_invalid_priorities_are_rejected(desk, priority):
    before = state(desk)
    with pytest.raises(ValueError):
        desk.open_ticket("T4", priority)
    assert state(desk) == before
    assert desk.get_tickets() == ["T1", "T2", "T3"]


def test_opening_a_ticket_twice_is_rejected(desk):
    desk.assign("T1", "kim")
    before = state(desk)
    with pytest.raises(DeskError):
        desk.open_ticket("T1", 9)
    assert state(desk) == before


def test_a_bad_ticket_id_is_reported_before_a_bad_priority(desk):
    with pytest.raises(ValueError):
        desk.open_ticket("", 0)


def test_a_bad_priority_is_reported_before_a_duplicate_ticket(desk):
    with pytest.raises(ValueError):
        desk.open_ticket("T1", 0)
    assert desk.get_priority("T1") == 2


@pytest.mark.parametrize(
    "call",
    [
        lambda d: d.assign("T9", "kim"),
        lambda d: d.resolve("T9"),
        lambda d: d.get_status("T9"),
        lambda d: d.get_priority("T9"),
        lambda d: d.get_status(None),
        lambda d: d.assign(1, "kim"),
    ],
)
def test_tickets_that_do_not_exist_raise_key_error(desk, call):
    desk.assign("T1", "kim")
    before = state(desk)
    with pytest.raises(KeyError):
        call(desk)
    assert state(desk) == before


# --- assigning and resolving ------------------------------------------------


def test_queues_keep_opening_order_not_assignment_order(desk):
    desk.assign("T3", "kim")
    desk.assign("T1", "kim")
    desk.assign("T2", "lee")
    assert desk.get_tickets("kim") == ["T1", "T3"]
    assert desk.get_tickets("lee") == ["T2"]
    assert desk.get_status("T3") == "assigned"


def test_reassigning_takes_the_ticket_from_the_first_agent(desk):
    desk.assign("T1", "kim")
    desk.assign("T2", "kim")
    desk.assign("T1", "lee")
    assert desk.get_tickets("kim") == ["T2"]
    assert desk.get_tickets("lee") == ["T1"]
    assert desk.get_status("T1") == "assigned"


def test_assigning_to_the_agent_who_has_it_is_rejected(desk):
    desk.assign("T1", "kim")
    before = state(desk)
    with pytest.raises(DeskError):
        desk.assign("T1", "kim")
    assert state(desk) == before


def test_a_resolved_ticket_cannot_be_assigned(desk):
    desk.assign("T1", "kim")
    desk.resolve("T1")
    before = state(desk)
    with pytest.raises(DeskError):
        desk.assign("T1", "lee")
    with pytest.raises(DeskError):
        desk.assign("T1", "kim")
    assert state(desk) == before


def test_resolving_removes_the_ticket_from_the_queue_only(desk):
    desk.assign("T1", "kim")
    desk.assign("T2", "kim")
    desk.resolve("T1")
    assert desk.get_status("T1") == "resolved"
    assert desk.get_priority("T1") == 2
    assert desk.get_tickets("kim") == ["T2"]
    assert desk.get_tickets() == ["T1", "T2", "T3"]


def test_resolving_twice_is_rejected(desk):
    desk.assign("T1", "kim")
    desk.resolve("T1")
    before = state(desk)
    with pytest.raises(DeskError):
        desk.resolve("T1")
    assert state(desk) == before


def test_resolving_an_open_ticket_changes_nothing(desk):
    before = state(desk)
    with pytest.raises(DeskError):
        desk.resolve("T2")
    assert state(desk) == before


def test_an_unknown_ticket_is_reported_before_an_unknown_agent(desk):
    with pytest.raises(KeyError):
        desk.assign("T9", "max")


def test_an_unknown_agent_is_reported_before_a_resolved_ticket(desk):
    desk.assign("T1", "kim")
    desk.resolve("T1")
    with pytest.raises(KeyError):
        desk.assign("T1", "max")


def test_failed_calls_leave_queues_unchanged(desk):
    desk.assign("T1", "kim")
    for call in (
        lambda: desk.assign("T1", "kim"),
        lambda: desk.assign("T9", "lee"),
        lambda: desk.assign("T2", "max"),
        lambda: desk.resolve("T2"),
        lambda: desk.open_ticket("T2", 3),
    ):
        with pytest.raises((DeskError, KeyError)):
            call()
    assert desk.get_tickets("kim") == ["T1"]
    assert desk.get_tickets("lee") == []
    assert desk.get_status("T2") == "open"


def test_desks_do_not_share_agents_or_tickets():
    first, second = TicketDesk(), TicketDesk()
    first.add_agent("kim")
    first.open_ticket("T1", 1)
    assert second.get_tickets() == []
    with pytest.raises(KeyError):
        second.get_tickets("kim")
    second.add_agent("kim")
    second.open_ticket("T1", 4)
    assert second.get_priority("T1") == 4
