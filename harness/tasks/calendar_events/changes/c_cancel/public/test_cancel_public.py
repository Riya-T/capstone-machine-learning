"""Public checks for the c_cancel change (cancelling events and removing
attendees). Shown to the editor, never to the writer.

Usage (with agenda.py importable, e.g. in the sandbox):
    python -m pytest changes/c_cancel/public/test_cancel_public.py
"""

import pytest
from agenda import Agenda


def test_a_cancelled_event_disappears():
    ag = Agenda()
    ag.add_event("standup", 540, 555)
    ag.add_event("review", 600, 660)
    ag.add_attendee("review", "mira")
    ag.cancel_event("review")
    assert ag.get_events() == ["standup"]
    assert ag.get_cancelled() == ["review"]
    assert ag.get_schedule("mira") == []
    with pytest.raises(KeyError):
        ag.get_time("review")


def test_a_removed_attendee_leaves_the_event():
    ag = Agenda()
    ag.add_event("review", 600, 660)
    ag.add_attendee("review", "mira")
    ag.add_attendee("review", "theo")
    ag.remove_attendee("review", "mira")
    assert ag.get_attendees("review") == ["theo"]
    assert ag.get_schedule("mira") == []
