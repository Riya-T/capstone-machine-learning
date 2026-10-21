"""Order workflow where moves can be undone, with a history of the states
each order has been in.

Correct solution for order_workflow after c_rollback and c_history. A
rollback removes the undone move from the history, as if it never happened.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from workflow import OrderWorkflow
    flow = OrderWorkflow()
    flow.create_order("o1", 2500)
    flow.move("o1", "paid")
    flow.get_history("o1")  # ["new", "paid"]
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
        self._history = {}  # order id -> states entered, oldest first, in creation order
        self._totals = {}  # order id -> total in cents

    def create_order(self, order_id, total):
        if not isinstance(order_id, str) or not order_id:
            raise ValueError("order_id must be a non-empty str")
        if isinstance(total, bool) or not isinstance(total, int) or total <= 0:
            raise ValueError(f"total must be a positive int, got {total!r}")
        if order_id in self._history:
            raise WorkflowError(f"order {order_id!r} already exists")
        self._history[order_id] = ["new"]
        self._totals[order_id] = total

    def move(self, order_id, state):
        self._require(order_id)
        check_state_name(state)
        if (self._history[order_id][-1], state) not in ALLOWED:
            raise InvalidTransition(f"cannot move {order_id!r} to {state!r}")
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

    def rollback(self, order_id):
        self._require(order_id)
        states = self._history[order_id]
        if states[-1] == "delivered":
            raise InvalidTransition(f"order {order_id!r} was delivered; that cannot be undone")
        if len(states) == 1:
            raise WorkflowError(f"order {order_id!r} has no move to undo")
        states.pop()

    def _require(self, order_id):
        # Non-str ids are never stored, so they count as "does not exist" too.
        if not isinstance(order_id, str) or order_id not in self._history:
            raise KeyError(order_id)
