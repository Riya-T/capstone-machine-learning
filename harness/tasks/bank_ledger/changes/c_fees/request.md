Charge a fee on every withdrawal and every outgoing transfer in `ledger.py`.

- `Ledger` takes a new keyword argument `fee=0`: the fee in cents. It must
  be an `int` that is 0 or more (not a `bool`); anything else raises
  `ValueError`.
- Each successful `withdraw` and `transfer` also takes the fee from the
  account the money leaves. Deposits and incoming transfers are free.
- The account must be able to pay the amount and the fee together. If that
  would take its balance below the lowest balance it is allowed, raise
  `InsufficientFunds` and change nothing.
- When the fee is more than 0, the paying account's history gets a separate
  `("fee", fee)` entry straight after its `("withdrawal", amount)` or
  `("transfer_out", amount)` entry. A fee of 0 adds no entry.
- Add `Ledger.get_total_fees() -> int`: the sum of every fee charged so far,
  over all accounts.

All existing behavior must keep working.
