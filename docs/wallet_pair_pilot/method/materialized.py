"""An in-memory wallet with per-member balances and posting histories."""

from dataclasses import dataclass, field


@dataclass
class _Account:
    balance: int = 0
    postings: list[tuple[str, str, int]] = field(default_factory=list)


class Wallet:
    def __init__(self):
        self._accounts = {}
        self._operation_ids = set()

    @staticmethod
    def _identifier(value):
        if not isinstance(value, str) or not value:
            raise ValueError("expected a nonempty identifier")

    def _require_member(self, member):
        self._identifier(member)
        return self._accounts[member]

    def open_member(self, member):
        self._identifier(member)
        if member in self._accounts:
            raise ValueError("member already exists")
        self._accounts[member] = _Account()

    def balance(self, member):
        return self._require_member(member).balance

    def post(self, op_id, member, kind, amount):
        self._identifier(op_id)
        account = self._require_member(member)
        if not isinstance(kind, str) or kind not in ("credit", "debit"):
            raise ValueError("invalid operation kind")
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("expected a positive integer amount")
        if op_id in self._operation_ids:
            raise ValueError("operation already exists")
        if kind == "debit" and account.balance < amount:
            raise ValueError("insufficient credits")
        account.balance += amount if kind == "credit" else -amount
        account.postings.append((op_id, kind, amount))
        self._operation_ids.add(op_id)

    def history(self, member):
        return list(self._require_member(member).postings)
