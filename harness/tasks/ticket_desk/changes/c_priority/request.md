Add ways to look up tickets by status and by priority in `desk.py`, so the
desk can see what needs attention first.

- `get_tickets` takes a new keyword argument `status=None`. With a status
  (`"open"`, `"assigned"` or `"resolved"`) only tickets with that status are
  returned, in opening order. Any other status value raises `ValueError`.
  With both an `agent_id` and a `status`, only that agent's tickets with
  that status are returned: for `"assigned"` the tickets in the agent's
  queue, and for `"resolved"` the tickets the agent had when they were
  resolved. `"open"` with an agent always gives an empty list, since open
  tickets have no agent. `KeyError` for an unknown agent is raised before
  `ValueError` for a bad status.
- Add `TicketDesk.get_queue(agent_id=None, min_priority=1) -> list[str]`:
  the ids of the tickets that are not resolved, the highest priority first.
  Tickets with the same priority are listed in the order they were opened.
  With an `agent_id`, only the tickets in that agent's queue; with a
  `min_priority`, only tickets whose priority is at least that value.
  `min_priority` must be an `int` greater than 0, or `ValueError` is
  raised; `KeyError` for an unknown agent is raised first.
- Add `TicketDesk.get_priority_counts() -> list[tuple[int, int]]`: one
  `(priority, count)` pair for each priority that at least one unresolved
  ticket has, the highest priority first.

All existing behavior must keep working.
