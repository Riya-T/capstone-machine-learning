"""Subscription billing with an adjustable upgrade share, paused
subscriptions and versioned subscriptions.

Planted bug (after c_proration, c_pause and c_plan_version): versions work,
but billing cycles charge paused customers again.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from billing import BillingSystem
    billing = BillingSystem(upgrade_percent=50)
    billing.add_plan("basic", 900)
    billing.add_plan("pro", 1500, upgrade_percent=25)
    billing.subscribe("alice", "basic")
    billing.change_plan("alice", "pro")
"""


class BillingError(Exception):
    pass


class SubscriptionPaused(BillingError):
    pass


class VersionConflict(BillingError):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str")


def check_price(price):
    if isinstance(price, bool) or not isinstance(price, int) or price <= 0:
        raise ValueError(f"price must be a positive int, got {price!r}")


def check_percent(percent):
    if isinstance(percent, bool) or not isinstance(percent, int) or not 0 <= percent <= 100:
        raise ValueError(f"upgrade_percent must be an int from 0 to 100, got {percent!r}")


class BillingSystem:
    def __init__(self, upgrade_percent=100):
        check_percent(upgrade_percent)
        self._default_percent = upgrade_percent
        self._prices = {}  # plan id -> price per cycle, in the order added
        self._percents = {}  # plan id -> upgrade percentage for moves to it
        self._plans = {}  # customer -> current plan id, or None once cancelled
        self._charges = {}  # customer -> list of charges, oldest first
        self._paused = set()  # customers whose subscription is paused
        self._versions = {}  # customer -> version of their current subscription

    def add_plan(self, plan_id, price, upgrade_percent=None):
        check_name(plan_id, "plan_id")
        check_price(price)
        if upgrade_percent is None:
            upgrade_percent = self._default_percent
        check_percent(upgrade_percent)
        if plan_id in self._prices:
            raise BillingError(f"plan {plan_id!r} already exists")
        self._prices[plan_id] = price
        self._percents[plan_id] = upgrade_percent

    def subscribe(self, customer, plan_id):
        check_name(customer, "customer")
        self._require_plan(plan_id)
        if self._plans.get(customer) is not None:
            raise BillingError(f"{customer!r} is already subscribed")
        self._plans[customer] = plan_id
        self._charges.setdefault(customer, [])
        self._versions[customer] = 1

    def change_plan(self, customer, plan_id, expected_version=None):
        self._require_customer(customer)
        self._require_plan(plan_id)
        self._require_subscribed(customer)
        self._check_version(customer, expected_version)
        charge = self.get_upgrade_charge(customer, plan_id)
        if charge > 0:
            self._charges[customer].append(charge)
        self._plans[customer] = plan_id
        self._versions[customer] += 1

    def get_upgrade_charge(self, customer, plan_id):
        self._require_customer(customer)
        self._require_plan(plan_id)
        current = self._require_subscribed(customer)
        self._require_not_paused(customer)
        if plan_id == current:
            raise BillingError(f"{customer!r} is already on {plan_id!r}")
        difference = self._prices[plan_id] - self._prices[current]
        if difference <= 0:
            return 0
        return difference * self._percents[plan_id] // 100

    def get_upgrade_percent(self, plan_id):
        self._require_plan(plan_id)
        return self._percents[plan_id]

    def cancel(self, customer, expected_version=None):
        self._require_customer(customer)
        self._require_subscribed(customer)
        self._check_version(customer, expected_version)
        self._plans[customer] = None
        self._paused.discard(customer)

    def pause(self, customer, expected_version=None):
        self._require_customer(customer)
        self._require_subscribed(customer)
        self._check_version(customer, expected_version)
        self._require_not_paused(customer)
        self._paused.add(customer)
        self._versions[customer] += 1

    def resume(self, customer, expected_version=None):
        self._require_customer(customer)
        self._require_subscribed(customer)
        self._check_version(customer, expected_version)
        if customer not in self._paused:
            raise BillingError(f"{customer!r} is not paused")
        self._paused.discard(customer)
        self._versions[customer] += 1

    def is_paused(self, customer):
        self._require_customer(customer)
        return customer in self._paused

    def run_cycle(self):
        total = 0
        for customer, plan_id in self._plans.items():
            if plan_id is not None:
                price = self._prices[plan_id]
                self._charges[customer].append(price)
                total += price
        return total

    def get_version(self, customer):
        self._require_customer(customer)
        self._require_subscribed(customer)
        return self._versions[customer]

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

    def _check_version(self, customer, expected_version):
        current = self._versions[customer]
        if expected_version is not None and expected_version != current:
            raise VersionConflict(
                f"{customer!r} is at version {current}, not {expected_version!r}"
            )

    def _require_not_paused(self, customer):
        if customer in self._paused:
            raise SubscriptionPaused(f"{customer!r} is paused")
