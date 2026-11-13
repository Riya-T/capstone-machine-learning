Add Wallet.revise(op_id, amount) -> None. Replace the amount of an
existing operation in place, retaining its member, ID, kind and position
in history. A malformed ID or invalid amount raises ValueError. IDs
must be nonempty strings. Amounts must be positive integers and may not
be booleans. An unknown valid operation ID raises KeyError.

If replaying that member's full history with the new amount would ever
produce a negative balance, raise ValueError. Apply this rule even
when the final balance would be nonnegative. Every failed call leaves
all state unchanged. On success subsequent posts use the revised
balance and the ID stays reserved. Existing behavior still applies.

For example, starting with credit 10, debit 8, credit 5, reducing the
first credit to 7 raises ValueError because the second operation would
overdraw. Increasing it to 12 succeeds and the final balance becomes 9.
