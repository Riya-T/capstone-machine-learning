"""Subscription billing: plans, subscribed customers and billing cycles.

Planted bug (initial spec): a move to a plan with the same price records a
charge of 0.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from billing import BillingSystem
    billing = BillingSystem()
    billing.add_plan("basic", 900)
    billing.subscribe("alice", "basic")
    billing.run_cycle()
"""


class BillingError(Exception):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str")


def check_price(price):
    if isinstance(price, bool) or not isinstance(price, int) or price <= 0:
        raise ValueError(f"price must be a positive int, got {price!r}")


class BillingSystem:
    def __init__(self):
        self._prices = {}  # plan id -> price per cycle, in the order added
        self._plans = {}  # customer -> current plan id, or None once cancelled
        self._charges = {}  # customer -> list of charges, oldest first

    def add_plan(self, plan_id, price):
        check_name(plan_id, "plan_id")
        check_price(price)
        if plan_id in self._prices:
            raise BillingError(f"plan {plan_id!r} already exists")
        self._prices[plan_id] = price

    def subscribe(self, customer, plan_id):
        check_name(customer, "customer")
        self._require_plan(plan_id)
        if self._plans.get(customer) is not None:
            raise BillingError(f"{customer!r} is already subscribed")
        self._plans[customer] = plan_id
        self._charges.setdefault(customer, [])

    def change_plan(self, customer, plan_id):
        self._require_customer(customer)
        self._require_plan(plan_id)
        current = self._require_subscribed(customer)
        if plan_id == current:
            raise BillingError(f"{customer!r} is already on {plan_id!r}")
        difference = self._prices[plan_id] - self._prices[current]
        if difference >= 0:
            self._charges[customer].append(difference)
        self._plans[customer] = plan_id

    def cancel(self, customer):
        self._require_customer(customer)
        self._require_subscribed(customer)
        self._plans[customer] = None

    def run_cycle(self):
        total = 0
        for customer, plan_id in self._plans.items():
            if plan_id is not None:
                price = self._prices[plan_id]
                self._charges[customer].append(price)
                total += price
        return total

    def get_plan(self, customer):
        self._require_customer(customer)
        return self._plans[customer]

    def get_charges(self, customer):
        self._require_customer(customer)
        return list(self._charges[customer])

    def _require_plan(self, plan_id):
        # Non-str ids are never stored, so they count as "never added" too.
        if not isinstance(plan_id, str) or plan_id not in self._prices:
            raise KeyError(plan_id)

    def _require_customer(self, customer):
        if not isinstance(customer, str) or customer not in self._plans:
            raise KeyError(customer)

    def _require_subscribed(self, customer):
        plan_id = self._plans[customer]
        if plan_id is None:
            raise BillingError(f"{customer!r} has cancelled")
        return plan_id
