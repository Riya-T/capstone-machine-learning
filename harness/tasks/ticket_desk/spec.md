# Ticket desk

Write a module `desk.py` that tracks support tickets, the agents who work on
them, and which agent each ticket is assigned to.

## Interface

```python
class DeskError(Exception): ...


class TicketDesk:
    def __init__(self): ...
    def add_agent(self, agent_id: str) -> None: ...
    def open_ticket(self, ticket_id: str, priority: int) -> None: ...
    def assign(self, ticket_id: str, agent_id: str) -> None: ...
    def resolve(self, ticket_id: str) -> None: ...
    def get_status(self, ticket_id: str) -> str: ...
    def get_priority(self, ticket_id: str) -> int: ...
    def get_tickets(self, agent_id: str | None = None) -> list[str]: ...
```

A ticket's status is one of the strings `"open"`, `"assigned"` and
`"resolved"`.

## Agents

- `add_agent(agent_id)` adds an agent. An empty id raises `ValueError`, and
  adding an id that already exists raises `DeskError`.
- Every other method that takes an `agent_id` raises `KeyError` when the
  agent does not exist, including values that are not strings at all, such
  as `1`.

## Tickets

- `open_ticket(ticket_id, priority)` opens a ticket with status `"open"`.
  An empty ticket id raises `ValueError`. The priority must be an `int`
  greater than 0, or `ValueError` is raised. A ticket id that is already in
  use raises `DeskError`. When a call has several problems, the first of
  these is raised: `ValueError` for the ticket id, `ValueError` for the
  priority, `DeskError` for the duplicate ticket.
- `assign(ticket_id, agent_id)` gives the ticket to the agent and sets its
  status to `"assigned"`. A ticket that is already assigned can be
  reassigned to another agent, which takes it away from the first one.
  Assigning a ticket to the agent who already has it raises `DeskError`.
  A resolved ticket cannot be assigned: that raises `DeskError`.
- `resolve(ticket_id)` sets the status to `"resolved"`. Only an assigned
  ticket can be resolved: resolving an open or an already resolved ticket
  raises `DeskError`.
- `get_status(ticket_id)` and `get_priority(ticket_id)` return the ticket's
  current status and its priority.
- Every method that takes a `ticket_id` other than `open_ticket` raises
  `KeyError` when the ticket does not exist, including values that are not
  strings at all, such as `None` or `1`.

When `assign` has several problems, the first of these is raised: `KeyError`
for the ticket, `KeyError` for the agent, `DeskError` for a resolved ticket,
`DeskError` for the agent who already has it.

## Listing tickets

- `get_tickets()` returns the ids of all tickets, in the order they were
  opened, whatever their status.
- `get_tickets(agent_id)` returns the agent's queue: the ids of the tickets
  that are assigned to that agent and not yet resolved, in the order they
  were opened. An agent with nothing to do gets an empty list.

A failed call has no effect: if a method raises, every ticket, every status
and every assignment is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes ids that are not strings passed to `add_agent` or as the new id in
`open_ticket`, `bool` priorities, what happens if a returned list is
changed, the text of error messages, saving the desk to a file, and use from
several threads.
