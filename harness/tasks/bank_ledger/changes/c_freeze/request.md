Let accounts in `ledger.py` be frozen, for example while a suspicious
payment is being checked.

- Add `Ledger.freeze(account_id)`, `Ledger.unfreeze(account_id)` and
  `Ledger.is_frozen(account_id) -> bool`. All three raise `KeyError` for an
  account that is not open. New accounts are not frozen. Freezing a frozen
  account, or unfreezing one that is not frozen, does nothing.
- Add `class AccountFrozen(LedgerError)` to `ledger.py`.
- While an account is frozen, withdrawing from it, transferring from it and
  transferring to it raise `AccountFrozen` and change nothing. Deposits into
  a frozen account still work.
- When such a call also has another problem (an account that is not open,
  an invalid amount, a transfer to the same account, or too little money),
  which error is raised is unspecified.
- Freezing and unfreezing add nothing to the history.

All existing behavior must keep working.
