"""Public checks for the c_no_overlap change (no double-booking). Shown to
the editor, never to the writer.

Usage (with agenda.py importable, e.g. in the sandbox):
    python -m pytest changes/c_no_overlap/public/test_no_overlap_public.py
"""

import pytest
from agenda import Agenda, ScheduleConflict


def test_joining_an_overlapping_event_is_refused():
    ag = Agenda()
    ag.add_event("review", 600, 660)
    ag.add_event("call", 630, 690)
    ag.add_attendee("review", "mira")
    with pytest.raises(ScheduleConflict):
        ag.add_attendee("call", "mira")
    assert ag.get_attendees("call") == []
    assert ag.get_conflicts("call", "mira") == ["review"]


def test_events_that_touch_do_not_conflict():
    ag = Agenda()
    ag.add_event("review", 600, 660)
    ag.add_event("debrief", 660, 720)
    ag.add_attendee("review", "mira")
    ag.add_attendee("debrief", "mira")
    assert ag.get_schedule("mira") == ["review", "debrief"]
    assert ag.get_conflicts("debrief", "mira") == []
