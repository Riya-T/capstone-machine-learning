"""Public checks for agenda.py.

Usage (with agenda.py importable, e.g. in the sandbox):
    python -m pytest public/test_agenda_public.py
"""

import pytest
from agenda import Agenda


@pytest.fixture
def agenda():
    ag = Agenda()
    ag.add_event("standup", 540, 555)
    ag.add_event("review", 600, 660)
    return ag


def test_added_events_keep_their_time(agenda):
    assert agenda.get_time("standup") == (540, 555)
    assert agenda.get_events() == ["standup", "review"]


def test_attendees_are_listed_in_the_order_added(agenda):
    agenda.add_attendee("standup", "mira")
    agenda.add_attendee("standup", "theo")
    assert agenda.get_attendees("standup") == ["mira", "theo"]
    assert agenda.get_attendees("review") == []


def test_schedule_is_sorted_by_start_time(agenda):
    agenda.add_attendee("review", "mira")
    agenda.add_attendee("standup", "mira")
    assert agenda.get_schedule("mira") == ["standup", "review"]
    assert agenda.get_schedule("theo") == []


def test_end_must_come_after_start(agenda):
    with pytest.raises(ValueError):
        agenda.add_event("lunch", 780, 720)
    assert agenda.get_events() == ["standup", "review"]


def test_unknown_event_raises_key_error(agenda):
    with pytest.raises(KeyError):
        agenda.get_time("lunch")
    with pytest.raises(KeyError):
        agenda.add_attendee("lunch", "mira")
