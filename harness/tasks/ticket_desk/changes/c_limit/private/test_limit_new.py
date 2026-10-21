"""Hidden tests for the c_limit change (per-agent queue limits). Never shown
to the writer or the editor.

Usage (with desk.py importable, e.g. in the sandbox):
    python -m pytest changes/c_limit/private/test_limit_new.py
"""

import pytest
from desk import AgentFull, DeskError, TicketDesk

BAD_LIMITS = [-1, 1.5, "2", True, "none"]
AGENTS = ["kim", "lee"]


@pytest.fixture
def desk():
    d = TicketDesk()
    d.add_agent("kim", limit=2)
    d.add_agent("lee")
    for n in range(1, 6):
        d.open_ticket(f"T{n}", n)
    return d


def state(d):
    tickets = {t: d.get_status(t) for t in d.get_tickets()}
    queues = {a: (d.get_tickets(a), d.get_limit(a)) for a in AGENTS}
    return tickets, queues


def test_the_limit_is_reported(desk):
    assert desk.get_limit("kim") == 2
    assert desk.get_limit("lee") is None


def test_the_queue_can_be_filled_exactly_to_the_limit(desk):
    desk.assign("T1", "kim")
    desk.assign("T2", "kim")
    assert desk.get_tickets("kim") == ["T1", "T2"]
    before = state(desk)
    with pytest.raises(AgentFull):
        desk.assign("T3", "kim")
    assert state(desk) == before


def test_resolving_frees_room(desk):
    desk.assign("T1", "kim")
    desk.assign("T2", "kim")
    desk.resolve("T1")
    desk.assign("T3", "kim")
    assert desk.get_tickets("kim") == ["T2", "T3"]


def test_reassigning_away_frees_room_and_counts_for_the_receiver(desk):
    desk.set_limit("lee", 1)
    desk.assign("T1", "kim")
    desk.assign("T2", "kim")
    desk.assign("T1", "lee")
    desk.assign("T3", "kim")
    assert desk.get_tickets("kim") == ["T2", "T3"]
    assert desk.get_tickets("lee") == ["T1"]
    with pytest.raises(AgentFull):
        desk.assign("T2", "lee")
    assert desk.get_tickets("kim") == ["T2", "T3"]


def test_a_limit_of_zero_takes_nothing(desk):
    desk.add_agent("max", limit=0)
    with pytest.raises(AgentFull):
        desk.assign("T1", "max")
    assert desk.get_status("T1") == "open"


@pytest.mark.parametrize("limit", BAD_LIMITS)
def test_invalid_limits_are_rejected_when_adding(desk, limit):
    with pytest.raises(ValueError):
        desk.add_agent("max", limit=limit)
    with pytest.raises(KeyError):
        desk.get_limit("max")


@pytest.mark.parametrize("limit", BAD_LIMITS)
def test_invalid_limits_are_rejected_when_setting(desk, limit):
    before = state(desk)
    with pytest.raises(ValueError):
        desk.set_limit("kim", limit)
    assert state(desk) == before


def test_a_duplicate_agent_is_reported_after_a_bad_limit(desk):
    with pytest.raises(ValueError):
        desk.add_agent("kim", limit=-1)
    with pytest.raises(DeskError):
        desk.add_agent("kim", limit=5)
    assert desk.get_limit("kim") == 2


def test_limit_methods_reject_unknown_agents(desk):
    with pytest.raises(KeyError):
        desk.get_limit("max")
    with pytest.raises(KeyError):
        desk.set_limit("max", 3)
    with pytest.raises(KeyError):
        desk.set_limit("max", -1)


def test_set_limit_replaces_the_limit(desk):
    desk.set_limit("kim", 3)
    assert desk.get_limit("kim") == 3
    for t in ["T1", "T2", "T3"]:
        desk.assign(t, "kim")
    with pytest.raises(AgentFull):
        desk.assign("T4", "kim")
    desk.set_limit("kim", None)
    assert desk.get_limit("kim") is None
    desk.assign("T4", "kim")
    assert desk.get_tickets("kim") == ["T1", "T2", "T3", "T4"]


def test_a_limit_below_the_queue_size_is_rejected(desk):
    desk.assign("T1", "kim")
    desk.assign("T2", "kim")
    before = state(desk)
    with pytest.raises(DeskError):
        desk.set_limit("kim", 1)
    assert state(desk) == before
    desk.set_limit("kim", 2)  # exactly the queue size is fine
    assert desk.get_limit("kim") == 2


def test_a_bad_limit_is_reported_before_the_queue_size_check(desk):
    desk.assign("T1", "kim")
    desk.assign("T2", "kim")
    with pytest.raises(ValueError):
        desk.set_limit("kim", -1)


def test_agent_full_is_checked_after_the_other_assign_errors(desk):
    desk.assign("T1", "kim")
    desk.assign("T2", "kim")
    with pytest.raises(DeskError) as err:
        desk.assign("T1", "kim")  # already has it
    assert not isinstance(err.value, AgentFull)
    desk.assign("T3", "lee")
    desk.resolve("T3")
    with pytest.raises(DeskError) as err:
        desk.assign("T3", "kim")  # resolved
    assert not isinstance(err.value, AgentFull)
    with pytest.raises(KeyError):
        desk.assign("T9", "kim")


def test_agent_full_is_a_desk_error():
    assert issubclass(AgentFull, DeskError)
