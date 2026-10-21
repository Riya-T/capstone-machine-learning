"""Hidden tests for the c_reopen change (reopening resolved tickets). Never
shown to the writer or the editor.

Usage (with desk.py importable, e.g. in the sandbox):
    python -m pytest changes/c_reopen/private/test_reopen_new.py
"""

import pytest
from desk import DeskError, TicketDesk

AGENTS = ["kim", "lee"]


@pytest.fixture
def desk():
    d = TicketDesk()
    for agent in AGENTS:
        d.add_agent(agent)
    d.open_ticket("T1", 2)
    d.open_ticket("T2", 5)
    d.open_ticket("T3", 1)
    d.assign("T1", "kim")
    d.assign("T2", "lee")
    d.assign("T3", "kim")
    return d


def state(d):
    tickets = {
        t: (d.get_status(t), d.get_priority(t), d.get_reopen_count(t)) for t in d.get_tickets()
    }
    queues = {a: d.get_tickets(a) for a in AGENTS}
    return tickets, queues


def test_new_tickets_have_a_reopen_count_of_zero(desk):
    desk.open_ticket("T4", 1)
    assert desk.get_reopen_count("T4") == 0
    assert desk.get_reopen_count("T1") == 0


def test_a_reopened_ticket_rejoins_the_queue_in_opening_order(desk):
    desk.resolve("T1")
    assert desk.get_tickets("kim") == ["T3"]
    desk.reopen("T1")
    assert desk.get_tickets("kim") == ["T1", "T3"]
    assert desk.get_tickets("lee") == ["T2"]
    assert desk.get_status("T1") == "assigned"


def test_the_ticket_returns_to_the_agent_who_resolved_it(desk):
    desk.assign("T1", "lee")
    desk.resolve("T1")
    desk.reopen("T1")
    assert desk.get_tickets("lee") == ["T1", "T2"]
    assert desk.get_tickets("kim") == ["T3"]


def test_reopen_count_grows_with_each_reopen(desk):
    for _ in range(3):
        desk.resolve("T1")
        desk.reopen("T1")
    assert desk.get_reopen_count("T1") == 3
    assert desk.get_reopen_count("T3") == 0
    assert desk.get_status("T1") == "assigned"


def test_a_reopened_ticket_can_be_reassigned_and_resolved_again(desk):
    desk.resolve("T1")
    desk.reopen("T1")
    desk.assign("T1", "lee")
    assert desk.get_tickets("lee") == ["T1", "T2"]
    desk.resolve("T1")
    assert desk.get_status("T1") == "resolved"
    assert desk.get_tickets("lee") == ["T2"]
    desk.reopen("T1")
    assert desk.get_tickets("lee") == ["T1", "T2"]
    assert desk.get_reopen_count("T1") == 2


def test_reopening_an_open_or_assigned_ticket_changes_nothing(desk):
    desk.open_ticket("T4", 1)
    before = state(desk)
    with pytest.raises(DeskError):
        desk.reopen("T4")
    with pytest.raises(DeskError):
        desk.reopen("T1")
    assert state(desk) == before


def test_reopen_methods_reject_unknown_tickets(desk):
    with pytest.raises(KeyError):
        desk.reopen("T9")
    with pytest.raises(KeyError):
        desk.get_reopen_count("T9")
    with pytest.raises(KeyError):
        desk.reopen(None)


def test_an_unknown_ticket_is_reported_before_a_not_resolved_ticket(desk):
    with pytest.raises(KeyError):
        desk.reopen(1)


def test_reopening_keeps_priority_and_other_tickets(desk):
    desk.resolve("T1")
    desk.resolve("T2")
    before = state(desk)
    desk.reopen("T1")
    after = state(desk)
    assert after[0]["T2"] == before[0]["T2"]
    assert after[0]["T3"] == before[0]["T3"]
    assert desk.get_priority("T1") == 2
    assert desk.get_tickets() == ["T1", "T2", "T3"]


def test_a_reopened_ticket_cannot_be_assigned_to_its_own_agent(desk):
    desk.resolve("T1")
    desk.reopen("T1")
    with pytest.raises(DeskError):
        desk.assign("T1", "kim")


def test_resolved_then_reopened_tickets_count_as_assigned_everywhere(desk):
    desk.resolve("T3")
    desk.reopen("T3")
    with pytest.raises(DeskError):
        desk.reopen("T3")
    desk.resolve("T3")
    assert desk.get_status("T3") == "resolved"
