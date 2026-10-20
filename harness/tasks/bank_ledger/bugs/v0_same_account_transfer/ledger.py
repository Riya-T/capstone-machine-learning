"""Bank ledger: account balances and a history of every movement of money.

Planted bug (initial version): a transfer to the same account is allowed.
The public checks never try one, so only the hidden initial tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from ledger import Ledger
    ledger = Ledger()
    ledger.open_account("alice")
    ledger.deposit("alice", 500)
"""


class LedgerError(Exception):
    pass


class InsufficientFunds(LedgerError):
    pass


def check_amount(amount):
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise ValueError(f"amount must be a positive int, got {amount!r}")


class Ledger:
    def __init__(self):
        self._balances = {}  # account id -> balance in cents, in opening order
        self._history = {}  # account id -> list of (kind, amount)

    def open_account(self, account_id):
        if not isinstance(account_id, str) or not account_id:
            raise ValueError("account_id must be a non-empty str")
        if account_id in self._balances:
            raise LedgerError(f"account {account_id!r} is already open")
        self._balances[account_id] = 0
        self._history[account_id] = []

    def deposit(self, account_id, amount):
        self._require(account_id)
        check_amount(amount)
        self._balances[account_id] += amount
        self._history[account_id].append(("deposit", amount))

    def withdraw(self, account_id, amount):
        self._require(account_id)
        check_amount(amount)
        self._require_funds(account_id, amount)
        self._balances[account_id] -= amount
        self._history[account_id].append(("withdrawal", amount))

    def transfer(self, from_id, to_id, amount):
        self._require(from_id)
        self._require(to_id)
        check_amount(amount)
        self._require_funds(from_id, amount)
        self._balances[from_id] -= amount
        self._balances[to_id] += amount
        self._history[from_id].append(("transfer_out", amount))
        self._history[to_id].append(("transfer_in", amount))

    def get_balance(self, account_id):
        self._require(account_id)
        return self._balances[account_id]

    def get_history(self, account_id):
        self._require(account_id)
        return list(self._history[account_id])

    def get_accounts(self):
        return list(self._balances)

    def _require(self, account_id):
        # Non-str ids are never stored, so they count as "not open" too.
        if not isinstance(account_id, str) or account_id not in self._balances:
            raise KeyError(account_id)

    def _require_funds(self, account_id, amount):
        if self._balances[account_id] - amount < 0:
            raise InsufficientFunds(f"account {account_id!r} cannot cover {amount}")
