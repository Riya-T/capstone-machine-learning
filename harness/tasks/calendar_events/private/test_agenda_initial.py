"""Hidden tests for the initial calendar_events spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with agenda.py importable, e.g. in the sandbox):
    python -m pytest private/test_agenda_initial.py
"""

import pytest
from agenda import Agenda, AgendaError

BAD_TIMES = [
    (-1, 60),
    (60, 60),
    (90, 60),
    (1.5, 60),
    (0, 2.5),
    ("0", 60),
    (0, "60"),
    (None, 60),
    (0, None),
]


@pytest.fixture
def agenda():
    ag = Agenda()
    ag.add_event("standup", 540, 555)
    ag.add_event("review", 600, 660)
    ag.add_event("lunch", 720, 780)
    return ag


def state(ag):
    """Every event's time and attendees, to check that a failed call changed nothing."""
    return {e: (ag.get_time(e), ag.get_attendees(e)) for e in ag.get_events()}


# --- events -----------------------------------------------------------------


def test_a_new_agenda_is_empty():
    assert Agenda().get_events() == []


def test_events_are_listed_in_the_order_added():
    ag = Agenda()
    ag.add_event("late", 900, 960)
    ag.add_event("early", 60, 120)
    ag.add_event("middle", 480, 540)
    assert ag.get_events() == ["late", "early", "middle"]


def test_get_time_returns_start_and_end(agenda):
    assert agenda.get_time("review") == (600, 660)
    assert agenda.get_time("lunch") == (720, 780)


def test_an_event_may_start_at_minute_zero():
    ag = Agenda()
    ag.add_event("midnight", 0, 1)
    assert ag.get_time("midnight") == (0, 1)


def test_a_new_event_has_no_attendees(agenda):
    assert agenda.get_attendees("standup") == []


@pytest.mark.parametrize("bad_id", [""])
def test_invalid_event_ids_are_rejected(bad_id):
    ag = Agenda()
    with pytest.raises(ValueError):
        ag.add_event(bad_id, 0, 60)
    assert ag.get_events() == []


@pytest.mark.parametrize("start,end", BAD_TIMES)
def test_invalid_times_are_rejected(agenda, start, end):
    before = state(agenda)
    with pytest.raises(ValueError):
        agenda.add_event("extra", start, end)
    assert state(agenda) == before


def test_adding_an_existing_event_is_rejected(agenda):
    agenda.add_attendee("standup", "mira")
    before = state(agenda)
    with pytest.raises(AgendaError):
        agenda.add_event("standup", 0, 60)
    assert state(agenda) == before


def test_bad_times_are_reported_before_a_duplicate_id(agenda):
    with pytest.raises(ValueError):
        agenda.add_event("standup", 60, 30)


@pytest.mark.parametrize(
    "call",
    [
        lambda ag: ag.get_time("party"),
        lambda ag: ag.get_attendees("party"),
        lambda ag: ag.add_attendee("party", "mira"),
        lambda ag: ag.get_time(None),
        lambda ag: ag.get_attendees(1),
        lambda ag: ag.add_attendee(None, "mira"),
    ],
)
def test_events_that_do_not_exist_raise_key_error(agenda, call):
    agenda.add_attendee("standup", "mira")
    before = state(agenda)
    with pytest.raises(KeyError):
        call(agenda)
    assert state(agenda) == before


# --- attendees --------------------------------------------------------------


def test_attendees_are_listed_in_the_order_added(agenda):
    for name in ["theo", "mira", "anya"]:
        agenda.add_attendee("review", name)
    assert agenda.get_attendees("review") == ["theo", "mira", "anya"]
    assert agenda.get_attendees("standup") == []


def test_the_same_person_can_attend_several_events(agenda):
    agenda.add_attendee("standup", "mira")
    agenda.add_attendee("review", "mira")
    assert agenda.get_attendees("standup") == ["mira"]
    assert agenda.get_attendees("review") == ["mira"]


def test_different_people_may_attend_events_at_the_same_time(agenda):
    agenda.add_event("call", 600, 630)
    agenda.add_attendee("review", "mira")
    agenda.add_attendee("call", "theo")
    assert agenda.get_schedule("mira") == ["review"]
    assert agenda.get_schedule("theo") == ["call"]


def test_an_empty_name_is_rejected(agenda):
    before = state(agenda)
    with pytest.raises(ValueError):
        agenda.add_attendee("standup", "")
    assert state(agenda) == before


def test_adding_an_attendee_twice_is_rejected(agenda):
    agenda.add_attendee("standup", "mira")
    before = state(agenda)
    with pytest.raises(AgendaError):
        agenda.add_attendee("standup", "mira")
    assert state(agenda) == before
    assert agenda.get_schedule("mira") == ["standup"]


def test_a_missing_event_is_reported_before_an_empty_name(agenda):
    with pytest.raises(KeyError):
        agenda.add_attendee("party", "")


# --- schedules --------------------------------------------------------------


def test_schedule_lists_only_the_events_the_person_attends(agenda):
    agenda.add_attendee("standup", "mira")
    agenda.add_attendee("lunch", "mira")
    agenda.add_attendee("review", "theo")
    assert agenda.get_schedule("mira") == ["standup", "lunch"]
    assert agenda.get_schedule("theo") == ["review"]


def test_schedule_is_sorted_earliest_start_first(agenda):
    agenda.add_event("coffee", 480, 500)
    for event in ["lunch", "coffee", "review", "standup"]:
        agenda.add_attendee(event, "mira")
    assert agenda.get_schedule("mira") == ["coffee", "standup", "review", "lunch"]


def test_schedule_order_does_not_depend_on_when_the_person_joined(agenda):
    agenda.add_attendee("lunch", "mira")
    agenda.add_attendee("standup", "mira")
    agenda.add_attendee("review", "mira")
    assert agenda.get_schedule("mira") == ["standup", "review", "lunch"]
    agenda.add_event("early", 60, 120)
    agenda.add_attendee("early", "mira")
    assert agenda.get_schedule("mira") == ["early", "standup", "review", "lunch"]


def test_events_that_touch_are_both_in_the_schedule(agenda):
    agenda.add_event("debrief", 555, 600)
    agenda.add_attendee("debrief", "mira")
    agenda.add_attendee("standup", "mira")
    agenda.add_attendee("review", "mira")
    assert agenda.get_schedule("mira") == ["standup", "debrief", "review"]


def test_schedule_of_an_unknown_name_is_empty(agenda):
    assert agenda.get_schedule("nobody") == []
    assert agenda.get_schedule("") == []


def test_failed_calls_change_no_schedule(agenda):
    agenda.add_attendee("standup", "mira")
    for call in (
        lambda: agenda.add_attendee("standup", "mira"),
        lambda: agenda.add_attendee("party", "mira"),
        lambda: agenda.add_attendee("review", ""),
    ):
        with pytest.raises((KeyError, ValueError, AgendaError)):
            call()
    assert agenda.get_schedule("mira") == ["standup"]


def test_agendas_do_not_share_events():
    first, second = Agenda(), Agenda()
    first.add_event("standup", 540, 555)
    first.add_attendee("standup", "mira")
    assert second.get_events() == []
    assert second.get_schedule("mira") == []
    second.add_event("standup", 0, 10)
    assert second.get_time("standup") == (0, 10)
    assert second.get_attendees("standup") == []
