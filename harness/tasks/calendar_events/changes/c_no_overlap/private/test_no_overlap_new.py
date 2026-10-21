"""Hidden tests for the c_no_overlap change (no double-booking). Never shown
to the writer or the editor.

Usage (with agenda.py importable, e.g. in the sandbox):
    python -m pytest changes/c_no_overlap/private/test_no_overlap_new.py
"""

import pytest
from agenda import Agenda, AgendaError, ScheduleConflict


@pytest.fixture
def agenda():
    ag = Agenda()
    ag.add_event("standup", 540, 555)
    ag.add_event("review", 600, 660)
    ag.add_event("lunch", 720, 780)
    ag.add_event("call", 630, 690)
    ag.add_attendee("review", "mira")
    ag.add_attendee("review", "theo")
    return ag


def state(ag):
    return {e: (ag.get_time(e), ag.get_attendees(e)) for e in ag.get_events()}


def test_a_partly_overlapping_event_is_refused(agenda):
    before = state(agenda)
    with pytest.raises(ScheduleConflict):
        agenda.add_attendee("call", "mira")
    assert state(agenda) == before
    assert agenda.get_schedule("mira") == ["review"]


def test_an_event_around_or_inside_another_is_refused(agenda):
    agenda.add_event("offsite", 500, 900)
    agenda.add_event("coffee", 610, 620)
    for event in ["offsite", "coffee"]:
        with pytest.raises(ScheduleConflict):
            agenda.add_attendee(event, "mira")
    assert agenda.get_attendees("offsite") == []
    assert agenda.get_attendees("coffee") == []


def test_events_that_only_touch_may_both_be_attended(agenda):
    agenda.add_event("debrief", 660, 720)
    agenda.add_event("warmup", 580, 600)
    agenda.add_attendee("debrief", "mira")
    agenda.add_attendee("warmup", "mira")
    agenda.add_attendee("lunch", "mira")
    assert agenda.get_schedule("mira") == ["warmup", "review", "debrief", "lunch"]


def test_other_people_are_not_affected_by_a_conflict(agenda):
    agenda.add_attendee("call", "anya")
    assert agenda.get_attendees("call") == ["anya"]
    with pytest.raises(ScheduleConflict):
        agenda.add_attendee("call", "theo")
    assert agenda.get_attendees("call") == ["anya"]


def test_after_a_refusal_the_person_can_still_join_elsewhere(agenda):
    with pytest.raises(ScheduleConflict):
        agenda.add_attendee("call", "mira")
    agenda.add_attendee("lunch", "mira")
    assert agenda.get_schedule("mira") == ["review", "lunch"]


def test_schedule_conflict_is_an_agenda_error():
    assert issubclass(ScheduleConflict, AgendaError)


def test_get_conflicts_lists_overlapping_events_earliest_first(agenda):
    agenda.add_attendee("standup", "mira")
    agenda.add_attendee("lunch", "mira")
    agenda.add_event("morning", 550, 700)
    assert agenda.get_conflicts("morning", "mira") == ["standup", "review"]
    assert agenda.get_conflicts("call", "mira") == ["review"]


def test_get_conflicts_ignores_the_event_itself_and_touching_events(agenda):
    agenda.add_event("debrief", 660, 720)
    agenda.add_attendee("debrief", "mira")
    assert agenda.get_conflicts("review", "mira") == []
    assert agenda.get_conflicts("debrief", "mira") == []
    assert agenda.get_conflicts("standup", "mira") == []


def test_get_conflicts_for_someone_with_no_events_is_empty(agenda):
    assert agenda.get_conflicts("call", "nobody") == []
    assert agenda.get_conflicts("call", "") == []


def test_get_conflicts_for_a_missing_event_raises_key_error(agenda):
    with pytest.raises(KeyError):
        agenda.get_conflicts("party", "mira")
    with pytest.raises(KeyError):
        agenda.get_conflicts(None, "mira")


def test_a_missing_event_is_reported_before_a_conflict(agenda):
    with pytest.raises(KeyError):
        agenda.add_attendee("party", "mira")


def test_already_attending_is_reported_as_a_plain_agenda_error(agenda):
    with pytest.raises(AgendaError) as caught:
        agenda.add_attendee("review", "mira")
    assert not isinstance(caught.value, ScheduleConflict)
    assert agenda.get_attendees("review") == ["mira", "theo"]
