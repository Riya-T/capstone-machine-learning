"""Ticket desk with per-agent queue limits and reopening.

Planted bug (after c_limit and c_reopen): reopening was added correctly
(it skips the limit, as it should), but reassign lost its limit check along
the way, so reassigning still hands tickets to a full agent. Never shown to
the writer or the editor; validate-tasks checks that the tests catch it.

Usage:
    from desk import TicketDesk
    desk = TicketDesk()
    desk.add_agent("kim", limit=3)
    desk.open_ticket("T1", 3)
    desk.assign("T1", "kim")
    desk.resolve("T1")
    desk.reopen("T1")
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
        self.reopens = 0


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

    def reopen(self, ticket_id):
        ticket = self._require_ticket(ticket_id)
        if not ticket.resolved:
            raise DeskError(f"ticket {ticket_id!r} is not resolved")
        ticket.resolved = False
        ticket.reopens += 1
        # Back to the agent who resolved it; the limit applies to assign and
        # reassign only, so reopening never raises AgentFull.
        self._queues[ticket.agent].append(ticket_id)

    def get_priority(self, ticket_id):
        return self._require_ticket(ticket_id).priority

    def get_reopen_count(self, ticket_id):
        return self._require_ticket(ticket_id).reopens

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
