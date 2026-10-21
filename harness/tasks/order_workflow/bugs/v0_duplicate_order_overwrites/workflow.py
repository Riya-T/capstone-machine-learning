"""Order workflow: orders that move along a fixed set of allowed paths.

Planted bug (initial version): creating an order whose id already exists
silently replaces it instead of raising WorkflowError. The public checks
never create an order twice, so only the hidden initial tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from workflow import OrderWorkflow
    flow = OrderWorkflow()
    flow.create_order("o1", 2500)
    flow.move("o1", "paid")
"""

STATES = ("new", "paid", "shipped", "delivered", "cancelled")

ALLOWED = {
    ("new", "paid"),
    ("paid", "shipped"),
    ("shipped", "delivered"),
    ("new", "cancelled"),
    ("paid", "cancelled"),
}


class WorkflowError(Exception):
    pass


class InvalidTransition(WorkflowError):
    pass


def check_state_name(state):
    if state not in STATES:
        raise ValueError(f"unknown state {state!r}")


class OrderWorkflow:
    def __init__(self):
        self._states = {}  # order id -> current state, in creation order
        self._totals = {}  # order id -> total in cents

    def create_order(self, order_id, total):
        if not isinstance(order_id, str) or not order_id:
            raise ValueError("order_id must be a non-empty str")
        if isinstance(total, bool) or not isinstance(total, int) or total <= 0:
            raise ValueError(f"total must be a positive int, got {total!r}")
        self._states[order_id] = "new"
        self._totals[order_id] = total

    def move(self, order_id, state):
        self._require(order_id)
        check_state_name(state)
        if (self._states[order_id], state) not in ALLOWED:
            raise InvalidTransition(f"cannot move {order_id!r} to {state!r}")
        self._states[order_id] = state

    def get_state(self, order_id):
        self._require(order_id)
        return self._states[order_id]

    def get_total(self, order_id):
        self._require(order_id)
        return self._totals[order_id]

    def get_orders(self):
        return list(self._states)

    def get_orders_in(self, state):
        check_state_name(state)
        return [o for o, s in self._states.items() if s == state]

    def _require(self, order_id):
        # Non-str ids are never stored, so they count as "does not exist" too.
        if not isinstance(order_id, str) or order_id not in self._states:
            raise KeyError(order_id)
