"""Rate limiter where clients can be blocked.

Correct solution for token_bucket after c_block.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from limiter import RateLimiter
    limiter = RateLimiter(window=10)
    limiter.add_client("alice", allowance=3)
    limiter.block("alice")
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
        if client_id in self._blocked:
            return 0
        return self._allowances[client_id] - self._used(client_id)

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
