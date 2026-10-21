Stop people in `agenda.py` from being double-booked: a person may no longer
attend two events that overlap.

- Add `class ScheduleConflict(AgendaError)` to `agenda.py`.
- Two events overlap when each starts before the other ends. An event that
  ends exactly when another starts does not overlap it.
- `add_attendee(event_id, name)` raises `ScheduleConflict` when the person
  already attends an event that overlaps `event_id`, and nothing changes.
  This check comes last: after `KeyError` for a missing event, `ValueError`
  for an empty name and `AgendaError` for someone who already attends the
  event itself.
- Add `Agenda.get_conflicts(event_id, name) -> list[str]`: the ids of the
  events the person attends that overlap `event_id`, not counting
  `event_id` itself, in the same order as `get_schedule` (earliest start
  first). It raises `KeyError` for an event that does not exist. A name
  that attends nothing gives `[]`. Whether the person attends `event_id`
  makes no difference to the result.

All existing behavior must keep working.
