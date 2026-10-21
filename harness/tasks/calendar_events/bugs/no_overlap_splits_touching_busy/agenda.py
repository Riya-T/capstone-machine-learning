"""Agenda with free/busy queries where nobody can be double-booked.

Planted bug (after c_free_busy and c_no_overlap): the conflict check was
added correctly, but busy periods are now merged only when they strictly
overlap, so periods that touch are reported separately.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from agenda import Agenda
    agenda = Agenda()
    agenda.add_event("standup", 540, 555)
    agenda.add_attendee("standup", "mira")
    agenda.get_free("mira", 480, 720)
"""


class AgendaError(Exception):
    pass


class ScheduleConflict(AgendaError):
    pass


def check_times(start, end):
    for value in (start, end):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"times must be int, got {value!r}")
    if start < 0 or end <= start:
        raise ValueError(f"need 0 <= start < end, got {start} and {end}")


def overlaps(first, second):
    """Two (start, end) periods overlap when each starts before the other ends."""
    return first[0] < second[1] and second[0] < first[1]


class Agenda:
    def __init__(self):
        self._times = {}  # event id -> (start, end), in the order added
        self._attendees = {}  # event id -> list of names, in the order added

    def add_event(self, event_id, start, end):
        if not isinstance(event_id, str) or not event_id:
            raise ValueError("event_id must be a non-empty str")
        check_times(start, end)
        if event_id in self._times:
            raise AgendaError(f"event {event_id!r} already exists")
        self._times[event_id] = (start, end)
        self._attendees[event_id] = []

    def add_attendee(self, event_id, name):
        self._require(event_id)
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty str")
        if name in self._attendees[event_id]:
            raise AgendaError(f"{name!r} already attends {event_id!r}")
        clashes = self._conflicts(event_id, name)
        if clashes:
            raise ScheduleConflict(f"{name!r} already attends {clashes}")
        self._attendees[event_id].append(name)

    def get_events(self):
        return list(self._times)

    def get_time(self, event_id):
        self._require(event_id)
        return self._times[event_id]

    def get_attendees(self, event_id):
        self._require(event_id)
        return list(self._attendees[event_id])

    def get_schedule(self, name):
        # sorted() is stable, so events with equal starts keep the order added.
        attended = [e for e in self._times if name in self._attendees[e]]
        return sorted(attended, key=lambda e: self._times[e][0])

    def get_conflicts(self, event_id, name):
        self._require(event_id)
        return self._conflicts(event_id, name)

    def get_busy(self, name, start, end):
        check_times(start, end)
        periods = []
        # The schedule is sorted by start, and clipping keeps that order, so
        # each period only ever needs merging with the previous one.
        for event_id in self.get_schedule(name):
            first, last = self._times[event_id]
            first, last = max(first, start), min(last, end)
            if first >= last:
                continue  # entirely outside the window
            if periods and first < periods[-1][1]:
                periods[-1] = (periods[-1][0], max(periods[-1][1], last))
            else:
                periods.append((first, last))
        return periods

    def get_free(self, name, start, end):
        gaps = []
        cursor = start
        for first, last in self.get_busy(name, start, end):
            if first > cursor:
                gaps.append((cursor, first))
            cursor = last
        if cursor < end:
            gaps.append((cursor, end))
        return gaps

    def is_free(self, name, start, end):
        return not self.get_busy(name, start, end)

    def _conflicts(self, event_id, name):
        time = self._times[event_id]
        return [
            e
            for e in self.get_schedule(name)
            if e != event_id and overlaps(self._times[e], time)
        ]

    def _require(self, event_id):
        # Non-str ids are never stored, so they count as "does not exist" too.
        if not isinstance(event_id, str) or event_id not in self._times:
            raise KeyError(event_id)
