"""Ticket desk: support tickets, agents, assignment and resolution.

Correct solution for ticket_desk before any change (the initial spec).
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from desk import TicketDesk
    desk = TicketDesk()
    desk.add_agent("kim")
    desk.open_ticket("T1", 3)
    desk.assign("T1", "kim")
    desk.resolve("T1")
"""

OPEN, ASSIGNED, RESOLVED = "open", "assigned", "resolved"


class DeskError(Exception):
    pass


def check_id(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_priority(priority):
    if isinstance(priority, bool) or not isinstance(priority, int) or priority <= 0:
        raise ValueError(f"priority must be a positive int, got {priority!r}")


class Ticket:
    def __init__(self, priority):
        self.priority = priority
        self.status = OPEN
        self.agent = None  # the agent who has the ticket, once assigned


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

    def get_status(self, ticket_id):
        return self._require_ticket(ticket_id).status

    def get_priority(self, ticket_id):
        return self._require_ticket(ticket_id).priority

    def get_tickets(self, agent_id=None):
        if agent_id is None:
            return list(self._tickets)
        self._require_agent(agent_id)
        return [
            tid
            for tid, t in self._tickets.items()
            if t.agent == agent_id and t.status == ASSIGNED
        ]

    def _require_agent(self, agent_id):
        if not isinstance(agent_id, str) or agent_id not in self._agents:
            raise KeyError(agent_id)

    def _require_ticket(self, ticket_id):
        # Non-str ids are never stored, so they count as "unknown" too.
        if not isinstance(ticket_id, str) or ticket_id not in self._tickets:
            raise KeyError(ticket_id)
        return self._tickets[ticket_id]
