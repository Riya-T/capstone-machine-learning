"""Hidden tests for the initial ticket_desk spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

What happens to a resolved ticket (other than leaving its agent's queue) is
unspecified, so no test here looks a resolved ticket up again.

Usage (with desk.py importable, e.g. in the sandbox):
    python -m pytest private/test_desk_initial.py
"""

import pytest
from desk import DeskError, TicketDesk

BAD_PRIORITIES = [0, -4, 1.5, "3", None]
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
    return d


def state(d, tickets=TICKETS):
    """Every queue and the given tickets' priorities (copied), to check that a
    failed call changed nothing."""
    queues = {a: list(d.get_queue(a)) for a in AGENTS}
    priorities = {t: d.get_priority(t) for t in tickets}
    return queues, priorities


# --- agents -----------------------------------------------------------------


def test_an_empty_agent_id_is_rejected():
    d = TicketDesk()
    with pytest.raises(ValueError):
        d.add_agent("")
    d.add_agent("kim")
    assert d.get_queue("kim") == []


def test_adding_an_agent_twice_is_rejected(desk):
    desk.assign("T1", "kim")
    with pytest.raises(DeskError):
        desk.add_agent("kim")
    assert desk.get_queue("kim") == ["T1"]


@pytest.mark.parametrize(
    "call",
    [
        lambda d: d.assign("T2", "max"),
        lambda d: d.reassign("T1", "max"),
        lambda d: d.get_queue("max"),
        lambda d: d.assign("T2", 1),
        lambda d: d.reassign("T1", 1),
        lambda d: d.get_queue(1),
    ],
)
def test_agents_that_do_not_exist_raise_key_error(desk, call):
    desk.assign("T1", "kim")
    before = state(desk)
    with pytest.raises(KeyError):
        call(desk)
    assert state(desk) == before


def test_a_new_agent_has_an_empty_queue(desk):
    assert desk.get_queue("kim") == []
    assert desk.get_queue("lee") == []
    desk.add_agent("max")
    assert desk.get_queue("max") == []


# --- opening tickets --------------------------------------------------------


def test_a_new_ticket_has_its_priority_and_no_agent(desk):
    assert desk.get_priority("T1") == 2
    assert desk.get_priority("T2") == 5
    assert desk.get_priority("T3") == 1
    assert desk.get_queue("kim") == []
    desk.assign("T2", "kim")  # it has no agent, so assign takes it
    assert desk.get_queue("kim") == ["T2"]


def test_an_empty_ticket_id_is_rejected(desk):
    before = state(desk)
    with pytest.raises(ValueError):
        desk.open_ticket("", 1)
    assert state(desk) == before


@pytest.mark.parametrize("priority", BAD_PRIORITIES)
def test_invalid_priorities_are_rejected(desk, priority):
    before = state(desk)
    with pytest.raises(ValueError):
        desk.open_ticket("T4", priority)
    assert state(desk) == before
    with pytest.raises(KeyError):
        desk.get_priority("T4")


def test_opening_a_ticket_twice_is_rejected(desk):
    desk.assign("T1", "kim")
    before = state(desk)
    with pytest.raises(DeskError):
        desk.open_ticket("T1", 9)
    with pytest.raises(DeskError):
        desk.open_ticket("T2", 9)
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
        lambda d: d.reassign("T9", "lee"),
        lambda d: d.resolve("T9"),
        lambda d: d.get_priority("T9"),
        lambda d: d.get_priority(None),
        lambda d: d.assign(1, "kim"),
        lambda d: d.reassign(None, "lee"),
        lambda d: d.resolve(None),
    ],
)
def test_tickets_that_do_not_exist_raise_key_error(desk, call):
    desk.assign("T1", "kim")
    before = state(desk)
    with pytest.raises(KeyError):
        call(desk)
    assert state(desk) == before


# --- assigning --------------------------------------------------------------


def test_a_queue_keeps_the_order_the_agent_got_the_tickets(desk):
    desk.assign("T3", "kim")
    desk.assign("T1", "kim")
    desk.assign("T2", "lee")
    assert desk.get_queue("kim") == ["T3", "T1"]
    assert desk.get_queue("lee") == ["T2"]


def test_assigning_a_ticket_that_has_an_agent_is_rejected(desk):
    desk.assign("T1", "kim")
    before = state(desk)
    with pytest.raises(DeskError):
        desk.assign("T1", "lee")
    with pytest.raises(DeskError):
        desk.assign("T1", "kim")
    assert state(desk) == before


def test_a_reassigned_ticket_cannot_be_assigned(desk):
    desk.assign("T1", "kim")
    desk.reassign("T1", "lee")
    before = state(desk)
    with pytest.raises(DeskError):
        desk.assign("T1", "kim")
    assert state(desk) == before
    assert desk.get_queue("lee") == ["T1"]


# --- reassigning ------------------------------------------------------------


def test_reassigning_moves_the_ticket_to_the_end_of_the_new_queue(desk):
    desk.assign("T1", "kim")
    desk.assign("T2", "kim")
    desk.assign("T3", "lee")
    desk.reassign("T1", "lee")
    assert desk.get_queue("kim") == ["T2"]
    assert desk.get_queue("lee") == ["T3", "T1"]


def test_a_ticket_can_be_reassigned_back(desk):
    desk.assign("T1", "kim")
    desk.assign("T2", "kim")
    desk.reassign("T1", "lee")
    desk.reassign("T1", "kim")
    assert desk.get_queue("kim") == ["T2", "T1"]
    assert desk.get_queue("lee") == []


def test_reassigning_to_the_agent_who_has_it_is_rejected(desk):
    desk.assign("T1", "kim")
    desk.assign("T2", "kim")
    before = state(desk)
    with pytest.raises(DeskError):
        desk.reassign("T1", "kim")
    assert state(desk) == before
    assert desk.get_queue("kim") == ["T1", "T2"]


def test_a_ticket_with_no_agent_cannot_be_reassigned(desk):
    before = state(desk)
    with pytest.raises(DeskError):
        desk.reassign("T2", "lee")
    assert state(desk) == before
    desk.assign("T2", "lee")
    assert desk.get_queue("lee") == ["T2"]


def test_a_failed_reassign_leaves_the_ticket_where_it_was(desk):
    desk.assign("T1", "kim")
    desk.assign("T2", "kim")
    with pytest.raises(KeyError):
        desk.reassign("T1", "max")
    assert desk.get_queue("kim") == ["T1", "T2"]
    desk.reassign("T1", "lee")
    assert desk.get_queue("lee") == ["T1"]
    assert desk.get_queue("kim") == ["T2"]


# --- resolving --------------------------------------------------------------


def test_resolving_takes_the_ticket_out_of_the_queue(desk):
    desk.assign("T1", "kim")
    desk.assign("T2", "kim")
    desk.resolve("T1")
    assert desk.get_queue("kim") == ["T2"]
    assert desk.get_queue("lee") == []
    assert desk.get_priority("T2") == 5


def test_resolving_a_reassigned_ticket_takes_it_from_the_new_queue(desk):
    desk.assign("T1", "kim")
    desk.reassign("T1", "lee")
    desk.resolve("T1")
    assert desk.get_queue("kim") == []
    assert desk.get_queue("lee") == []


def test_resolving_leaves_the_other_tickets_alone(desk):
    desk.assign("T1", "kim")
    desk.assign("T2", "lee")
    desk.assign("T3", "kim")
    desk.resolve("T3")
    assert desk.get_queue("kim") == ["T1"]
    assert desk.get_queue("lee") == ["T2"]
    desk.reassign("T1", "lee")
    desk.resolve("T2")
    assert desk.get_queue("lee") == ["T1"]
    assert desk.get_priority("T1") == 2


def test_an_agent_takes_new_tickets_after_resolving(desk):
    desk.assign("T1", "kim")
    desk.resolve("T1")
    desk.assign("T3", "kim")
    desk.open_ticket("T4", 3)
    desk.assign("T4", "kim")
    assert desk.get_queue("kim") == ["T3", "T4"]


def test_a_ticket_with_no_agent_cannot_be_resolved(desk):
    before = state(desk)
    with pytest.raises(DeskError):
        desk.resolve("T2")
    assert state(desk) == before
    desk.assign("T2", "lee")
    desk.resolve("T2")
    assert desk.get_queue("lee") == []


# --- everything together ----------------------------------------------------


def test_failed_calls_leave_queues_unchanged(desk):
    desk.assign("T1", "kim")
    for call in (
        lambda: desk.assign("T1", "lee"),
        lambda: desk.reassign("T1", "kim"),
        lambda: desk.reassign("T2", "lee"),
        lambda: desk.assign("T9", "lee"),
        lambda: desk.assign("T2", "max"),
        lambda: desk.resolve("T2"),
        lambda: desk.open_ticket("T2", 3),
        lambda: desk.add_agent("kim"),
    ):
        with pytest.raises((DeskError, KeyError)):
            call()
    assert desk.get_queue("kim") == ["T1"]
    assert desk.get_queue("lee") == []
    assert {t: desk.get_priority(t) for t in TICKETS} == {"T1": 2, "T2": 5, "T3": 1}


def test_the_example_from_the_spec(desk):
    desk.assign("T3", "kim")
    desk.assign("T1", "kim")
    assert desk.get_queue("kim") == ["T3", "T1"]
    with pytest.raises(DeskError):
        desk.assign("T1", "lee")
    with pytest.raises(DeskError):
        desk.reassign("T2", "lee")
    with pytest.raises(DeskError):
        desk.resolve("T2")
    desk.reassign("T3", "lee")
    assert desk.get_queue("kim") == ["T1"]
    assert desk.get_queue("lee") == ["T3"]
    with pytest.raises(DeskError):
        desk.reassign("T3", "lee")
    desk.assign("T2", "kim")
    desk.reassign("T3", "kim")
    assert desk.get_queue("kim") == ["T1", "T2", "T3"]
    assert desk.get_queue("lee") == []
    desk.resolve("T1")
    assert desk.get_queue("kim") == ["T2", "T3"]
    assert desk.get_priority("T2") == 5
    with pytest.raises(KeyError):
        desk.get_queue("max")


def test_desks_do_not_share_agents_or_tickets():
    first, second = TicketDesk(), TicketDesk()
    first.add_agent("kim")
    first.open_ticket("T1", 1)
    with pytest.raises(KeyError):
        second.get_queue("kim")
    with pytest.raises(KeyError):
        second.get_priority("T1")
    second.add_agent("kim")
    second.open_ticket("T1", 4)
    assert second.get_priority("T1") == 4
    second.assign("T1", "kim")
    assert first.get_queue("kim") == []
