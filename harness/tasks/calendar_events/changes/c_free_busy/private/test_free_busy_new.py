"""Hidden tests for the c_free_busy change (free/busy queries). Never shown
to the writer or the editor.

Usage (with agenda.py importable, e.g. in the sandbox):
    python -m pytest changes/c_free_busy/private/test_free_busy_new.py
"""

import pytest
from agenda import Agenda

BAD_WINDOWS = [(-1, 60), (60, 60), (90, 60), (1.5, 60), (0, "60"), (None, 60)]


@pytest.fixture
def agenda():
    ag = Agenda()
    ag.add_event("standup", 540, 555)
    ag.add_event("review", 600, 660)
    ag.add_event("lunch", 720, 780)
    ag.add_event("debrief", 660, 720)
    for event in ["standup", "review", "debrief"]:
        ag.add_attendee(event, "mira")
    ag.add_attendee("lunch", "theo")
    return ag


def state(ag):
    return {e: (ag.get_time(e), ag.get_attendees(e)) for e in ag.get_events()}


def test_busy_periods_come_earliest_first(agenda):
    assert agenda.get_busy("mira", 0, 1440) == [(540, 555), (600, 720)]


def test_touching_events_merge_into_one_busy_period(agenda):
    agenda.add_attendee("lunch", "mira")
    assert agenda.get_busy("mira", 480, 900) == [(540, 555), (600, 780)]
    assert agenda.get_free("mira", 480, 900) == [(480, 540), (555, 600), (780, 900)]


def test_busy_periods_are_clipped_to_the_window(agenda):
    assert agenda.get_busy("mira", 550, 650) == [(550, 555), (600, 650)]
    assert agenda.get_free("mira", 550, 650) == [(555, 600)]


def test_events_outside_the_window_are_ignored(agenda):
    assert agenda.get_busy("mira", 0, 540) == []
    assert agenda.get_busy("mira", 720, 1440) == []
    assert agenda.get_free("mira", 0, 540) == [(0, 540)]
    assert agenda.is_free("mira", 720, 1440)


def test_free_is_the_whole_window_when_nothing_is_booked(agenda):
    assert agenda.get_free("theo", 0, 700) == [(0, 700)]
    assert agenda.get_busy("theo", 0, 700) == []
    assert agenda.is_free("theo", 0, 700)


def test_free_is_empty_when_the_window_is_fully_booked(agenda):
    assert agenda.get_free("mira", 600, 720) == []
    assert agenda.get_free("mira", 610, 700) == []
    assert not agenda.is_free("mira", 610, 700)


def test_a_window_matching_an_event_exactly_is_all_busy(agenda):
    assert agenda.get_busy("mira", 540, 555) == [(540, 555)]
    assert agenda.get_free("mira", 540, 555) == []


def test_a_window_touching_an_event_is_free(agenda):
    assert agenda.is_free("mira", 555, 600)
    assert agenda.is_free("mira", 720, 721)
    assert agenda.get_busy("mira", 555, 600) == []


def test_is_free_is_false_for_any_overlap(agenda):
    assert not agenda.is_free("mira", 500, 541)
    assert not agenda.is_free("mira", 554, 700)
    assert not agenda.is_free("mira", 0, 1440)


def test_other_people_do_not_make_someone_busy(agenda):
    assert agenda.get_busy("theo", 480, 900) == [(720, 780)]
    assert agenda.get_busy("mira", 720, 780) == []
    assert agenda.get_busy("nobody", 0, 1440) == []
    assert agenda.get_free("", 0, 10) == [(0, 10)]


@pytest.mark.parametrize("start,end", BAD_WINDOWS)
@pytest.mark.parametrize("method", ["get_busy", "get_free", "is_free"])
def test_invalid_windows_are_rejected(agenda, method, start, end):
    with pytest.raises(ValueError):
        getattr(agenda, method)("mira", start, end)


def test_queries_change_nothing(agenda):
    before = state(agenda)
    agenda.get_busy("mira", 0, 1440)
    agenda.get_free("mira", 0, 1440)
    agenda.is_free("theo", 0, 1440)
    assert state(agenda) == before
    assert agenda.get_schedule("mira") == ["standup", "review", "debrief"]
