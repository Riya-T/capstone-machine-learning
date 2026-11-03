"""Ticket desk with reopening and queries by priority.

Planted bug (after c_reopen and c_priority): the priority and resolved-ticket
queries were added correctly, but reopen no longer increases the ticket's
reopen count. Never shown to the writer or the editor; validate-tasks checks
that the tests catch it.

Usage:
    from desk import TicketDesk
    desk = TicketDesk()
    desk.add_agent("kim")
    desk.open_ticket("T1", 3)
    desk.assign("T1", "kim")
    desk.resolve("T1")
    desk.reopen("T1")
    desk.get_by_priority("kim")
"""


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
        self.agent = None  # the agent who has the ticket, kept once it is resolved
        self.resolved = False
        self.reopens = 0


class TicketDesk:
    def __init__(self):
        self._queues = {}  # agent id -> ticket ids, in the order the agent got them
        self._tickets = {}  # ticket id -> Ticket, in opening order

    def add_agent(self, agent_id):
        check_id(agent_id, "agent_id")
        if agent_id in self._queues:
            raise DeskError(f"agent {agent_id!r} already exists")
        self._queues[agent_id] = []

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
        self._queues[ticket.agent].append(ticket_id)  # back to the agent who resolved it

    def get_priority(self, ticket_id):
        return self._require_ticket(ticket_id).priority

    def get_reopen_count(self, ticket_id):
        return self._require_ticket(ticket_id).reopens

    def get_queue(self, agent_id):
        self._require_agent(agent_id)
        return list(self._queues[agent_id])

    def get_by_priority(self, agent_id=None, min_priority=1):
        if agent_id is None:  # every unresolved ticket, in opening order
            tickets = [tid for tid, t in self._tickets.items() if not t.resolved]
        else:
            tickets = self.get_queue(agent_id)  # KeyError for an unknown agent first
        check_priority(min_priority, "min_priority")
        wanted = [tid for tid in tickets if self._tickets[tid].priority >= min_priority]
        # sorted is stable, so equal priorities keep the order they were listed in.
        return sorted(wanted, key=lambda tid: -self._tickets[tid].priority)

    def get_priority_counts(self):
        counts = {}
        for t in self._tickets.values():
            if not t.resolved:
                counts[t.priority] = counts.get(t.priority, 0) + 1
        return sorted(counts.items(), reverse=True)

    def get_resolved(self, agent_id=None):
        if agent_id is not None:
            self._require_agent(agent_id)
        return [
            tid
            for tid, t in self._tickets.items()
            if t.resolved and (agent_id is None or t.agent == agent_id)
        ]

    def _require_agent(self, agent_id):
        if not isinstance(agent_id, str) or agent_id not in self._queues:
            raise KeyError(agent_id)

    def _require_ticket(self, ticket_id):
        # Non-str ids are never stored, so they count as "unknown" too.
        if not isinstance(ticket_id, str) or ticket_id not in self._tickets:
            raise KeyError(ticket_id)
        return self._tickets[ticket_id]
