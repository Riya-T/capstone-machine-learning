"""An in-memory wallet backed by one posting ledger."""


class Wallet:
    def __init__(self):
        self._members = set()
        self._postings = {}

    @staticmethod
    def _identifier(value):
        if not isinstance(value, str) or not value:
            raise ValueError("expected a nonempty identifier")

    def _require_member(self, member):
        self._identifier(member)
        if member not in self._members:
            raise KeyError(member)

    def open_member(self, member):
        self._identifier(member)
        if member in self._members:
            raise ValueError("member already exists")
        self._members.add(member)

    def balance(self, member):
        self._require_member(member)
        return sum(
            amount if kind == "credit" else -amount
            for owner, kind, amount in self._postings.values()
            if owner == member
        )

    def post(self, op_id, member, kind, amount):
        self._identifier(op_id)
        self._require_member(member)
        if not isinstance(kind, str) or kind not in ("credit", "debit"):
            raise ValueError("invalid operation kind")
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("expected a positive integer amount")
        if op_id in self._postings:
            raise ValueError("operation already exists")
        if kind == "debit" and self.balance(member) < amount:
            raise ValueError("insufficient credits")
        self._postings[op_id] = (member, kind, amount)

    def history(self, member):
        self._require_member(member)
        return [
            (op_id, kind, amount)
            for op_id, (owner, kind, amount) in self._postings.items()
            if owner == member
        ]
