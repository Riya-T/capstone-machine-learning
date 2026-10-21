"""Public checks for the c_free_busy change (free/busy queries). Shown to
the editor, never to the writer.

Usage (with agenda.py importable, e.g. in the sandbox):
    python -m pytest changes/c_free_busy/public/test_free_busy_public.py
"""

from agenda import Agenda


def test_busy_and_free_periods_inside_a_window():
    ag = Agenda()
    ag.add_event("standup", 540, 555)
    ag.add_event("review", 600, 660)
    ag.add_attendee("standup", "mira")
    ag.add_attendee("review", "mira")
    assert ag.get_busy("mira", 480, 720) == [(540, 555), (600, 660)]
    assert ag.get_free("mira", 480, 720) == [(480, 540), (555, 600), (660, 720)]
    assert ag.is_free("mira", 555, 600)
    assert not ag.is_free("mira", 550, 560)


def test_busy_periods_are_cut_to_the_window():
    ag = Agenda()
    ag.add_event("review", 600, 660)
    ag.add_attendee("review", "mira")
    assert ag.get_busy("mira", 630, 640) == [(630, 640)]
    assert ag.get_free("mira", 630, 640) == []
    assert ag.get_free("theo", 630, 640) == [(630, 640)]
