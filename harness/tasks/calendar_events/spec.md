# Agenda

Write a module `agenda.py` that keeps the events of one day and who attends
each of them.

## Interface

```python
class AgendaError(Exception): ...


class Agenda:
    def __init__(self): ...
    def add_event(self, event_id: str, start: int, end: int) -> None: ...
    def add_attendee(self, event_id: str, name: str) -> None: ...
    def get_events(self) -> list[str]: ...
    def get_time(self, event_id: str) -> tuple[int, int]: ...
    def get_attendees(self, event_id: str) -> list[str]: ...
    def get_schedule(self, name: str) -> list[str]: ...
```

All times are whole minutes since the start of the day, as `int`.

## Events

- `add_event(event_id, start, end)` adds an event that runs from `start` up
  to, but not including, `end`. An empty id raises `ValueError`. `start`
  must be an `int` that is 0 or more and `end` an `int` greater than
  `start`; anything else raises `ValueError`. There is no upper bound on
  times. Adding an id that already exists raises `AgendaError`.
- `get_events()` returns the ids of all events, in the order they were
  added.
- `get_time(event_id)` returns `(start, end)`.
- Every method that takes an event id raises `KeyError` when the id is not
  an existing event, including values that are not strings at all, such as
  `None` or `1`.

When `add_event` has several problems, `ValueError` for a bad id or bad
times is raised before `AgendaError` for a duplicate id. If both the id and
the times are bad, either `ValueError` may come first.

## Attendees

- `add_attendee(event_id, name)` adds a person to an event. An empty name
  raises `ValueError`. Adding someone who already attends that event raises
  `AgendaError`. A person may attend any number of events.
- `get_attendees(event_id)` returns the names attending the event, in the
  order they were added.
- `get_schedule(name)` returns the ids of every event the person attends,
  earliest start first, whatever the order the person was added to them. A
  name that attends nothing gives `[]`; it is not an error.

When `add_attendee` has several problems, the first of these is raised:

1. `KeyError` for an event that does not exist;
2. `ValueError` for an empty name;
3. `AgendaError` for a person who already attends the event.

A failed call has no effect: if a method raises, every event, time and
attendee list is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes ids and names that are not strings passed to `add_event` or as
`name`, `bool` times, the order of a person's events that share the same
start, what happens if a returned list is changed, the text of error
messages, saving the agenda to a file, and use from several threads.
