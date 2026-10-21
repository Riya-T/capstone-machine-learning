"""Budget envelopes where envelopes can be locked, with moves between
envelopes and all-or-nothing multi-envelope allocation.

Planted bug (after c_lock and c_move): moves were added correctly and
respect locks, but while reworking the funds checks the lock check in
spend was dropped, so a locked envelope can be spent from. Never shown to
the writer or the editor; validate-tasks checks that the tests catch it.

Usage:
    from envelopes import Budget
    budget = Budget()
    budget.add_envelope("rent")
    budget.add_envelope("food")
    budget.add_income(50000)
    budget.allocate_many({"rent": 45000, "food": 5000})
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
        self._require_unassigned(amount)
        self._unassigned -= amount
        self._balances[name] += amount

    def allocate_many(self, amounts):
        # Check everything first so a failure half-way cannot happen.
        for name in amounts:
            self._require(name)
        for amount in amounts.values():
            check_amount(amount)
        for name in amounts:
            self._require_unlocked(name)
        self._require_unassigned(sum(amounts.values()))
        for name, amount in amounts.items():
            self._unassigned -= amount
            self._balances[name] += amount

    def spend(self, name, amount):
        self._require(name)
        check_amount(amount)
        self._require_funds(name, amount)
        self._balances[name] -= amount

    def move(self, from_name, to_name, amount):
        self._require(from_name)
        self._require(to_name)
        check_amount(amount)
        if from_name == to_name:
            raise ValueError("cannot move money into the same envelope")
        self._require_unlocked(from_name)
        self._require_unlocked(to_name)
        self._require_funds(from_name, amount)
        self._balances[from_name] -= amount
        self._balances[to_name] += amount

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

    def _require_unassigned(self, amount):
        if amount > self._unassigned:
            raise NotEnoughMoney(f"only {self._unassigned} unassigned, cannot allocate {amount}")

    def _require_funds(self, name, amount):
        if amount > self._balances[name]:
            raise NotEnoughMoney(f"envelope {name!r} cannot cover {amount}")
