"""Compare the two published Wallet starts over small, deterministic operation traces."""

from __future__ import annotations

from itertools import product

from ledger import Wallet as LedgerWallet
from materialized import Wallet as StoredBalanceWallet

MEMBERS = ("a", "b")
OPERATIONS = (
    ("p", "a", "credit", 3),
    ("q", "a", "debit", 2),
    ("r", "b", "credit", 2),
    ("s", "b", "debit", 1),
    ("p", "b", "credit", 1),
    ("t", "b", "debit", True),
    ("u", "missing", "credit", 2),
    ("v", "b", "adjustment", 1),
)


def contract_result(operation, balances, histories, used_ids):
    """Apply the public contract to plain observable state."""
    operation_id, member, kind, amount = operation
    if member not in balances:
        return KeyError
    if kind not in ("credit", "debit") or type(amount) is not int or amount <= 0:
        return ValueError
    if operation_id in used_ids:
        return ValueError
    delta = amount if kind == "credit" else -amount
    if balances[member] + delta < 0:
        return ValueError
    balances[member] += delta
    histories[member].append((operation_id, kind, amount))
    used_ids.add(operation_id)
    return None


def post_result(wallet, operation):
    try:
        result = wallet.post(*operation)
    except (KeyError, ValueError) as error:
        return type(error)
    if result is not None:
        raise AssertionError("post must return None")
    return None


def check_trace(trace):
    wallets = (LedgerWallet(), StoredBalanceWallet())
    balances = dict.fromkeys(MEMBERS, 0)
    histories = {member: [] for member in MEMBERS}
    used_ids = set()
    for wallet in wallets:
        for member in MEMBERS:
            wallet.open_member(member)
    for operation in trace:
        expected = contract_result(operation, balances, histories, used_ids)
        for wallet in wallets:
            if post_result(wallet, operation) != expected:
                raise AssertionError(
                    f"{type(wallet).__module__} returned the wrong outcome: {trace}"
                )
            for member in MEMBERS:
                if (wallet.balance(member), wallet.history(member)) != (
                    balances[member],
                    histories[member],
                ):
                    raise AssertionError(f"{type(wallet).__module__} state mismatch: {trace}")


def main():
    traces = tuple(product(OPERATIONS, repeat=3))
    for trace in traces:
        check_trace(trace)
    print(f"Both published Wallet starts matched the contract on {len(traces)} traces.")


if __name__ == "__main__":
    main()
