"""Agenda: the events of one day and who attends each of them.

Planted bug (initial version): an event whose end equals its start is
accepted (the check uses < instead of <=). The public checks only try an
end before the start, so only the hidden initial tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from agenda import Agenda
    agenda = Agenda()
    agenda.add_event("standup", 540, 555)
    agenda.add_attendee("standup", "mira")
"""


class AgendaError(Exception):
    pass


def check_times(start, end):
    for value in (start, end):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"times must be int, got {value!r}")
    if start < 0 or end < start:
        raise ValueError(f"need 0 <= start < end, got {start} and {end}")


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

    def _require(self, event_id):
        # Non-str ids are never stored, so they count as "does not exist" too.
        if not isinstance(event_id, str) or event_id not in self._times:
            raise KeyError(event_id)
