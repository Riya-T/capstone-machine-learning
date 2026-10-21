Let events in `agenda.py` be cancelled and attendees be taken off events.

- Add `Agenda.cancel_event(event_id)`. Afterwards the event is gone: it is
  not in `get_events()`, it is in nobody's schedule, and every method that
  takes an event id raises `KeyError` for it, including `cancel_event`
  itself. A cancelled event no longer counts for any check or query. The
  id may be given to `add_event` again, which makes a fresh event with no
  attendees. `cancel_event` raises `KeyError` for an event that does not
  exist.
- Add `Agenda.get_cancelled() -> list[str]`: the ids of cancelled events,
  in the order they were cancelled. An id stays in this list even if it is
  added again.
- Add `Agenda.remove_attendee(event_id, name)`, which takes the person off
  the event. Afterwards the event is not in the person's schedule, the
  other attendees keep their order, and the person may be added to the
  event again. It raises `KeyError` for an event that does not exist, then
  `AgendaError` for a name that does not attend the event (an empty name
  included). In each case nothing changes.
- Cancelling an event or removing an attendee leaves every other event and
  every other attendee exactly as it was.

All existing behavior must keep working.
