Limit how many tickets an agent in `desk.py` can be working on at once.

- `add_agent` takes a new keyword argument `limit=None`: the most tickets
  the agent may have in their queue at one time. `None` means no limit.
  Otherwise it must be an `int` that is 0 or more (not a `bool`); anything
  else raises `ValueError` and no agent is added. If both the agent id and
  the limit are invalid, either `ValueError` may come first. The `DeskError`
  for an agent that already exists is checked after both.
- Add `class AgentFull(DeskError)` to `desk.py`. `assign` raises `AgentFull`
  and changes nothing when the agent's queue already holds as many tickets
  as their limit. Moving a ticket between two agents counts against the
  receiving agent only. `AgentFull` is checked last, after every `KeyError`
  and every other `DeskError` of `assign`.
- Add `TicketDesk.get_limit(agent_id) -> int | None`, which returns the
  agent's current limit, and `TicketDesk.set_limit(agent_id, limit)`, which
  replaces it. Both raise `KeyError` for an unknown agent; `set_limit` then
  raises `ValueError` for an invalid limit, then `DeskError` if the agent's
  queue already holds more tickets than the new limit. In each case nothing
  changes. A queue that is exactly at the new limit is fine.
- The limit applies to `assign` only. Tickets that leave the queue by being
  resolved or reassigned free up room.

All existing behavior must keep working.
