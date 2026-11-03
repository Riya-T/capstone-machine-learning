"""Ticket desk with per-agent queue limits.

Correct solution for ticket_desk after c_limit.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from desk import TicketDesk
    desk = TicketDesk()
    desk.add_agent("kim", limit=3)
    desk.open_ticket("T1", 3)
    desk.assign("T1", "kim")
    desk.set_limit("kim", 1)
    desk.get_queue("kim")
"""


class DeskError(Exception):
    pass


class AgentFull(DeskError):
    pass


def check_id(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_priority(priority):
    if isinstance(priority, bool) or not isinstance(priority, int) or priority <= 0:
        raise ValueError(f"priority must be a positive int, got {priority!r}")


def check_limit(limit):
    if limit is None:
        return
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
        raise ValueError(f"limit must be None or an int >= 0, got {limit!r}")


class Ticket:
    def __init__(self, priority):
        self.priority = priority
        self.agent = None  # the agent who has the ticket, kept once it is resolved
        self.resolved = False


class TicketDesk:
    def __init__(self):
        self._queues = {}  # agent id -> ticket ids, in the order the agent got them
        self._limits = {}  # agent id -> limit, or None for no limit
        self._tickets = {}  # ticket id -> Ticket, in opening order

    def add_agent(self, agent_id, limit=None):
        check_id(agent_id, "agent_id")
        check_limit(limit)
        if agent_id in self._queues:
            raise DeskError(f"agent {agent_id!r} already exists")
        self._queues[agent_id] = []
        self._limits[agent_id] = limit

    def open_ticket(self, ticket_id, priority):
        check_id(ticket_id, "ticket_id")
        check_priority(priority)
        if ticket_id in self._tickets:
            raise DeskError(f"ticket {ticket_id!r} already exists")
        self._tickets[ticket_id] = Ticket(priority)

    def assign(self, ticket_id, agent_id):
        ticket = self._require_ticket(ticket_id)
        self._require_agent(agent_id)
        if ticket.resolved:
            raise DeskError(f"ticket {ticket_id!r} is resolved")
        if ticket.agent is not None:
            raise DeskError(f"ticket {ticket_id!r} already has an agent; reassign it")
        self._check_room(agent_id)
        ticket.agent = agent_id
        self._queues[agent_id].append(ticket_id)

    def reassign(self, ticket_id, agent_id):
        ticket = self._require_ticket(ticket_id)
        self._require_agent(agent_id)
        if ticket.resolved:
            raise DeskError(f"ticket {ticket_id!r} is resolved")
        if ticket.agent is None:
            raise DeskError(f"ticket {ticket_id!r} has no agent; assign it")
        if ticket.agent == agent_id:
            raise DeskError(f"agent {agent_id!r} already has ticket {ticket_id!r}")
        self._check_room(agent_id)
        self._queues[ticket.agent].remove(ticket_id)
        ticket.agent = agent_id
        self._queues[agent_id].append(ticket_id)

    def resolve(self, ticket_id):
        ticket = self._require_ticket(ticket_id)
        if ticket.resolved:
            raise DeskError(f"ticket {ticket_id!r} is already resolved")
        if ticket.agent is None:
            raise DeskError(f"ticket {ticket_id!r} has no agent")
        self._queues[ticket.agent].remove(ticket_id)
        ticket.resolved = True

    def get_priority(self, ticket_id):
        return self._require_ticket(ticket_id).priority

    def get_limit(self, agent_id):
        self._require_agent(agent_id)
        return self._limits[agent_id]

    def set_limit(self, agent_id, limit):
        self._require_agent(agent_id)
        check_limit(limit)
        if limit is not None and len(self._queues[agent_id]) > limit:
            raise DeskError(f"agent {agent_id!r} already has more than {limit} tickets")
        self._limits[agent_id] = limit

    def get_queue(self, agent_id):
        self._require_agent(agent_id)
        return list(self._queues[agent_id])

    def _check_room(self, agent_id):
        limit = self._limits[agent_id]
        if limit is not None and len(self._queues[agent_id]) >= limit:
            raise AgentFull(f"agent {agent_id!r} already has {limit} tickets")

    def _require_agent(self, agent_id):
        if not isinstance(agent_id, str) or agent_id not in self._queues:
            raise KeyError(agent_id)

    def _require_ticket(self, ticket_id):
        # Non-str ids are never stored, so they count as "unknown" too.
        if not isinstance(ticket_id, str) or ticket_id not in self._tickets:
            raise KeyError(ticket_id)
        return self._tickets[ticket_id]
