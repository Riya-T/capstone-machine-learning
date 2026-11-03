"""Hidden tests for the c_reopen change (reopening resolved tickets). Never
shown to the writer or the editor.

The initial spec leaves resolved tickets unspecified; this change pins them
down (they stay on the desk, out of every queue), so those rules are tested
here.

Usage (with desk.py importable, e.g. in the sandbox):
    python -m pytest changes/c_reopen/private/test_reopen_new.py
"""

import pytest
from desk import DeskError, TicketDesk

AGENTS = ["kim", "lee"]
TICKETS = ["T1", "T2", "T3"]


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
    return d  # kim's queue: T1, T3; lee's: T2


def state(d):
    tickets = {t: (d.get_priority(t), d.get_reopen_count(t)) for t in TICKETS}
    queues = {a: list(d.get_queue(a)) for a in AGENTS}
    return tickets, queues


# --- resolved tickets stay on the desk --------------------------------------


def test_a_resolved_ticket_keeps_its_priority_and_id(desk):
    desk.resolve("T1")
    assert desk.get_priority("T1") == 2
    assert desk.get_reopen_count("T1") == 0
    with pytest.raises(DeskError):
        desk.open_ticket("T1", 9)
    assert desk.get_priority("T1") == 2
    assert desk.get_queue("kim") == ["T3"]


def test_a_resolved_ticket_cannot_be_assigned_reassigned_or_resolved(desk):
    desk.resolve("T1")
    before = state(desk)
    for call in (
        lambda: desk.assign("T1", "kim"),
        lambda: desk.assign("T1", "lee"),
        lambda: desk.reassign("T1", "lee"),
        lambda: desk.reassign("T1", "kim"),
        lambda: desk.resolve("T1"),
    ):
        with pytest.raises(DeskError):
            call()
    assert state(desk) == before


# --- reopening --------------------------------------------------------------


def test_new_tickets_have_a_reopen_count_of_zero(desk):
    desk.open_ticket("T4", 1)
    assert desk.get_reopen_count("T4") == 0
    assert desk.get_reopen_count("T1") == 0


def test_a_reopened_ticket_goes_to_the_end_of_its_agents_queue(desk):
    desk.resolve("T1")
    assert desk.get_queue("kim") == ["T3"]
    desk.reopen("T1")
    assert desk.get_queue("kim") == ["T3", "T1"]
    assert desk.get_queue("lee") == ["T2"]
    assert desk.get_reopen_count("T1") == 1


def test_the_ticket_returns_to_the_agent_who_resolved_it(desk):
    desk.reassign("T1", "lee")
    desk.resolve("T1")
    desk.reopen("T1")
    assert desk.get_queue("lee") == ["T2", "T1"]
    assert desk.get_queue("kim") == ["T3"]


def test_reopen_count_grows_with_each_reopen(desk):
    for _ in range(3):
        desk.resolve("T1")
        desk.reopen("T1")
    assert desk.get_reopen_count("T1") == 3
    assert desk.get_reopen_count("T3") == 0
    assert desk.get_queue("kim") == ["T3", "T1"]


def test_a_reopened_ticket_can_be_reassigned_and_resolved_again(desk):
    desk.resolve("T1")
    desk.reopen("T1")
    desk.reassign("T1", "lee")
    assert desk.get_queue("lee") == ["T2", "T1"]
    assert desk.get_queue("kim") == ["T3"]
    desk.resolve("T1")
    assert desk.get_queue("lee") == ["T2"]
    desk.reopen("T1")
    assert desk.get_queue("lee") == ["T2", "T1"]
    assert desk.get_reopen_count("T1") == 2


def test_a_reopened_ticket_still_has_its_agent(desk):
    desk.resolve("T1")
    desk.reopen("T1")
    before = state(desk)
    with pytest.raises(DeskError):
        desk.assign("T1", "lee")
    with pytest.raises(DeskError):
        desk.reassign("T1", "kim")
    assert state(desk) == before


def test_reopening_an_unresolved_ticket_changes_nothing(desk):
    desk.open_ticket("T4", 1)
    before = state(desk)
    with pytest.raises(DeskError):
        desk.reopen("T4")  # no agent yet
    with pytest.raises(DeskError):
        desk.reopen("T1")  # kim is working on it
    assert state(desk) == before
    assert desk.get_reopen_count("T4") == 0
    desk.assign("T4", "lee")
    assert desk.get_queue("lee") == ["T2", "T4"]


def test_a_reopened_ticket_cannot_be_reopened_until_resolved_again(desk):
    desk.resolve("T3")
    desk.reopen("T3")
    with pytest.raises(DeskError):
        desk.reopen("T3")
    assert desk.get_reopen_count("T3") == 1
    assert desk.get_queue("kim") == ["T1", "T3"]
    desk.resolve("T3")
    assert desk.get_queue("kim") == ["T1"]


def test_reopen_methods_reject_unknown_tickets(desk):
    before = state(desk)
    with pytest.raises(KeyError):
        desk.reopen("T9")
    with pytest.raises(KeyError):
        desk.get_reopen_count("T9")
    with pytest.raises(KeyError):
        desk.reopen(None)
    with pytest.raises(KeyError):
        desk.reopen(1)
    assert state(desk) == before


def test_reopening_keeps_priority_and_other_tickets(desk):
    desk.resolve("T1")
    desk.resolve("T2")
    desk.reopen("T1")
    assert desk.get_priority("T1") == 2
    assert desk.get_priority("T2") == 5
    assert desk.get_reopen_count("T2") == 0
    assert desk.get_queue("lee") == []
    assert desk.get_queue("kim") == ["T3", "T1"]
    with pytest.raises(DeskError):
        desk.resolve("T2")
    with pytest.raises(DeskError):
        desk.assign("T2", "kim")
