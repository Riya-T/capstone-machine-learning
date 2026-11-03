Let resolved tickets in `desk.py` be reopened, for example when the customer
writes back to say the problem is not fixed.

- A resolved ticket now stays on the desk, in nobody's queue, until it is
  reopened:
  - `get_priority` still returns its priority;
  - its id stays in use, so `open_ticket` with that id raises `DeskError`;
  - `assign`, `reassign` and `resolve` raise `DeskError` for it.
- Add `TicketDesk.reopen(ticket_id)`. It raises `KeyError` for a ticket that
  does not exist, and `DeskError` for a ticket that is not resolved.
- Reopening undoes the resolution: the ticket goes back to the agent who had
  it when it was resolved, at the end of that agent's queue. From then on it
  behaves like any other ticket that an agent has: it can be reassigned,
  resolved again and reopened again, and `assign` refuses it because it has
  an agent.
- Add `TicketDesk.get_reopen_count(ticket_id) -> int`: how many times the
  ticket has been reopened. New tickets have a count of 0. `KeyError` for a
  ticket that does not exist.
- Reopening changes nothing else: the ticket's priority, every other ticket
  and every other queue stay as they are.

When `assign` or `reassign` is given both a resolved ticket and an unknown
agent, either `KeyError` or `DeskError` may be raised. All existing behavior
must keep working.
