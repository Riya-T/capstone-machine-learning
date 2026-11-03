# Ticket desk

Write a module `desk.py` that tracks support tickets and the agents who work
on them. Each agent has a queue: the tickets they are working on, in the
order they got them.

## Interface

```python
class DeskError(Exception): ...


class TicketDesk:
    def __init__(self): ...
    def add_agent(self, agent_id: str) -> None: ...
    def open_ticket(self, ticket_id: str, priority: int) -> None: ...
    def assign(self, ticket_id: str, agent_id: str) -> None: ...
    def reassign(self, ticket_id: str, agent_id: str) -> None: ...
    def resolve(self, ticket_id: str) -> None: ...
    def get_priority(self, ticket_id: str) -> int: ...
    def get_queue(self, agent_id: str) -> list[str]: ...
```

A ticket is opened with no agent. `assign` gives it to its first agent,
`reassign` moves it from one agent to another, and `resolve` closes it,
which takes it out of its agent's queue.

## Unknown ids

Every method except `add_agent` and `open_ticket` raises `KeyError` when it
is given an agent id or a ticket id that the desk does not have, including
values that are not strings at all, such as `None` or `1`.

## Agents

`add_agent(agent_id)` adds an agent with an empty queue. It raises:

- `ValueError` if `agent_id` is an empty string;
- `DeskError` if an agent with that id already exists.

`get_queue(agent_id)` returns the ids of the tickets the agent has, in the
order the agent got them. A ticket that is reassigned to the agent goes
last, like one that was just assigned. An agent with no tickets gets `[]`.

## Tickets

`open_ticket(ticket_id, priority)` opens a ticket with no agent. It raises:

- `ValueError` if `ticket_id` is an empty string;
- `ValueError` if `priority` is not an `int` greater than 0, such as `0`,
  `-2`, `1.5`, `"3"` or `None`;
- `DeskError` if `ticket_id` is already in use.

When a call has several of these problems, the first one in this list is
raised.

`get_priority(ticket_id)` returns the ticket's priority.

## Assigning, reassigning and resolving

`assign(ticket_id, agent_id)` gives a ticket that has no agent to the agent.
The ticket goes at the end of the agent's queue. It raises:

- `KeyError` if the ticket or the agent does not exist;
- `DeskError` if the ticket already has an agent (`reassign` moves it).

`reassign(ticket_id, agent_id)` moves a ticket from the agent who has it to
`agent_id`. The ticket leaves the first agent's queue and goes at the end of
the new agent's queue. It raises:

- `KeyError` if the ticket or the agent does not exist;
- `DeskError` if the ticket has no agent (`assign` gives it one);
- `DeskError` if `agent_id` is the agent who already has the ticket.

`resolve(ticket_id)` resolves a ticket that an agent has. The ticket leaves
that agent's queue. It raises:

- `KeyError` if the ticket does not exist;
- `DeskError` if the ticket has no agent.

A failed call has no effect: if a method raises, every ticket and every
queue is unchanged.

## Example

```python
desk = TicketDesk()
desk.add_agent("kim")
desk.add_agent("lee")
desk.open_ticket("T1", 2)
desk.open_ticket("T2", 5)
desk.open_ticket("T3", 1)
desk.assign("T3", "kim")
desk.assign("T1", "kim")
desk.get_queue("kim")       # ["T3", "T1"]: the order kim got them
desk.assign("T1", "lee")    # raises DeskError: kim has T1
desk.reassign("T2", "lee")  # raises DeskError: T2 has no agent
desk.resolve("T2")          # raises DeskError: T2 has no agent
desk.reassign("T3", "lee")
desk.get_queue("kim")       # ["T1"]
desk.get_queue("lee")       # ["T3"]
desk.reassign("T3", "lee")  # raises DeskError: lee already has T3
desk.assign("T2", "kim")
desk.reassign("T3", "kim")
desk.get_queue("kim")       # ["T1", "T2", "T3"]: T3 came back last
desk.get_queue("lee")       # []
desk.resolve("T1")
desk.get_queue("kim")       # ["T2", "T3"]
desk.get_priority("T2")     # 5
desk.get_queue("max")       # raises KeyError: there is no agent max
```

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes everything about a ticket after it is resolved, other than leaving
its agent's queue: whether `get_priority` still returns its priority,
whether `open_ticket` can use its id again, and what `assign`, `reassign`
and `resolve` do with it. It also includes which error is raised when a call
has both a `KeyError` problem and a `DeskError` problem (such as an unknown
agent and a ticket that already has an agent), ids that are not strings
passed to `add_agent` or as the new id in `open_ticket`, `bool` priorities,
what happens if a returned list is changed, the text of error messages,
saving the desk to a file, and use from several threads.
