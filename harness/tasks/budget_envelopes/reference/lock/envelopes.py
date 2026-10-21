"""Budget envelopes where envelopes can be locked.

Correct solution for budget_envelopes after c_lock.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from envelopes import Budget
    budget = Budget()
    budget.add_envelope("rent")
    budget.add_income(50000)
    budget.allocate("rent", 45000)
    budget.lock("rent")
"""


class BudgetError(Exception):
    pass


class NotEnoughMoney(BudgetError):
    pass


class EnvelopeLocked(BudgetError):
    pass


def check_amount(amount):
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise ValueError(f"amount must be a positive int, got {amount!r}")


class Budget:
    def __init__(self):
        self._unassigned = 0  # income not yet put into an envelope, in cents
        self._balances = {}  # envelope name -> cents held, in creation order
        self._locked = set()  # envelopes whose money may not change

    def add_envelope(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty str")
        if name in self._balances:
            raise BudgetError(f"envelope {name!r} already exists")
        self._balances[name] = 0

    def add_income(self, amount):
        check_amount(amount)
        self._unassigned += amount

    def allocate(self, name, amount):
        self._require(name)
        check_amount(amount)
        self._require_unlocked(name)
        if amount > self._unassigned:
            raise NotEnoughMoney(f"only {self._unassigned} unassigned, cannot allocate {amount}")
        self._unassigned -= amount
        self._balances[name] += amount

    def spend(self, name, amount):
        self._require(name)
        check_amount(amount)
        self._require_unlocked(name)
        if amount > self._balances[name]:
            raise NotEnoughMoney(f"envelope {name!r} cannot cover {amount}")
        self._balances[name] -= amount

    def get_balance(self, name):
        self._require(name)
        return self._balances[name]

    def get_unassigned(self):
        return self._unassigned

    def get_envelopes(self):
        return list(self._balances)

    def lock(self, name):
        self._require(name)
        self._locked.add(name)

    def unlock(self, name):
        self._require(name)
        self._locked.discard(name)

    def is_locked(self, name):
        self._require(name)
        return name in self._locked

    def _require(self, name):
        # Non-str names are never stored, so they count as missing too.
        if not isinstance(name, str) or name not in self._balances:
            raise KeyError(name)

    def _require_unlocked(self, name):
        if name in self._locked:
            raise EnvelopeLocked(f"envelope {name!r} is locked")
