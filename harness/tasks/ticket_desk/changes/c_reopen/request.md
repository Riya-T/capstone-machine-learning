Let resolved tickets in `desk.py` be reopened, for example when the customer
writes back to say the problem is not fixed.

- Add `TicketDesk.reopen(ticket_id)`. It raises `KeyError` for a ticket that
  does not exist, then `DeskError` for a ticket that is not resolved.
- Reopening undoes the resolution: the ticket's status goes back to
  `"assigned"` and it returns to the queue of the agent who had it when it
  was resolved, in its usual place in opening order. From then on it behaves
  like any other assigned ticket: it can be reassigned, resolved again and
  reopened again.
- Add `TicketDesk.get_reopen_count(ticket_id) -> int`: how many times the
  ticket has been reopened. New tickets have a count of 0. `KeyError` for a
  ticket that does not exist.
- Reopening changes nothing else: the ticket's priority and every other
  ticket stay as they are.

All existing behavior must keep working.
