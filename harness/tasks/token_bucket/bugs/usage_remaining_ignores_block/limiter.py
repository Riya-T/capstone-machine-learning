"""Rate limiter where clients can be blocked, with usage queries.

Planted bug (after c_block and c_usage): the usage queries were added
correctly, but get_remaining was rewritten on top of the new range count
and no longer returns 0 for a blocked client. Never shown to the writer or
the editor; validate-tasks checks that the tests catch it.

Usage:
    from limiter import RateLimiter
    limiter = RateLimiter(window=10)
    limiter.add_client("alice", allowance=3)
    limiter.request("alice")
    limiter.get_usage("alice", 0, 10)
"""


class LimiterError(Exception):
    pass


class RateLimited(LimiterError):
    pass


class ClientBlocked(LimiterError):
    pass


def check_positive(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{what} must be a positive int, got {value!r}")


def check_range(start, end):
    for value in (start, end):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"range bounds must be ints >= 0, got {value!r}")
    if start > end:
        raise ValueError(f"start {start} is after end {end}")


class RateLimiter:
    def __init__(self, window):
        check_positive(window, "window")
        self._window = window
        self._time = 0
        self._next_receipt = 1
        self._allowances = {}  # client id -> allowance, in registration order
        self._requests = {}  # client id -> list of times of successful requests
        self._blocked = set()

    def add_client(self, client_id, allowance):
        if not isinstance(client_id, str) or not client_id:
            raise ValueError("client_id must be a non-empty str")
        check_positive(allowance, "allowance")
        if client_id in self._allowances:
            raise LimiterError(f"client {client_id!r} is already registered")
        self._allowances[client_id] = allowance
        self._requests[client_id] = []

    def tick(self, steps=1):
        check_positive(steps, "steps")
        self._time += steps

    def request(self, client_id):
        self._require(client_id)
        self._require_unblocked(client_id)
        if self._used(client_id) >= self._allowances[client_id]:
            raise RateLimited(f"client {client_id!r} has no requests left in this window")
        self._requests[client_id].append(self._time)
        receipt = self._next_receipt
        self._next_receipt += 1
        return receipt

    def get_remaining(self, client_id):
        self._require(client_id)
        start = self._time // self._window * self._window
        return self._allowances[client_id] - self._count_between(client_id, start, start + self._window)

    def get_time(self):
        return self._time

    def get_clients(self):
        return list(self._allowances)

    def block(self, client_id):
        self._require(client_id)
        self._blocked.add(client_id)

    def unblock(self, client_id):
        self._require(client_id)
        self._blocked.discard(client_id)

    def is_blocked(self, client_id):
        self._require(client_id)
        return client_id in self._blocked

    def get_request_times(self, client_id):
        self._require(client_id)
        return list(self._requests[client_id])

    def get_usage(self, client_id, start, end):
        self._require(client_id)
        check_range(start, end)
        return self._count_between(client_id, start, end)

    def get_active_clients(self, start, end):
        check_range(start, end)
        return [c for c in self._allowances if self._count_between(c, start, end) > 0]

    def _count_between(self, client_id, start, end):
        return sum(1 for t in self._requests[client_id] if start <= t < end)

    def _require(self, client_id):
        # Non-str ids are never stored, so they count as "not registered" too.
        if not isinstance(client_id, str) or client_id not in self._allowances:
            raise KeyError(client_id)

    def _require_unblocked(self, client_id):
        if client_id in self._blocked:
            raise ClientBlocked(f"client {client_id!r} is blocked")

    def _used(self, client_id):
        """Successful requests the client made in the current window."""
        current = self._time // self._window
        return sum(1 for t in self._requests[client_id] if t // self._window == current)
