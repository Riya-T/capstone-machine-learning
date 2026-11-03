Add ways to look up tickets by priority in `desk.py`, so the desk can see
what needs attention first, and to see which tickets each agent has
resolved.

- Add `TicketDesk.get_by_priority(agent_id=None, min_priority=1) -> list[str]`:
  tickets whose priority is at least `min_priority`, the highest priority
  first.
  - With an `agent_id`, it lists the tickets in `get_queue(agent_id)`.
    Tickets with the same priority keep their queue order.
  - With no `agent_id`, it lists every ticket that is not resolved, whether
    or not it has an agent. Tickets with the same priority keep the order
    they were opened in.

  For example, if `T1` and then `T3` were opened, both with priority 2, and
  `kim` got `T3` and then `T1`, `get_by_priority("kim")` is `["T3", "T1"]`
  while `get_by_priority()` is `["T1", "T3"]`. `min_priority` must be an
  `int` greater than 0, or `ValueError` is raised; `KeyError` for an unknown
  agent is raised first.
- Add `TicketDesk.get_priority_counts() -> list[tuple[int, int]]`: one
  `(priority, count)` pair for each priority that at least one unresolved
  ticket has, the highest priority first. Tickets with or without an agent
  both count.
- Add `TicketDesk.get_resolved(agent_id=None) -> list[str]`: the ids of the
  tickets that are resolved right now, in the order they were opened. With
  an `agent_id`, only the tickets that agent had when they were resolved.
  `KeyError` for an unknown agent.

All existing behavior must keep working.
