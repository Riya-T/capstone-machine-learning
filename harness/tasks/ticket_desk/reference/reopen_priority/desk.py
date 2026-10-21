"""Ticket desk with reopening and queries by status and priority.

Correct solution for ticket_desk after c_reopen and c_priority.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from desk import TicketDesk
    desk = TicketDesk()
    desk.add_agent("kim")
    desk.open_ticket("T1", 3)
    desk.assign("T1", "kim")
    desk.resolve("T1")
    desk.reopen("T1")
    desk.get_queue("kim")
"""

OPEN, ASSIGNED, RESOLVED = "open", "assigned", "resolved"
STATUSES = (OPEN, ASSIGNED, RESOLVED)


class DeskError(Exception):
    pass


def check_id(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_priority(priority, what="priority"):
    if isinstance(priority, bool) or not isinstance(priority, int) or priority <= 0:
        raise ValueError(f"{what} must be a positive int, got {priority!r}")


class Ticket:
    def __init__(self, priority):
        self.priority = priority
        self.status = OPEN
        self.agent = None  # the agent who has (or resolved) the ticket
        self.reopens = 0


class TicketDesk:
    def __init__(self):
        self._agents = []  # agent ids in the order added
        self._tickets = {}  # ticket id -> Ticket, in opening order

    def add_agent(self, agent_id):
        check_id(agent_id, "agent_id")
        if agent_id in self._agents:
            raise DeskError(f"agent {agent_id!r} already exists")
        self._agents.append(agent_id)

    def open_ticket(self, ticket_id, priority):
        check_id(ticket_id, "ticket_id")
        check_priority(priority)
        if ticket_id in self._tickets:
            raise DeskError(f"ticket {ticket_id!r} already exists")
        self._tickets[ticket_id] = Ticket(priority)

    def assign(self, ticket_id, agent_id):
        ticket = self._require_ticket(ticket_id)
        self._require_agent(agent_id)
        if ticket.status == RESOLVED:
            raise DeskError(f"ticket {ticket_id!r} is resolved")
        if ticket.agent == agent_id:
            raise DeskError(f"ticket {ticket_id!r} is already assigned to {agent_id!r}")
        ticket.agent = agent_id
        ticket.status = ASSIGNED

    def resolve(self, ticket_id):
        ticket = self._require_ticket(ticket_id)
        if ticket.status != ASSIGNED:
            raise DeskError(f"ticket {ticket_id!r} is {ticket.status}, not assigned")
        ticket.status = RESOLVED

    def reopen(self, ticket_id):
        ticket = self._require_ticket(ticket_id)
        if ticket.status != RESOLVED:
            raise DeskError(f"ticket {ticket_id!r} is {ticket.status}, not resolved")
        ticket.status = ASSIGNED  # the agent who resolved it still holds it
        ticket.reopens += 1

    def get_status(self, ticket_id):
        return self._require_ticket(ticket_id).status

    def get_priority(self, ticket_id):
        return self._require_ticket(ticket_id).priority

    def get_reopen_count(self, ticket_id):
        return self._require_ticket(ticket_id).reopens

    def get_tickets(self, agent_id=None, status=None):
        if agent_id is not None:
            self._require_agent(agent_id)
        if status is not None and status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}, got {status!r}")
        return [tid for tid, t in self._tickets.items() if self._matches(t, agent_id, status)]

    def get_queue(self, agent_id=None, min_priority=1):
        if agent_id is not None:
            self._require_agent(agent_id)
        check_priority(min_priority, "min_priority")
        unresolved = [
            tid
            for tid, t in self._tickets.items()
            if t.status != RESOLVED
            and (agent_id is None or t.status == ASSIGNED and t.agent == agent_id)
            and t.priority >= min_priority
        ]
        # sorted is stable, so equal priorities keep opening order.
        return sorted(unresolved, key=lambda tid: -self._tickets[tid].priority)

    def get_priority_counts(self):
        counts = {}
        for t in self._tickets.values():
            if t.status != RESOLVED:
                counts[t.priority] = counts.get(t.priority, 0) + 1
        return sorted(counts.items(), reverse=True)

    def _matches(self, ticket, agent_id, status):
        """Does the ticket belong in get_tickets(agent_id, status)?"""
        if status is not None and ticket.status != status:
            return False
        if agent_id is None:
            return True
        if ticket.agent != agent_id:
            return False
        # An agent's tickets: their queue, or their resolved ones when asked.
        return ticket.status == ASSIGNED or status == RESOLVED

    def _require_agent(self, agent_id):
        if not isinstance(agent_id, str) or agent_id not in self._agents:
            raise KeyError(agent_id)

    def _require_ticket(self, ticket_id):
        # Non-str ids are never stored, so they count as "unknown" too.
        if not isinstance(ticket_id, str) or ticket_id not in self._tickets:
            raise KeyError(ticket_id)
        return self._tickets[ticket_id]
