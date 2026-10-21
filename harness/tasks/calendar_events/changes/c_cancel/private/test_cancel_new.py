"""Hidden tests for the c_cancel change (cancelling events and removing
attendees). Never shown to the writer or the editor.

Usage (with agenda.py importable, e.g. in the sandbox):
    python -m pytest changes/c_cancel/private/test_cancel_new.py
"""

import pytest
from agenda import Agenda, AgendaError


@pytest.fixture
def agenda():
    ag = Agenda()
    ag.add_event("standup", 540, 555)
    ag.add_event("review", 600, 660)
    ag.add_event("lunch", 720, 780)
    ag.add_attendee("standup", "mira")
    ag.add_attendee("review", "mira")
    ag.add_attendee("review", "theo")
    return ag


def state(ag):
    return {e: (ag.get_time(e), ag.get_attendees(e)) for e in ag.get_events()}


@pytest.mark.parametrize(
    "call",
    [
        lambda ag: ag.get_time("review"),
        lambda ag: ag.get_attendees("review"),
        lambda ag: ag.add_attendee("review", "anya"),
        lambda ag: ag.cancel_event("review"),
        lambda ag: ag.remove_attendee("review", "mira"),
    ],
)
def test_a_cancelled_event_no_longer_exists(agenda, call):
    agenda.cancel_event("review")
    assert agenda.get_events() == ["standup", "lunch"]
    with pytest.raises(KeyError):
        call(agenda)


def test_cancelling_clears_the_event_from_every_schedule(agenda):
    agenda.cancel_event("review")
    assert agenda.get_schedule("mira") == ["standup"]
    assert agenda.get_schedule("theo") == []


def test_cancelling_leaves_other_events_untouched(agenda):
    agenda.cancel_event("standup")
    assert agenda.get_time("review") == (600, 660)
    assert agenda.get_attendees("review") == ["mira", "theo"]
    assert agenda.get_attendees("lunch") == []


def test_cancelling_a_missing_event_raises_key_error(agenda):
    before = state(agenda)
    for bad in ["party", None, 1]:
        with pytest.raises(KeyError):
            agenda.cancel_event(bad)
    assert state(agenda) == before
    assert agenda.get_cancelled() == []


def test_cancelled_ids_are_listed_in_the_order_cancelled(agenda):
    assert agenda.get_cancelled() == []
    agenda.cancel_event("lunch")
    agenda.cancel_event("standup")
    assert agenda.get_cancelled() == ["lunch", "standup"]
    assert agenda.get_events() == ["review"]


def test_a_cancelled_id_can_be_used_for_a_fresh_event(agenda):
    agenda.cancel_event("review")
    agenda.add_event("review", 900, 960)
    assert agenda.get_time("review") == (900, 960)
    assert agenda.get_attendees("review") == []
    assert agenda.get_events() == ["standup", "lunch", "review"]
    assert agenda.get_cancelled() == ["review"]
    assert agenda.get_schedule("theo") == []


def test_cancelling_frees_the_time_for_its_attendees(agenda):
    agenda.add_event("call", 630, 690)
    with pytest.raises(AgendaError):
        agenda.add_attendee("call", "mira")
    agenda.cancel_event("review")
    agenda.add_attendee("call", "mira")
    assert agenda.get_schedule("mira") == ["standup", "call"]


def test_removing_an_attendee_keeps_the_others_in_order(agenda):
    agenda.add_attendee("review", "anya")
    agenda.remove_attendee("review", "theo")
    assert agenda.get_attendees("review") == ["mira", "anya"]
    assert agenda.get_schedule("theo") == []
    assert agenda.get_schedule("mira") == ["standup", "review"]


def test_a_removed_attendee_can_join_again_or_elsewhere(agenda):
    agenda.add_event("call", 630, 690)
    agenda.remove_attendee("review", "mira")
    agenda.add_attendee("call", "mira")
    assert agenda.get_schedule("mira") == ["standup", "call"]
    agenda.remove_attendee("call", "mira")
    agenda.add_attendee("review", "mira")
    assert agenda.get_attendees("review") == ["theo", "mira"]


@pytest.mark.parametrize("name", ["anya", ""])
def test_removing_someone_who_does_not_attend_is_rejected(agenda, name):
    before = state(agenda)
    with pytest.raises(AgendaError):
        agenda.remove_attendee("review", name)
    assert state(agenda) == before


def test_removing_from_a_missing_event_raises_key_error(agenda):
    before = state(agenda)
    with pytest.raises(KeyError):
        agenda.remove_attendee("party", "mira")
    with pytest.raises(KeyError):
        agenda.remove_attendee("party", "anya")
    assert state(agenda) == before


def test_cancelling_and_removing_do_not_touch_other_attendees(agenda):
    agenda.remove_attendee("review", "mira")
    agenda.cancel_event("standup")
    assert agenda.get_attendees("review") == ["theo"]
    assert agenda.get_schedule("theo") == ["review"]
    assert agenda.get_schedule("mira") == []
