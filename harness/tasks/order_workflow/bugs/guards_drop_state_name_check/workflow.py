"""Order workflow with a state history and optional guarded transitions: an
order is paid only once its payments cover the total, and shipped only once
it has an address.

Planted bug (after c_history and c_guards): the guards were added
correctly, but while rewriting move the state-name check was dropped, so an
unknown state name raises InvalidTransition instead of ValueError. Never
shown to the writer or the editor; validate-tasks checks that the tests
catch it.

Usage:
    from workflow import OrderWorkflow
    flow = OrderWorkflow(guarded=True)
    flow.create_order("o1", 2500)
    flow.record_payment("o1", 2500)
    flow.move("o1", "paid")
    flow.set_address("o1", "1 Main St")
    flow.move("o1", "shipped")
"""

STATES = ("new", "paid", "shipped", "delivered", "cancelled")

ALLOWED = {
    ("new", "paid"),
    ("paid", "shipped"),
    ("shipped", "delivered"),
    ("new", "cancelled"),
    ("paid", "cancelled"),
}

# States in which the address may still be set or changed.
ADDRESSABLE = ("new", "paid")


class WorkflowError(Exception):
    pass


class InvalidTransition(WorkflowError):
    pass


class GuardFailed(WorkflowError):
    pass


def check_state_name(state):
    if state not in STATES:
        raise ValueError(f"unknown state {state!r}")


def check_amount(amount):
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise ValueError(f"amount must be a positive int, got {amount!r}")


class OrderWorkflow:
    def __init__(self, guarded=False):
        self._history = {}  # order id -> states entered, oldest first, in creation order
        self._totals = {}  # order id -> total in cents
        self._addresses = {}  # order id -> delivery address, "" when unset
        self._paid = {}  # order id -> sum of payments in cents
        # Guards by target state: each must hold for the move to be allowed.
        self._guards = {}
        if guarded:
            self._guards = {"paid": self._is_fully_paid, "shipped": self._has_address}

    def create_order(self, order_id, total):
        if not isinstance(order_id, str) or not order_id:
            raise ValueError("order_id must be a non-empty str")
        if isinstance(total, bool) or not isinstance(total, int) or total <= 0:
            raise ValueError(f"total must be a positive int, got {total!r}")
        if order_id in self._history:
            raise WorkflowError(f"order {order_id!r} already exists")
        self._history[order_id] = ["new"]
        self._totals[order_id] = total
        self._addresses[order_id] = ""
        self._paid[order_id] = 0

    def move(self, order_id, state):
        self._require(order_id)
        if (self._history[order_id][-1], state) not in ALLOWED:
            raise InvalidTransition(f"cannot move {order_id!r} to {state!r}")
        guard = self._guards.get(state)
        if guard is not None and not guard(order_id):
            raise GuardFailed(f"order {order_id!r} is not ready to be {state}")
        self._history[order_id].append(state)

    def get_state(self, order_id):
        self._require(order_id)
        return self._history[order_id][-1]

    def get_total(self, order_id):
        self._require(order_id)
        return self._totals[order_id]

    def get_orders(self):
        return list(self._history)

    def get_orders_in(self, state):
        check_state_name(state)
        return [o for o, h in self._history.items() if h[-1] == state]

    def get_history(self, order_id):
        self._require(order_id)
        return list(self._history[order_id])

    def get_move_count(self, order_id):
        self._require(order_id)
        return len(self._history[order_id]) - 1

    def get_orders_that_passed(self, state):
        check_state_name(state)
        return [o for o, h in self._history.items() if state in h]

    def set_address(self, order_id, address):
        self._require(order_id)
        if not isinstance(address, str) or not address:
            raise ValueError("address must be a non-empty str")
        if self._history[order_id][-1] not in ADDRESSABLE:
            raise WorkflowError(f"order {order_id!r} can no longer change its address")
        self._addresses[order_id] = address

    def get_address(self, order_id):
        self._require(order_id)
        return self._addresses[order_id]

    def record_payment(self, order_id, amount):
        self._require(order_id)
        check_amount(amount)
        if self._paid[order_id] + amount > self._totals[order_id]:
            raise ValueError(f"payment of {amount} would exceed the total of {order_id!r}")
        self._paid[order_id] += amount

    def get_paid(self, order_id):
        self._require(order_id)
        return self._paid[order_id]

    def _is_fully_paid(self, order_id):
        return self._paid[order_id] == self._totals[order_id]

    def _has_address(self, order_id):
        return self._addresses[order_id] != ""

    def _require(self, order_id):
        # Non-str ids are never stored, so they count as "does not exist" too.
        if not isinstance(order_id, str) or order_id not in self._history:
            raise KeyError(order_id)
