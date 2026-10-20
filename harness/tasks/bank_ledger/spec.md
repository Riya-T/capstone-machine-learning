# Bank ledger

Write a module `ledger.py` that keeps the balances of bank accounts and a
history of every movement of money.

## Interface

```python
class LedgerError(Exception): ...


class InsufficientFunds(LedgerError): ...


class Ledger:
    def __init__(self): ...
    def open_account(self, account_id: str) -> None: ...
    def deposit(self, account_id: str, amount: int) -> None: ...
    def withdraw(self, account_id: str, amount: int) -> None: ...
    def transfer(self, from_id: str, to_id: str, amount: int) -> None: ...
    def get_balance(self, account_id: str) -> int: ...
    def get_history(self, account_id: str) -> list[tuple[str, int]]: ...
    def get_accounts(self) -> list[str]: ...
```

All amounts are whole cents, as `int`.

## Accounts

- `open_account(account_id)` opens an account with a balance of 0. An empty
  id raises `ValueError`, and opening an id that is already open raises
  `LedgerError`.
- `get_accounts()` returns the ids of all open accounts, in the order they were
  opened.
- Every other method raises `KeyError` when given an account id that is not
  open, including values that are not strings at all, such as `None` or `1`.

## Moving money

- An amount must be an `int` greater than 0, or `ValueError` is raised.
- `deposit` adds the amount to the account. `withdraw` takes it out.
  `transfer` moves it from `from_id` to `to_id`; transferring to the same
  account raises `ValueError`.
- A balance never goes below 0: a `withdraw` or `transfer` of more than the
  balance raises `InsufficientFunds`.
- `get_balance(account_id)` returns the current balance.

When a call has several problems, the first of these is raised:

1. `KeyError` for an account that is not open (for `transfer`, `from_id`
   is checked before `to_id`);
2. `ValueError` for an invalid amount;
3. `ValueError` for a transfer to the same account;
4. `InsufficientFunds`.

## History

`get_history(account_id)` returns the account's movements, oldest first, as
`(kind, amount)` tuples with a positive amount:

- `("deposit", amount)` for a deposit;
- `("withdrawal", amount)` for a withdrawal;
- `("transfer_out", amount)` on the sending account and
  `("transfer_in", amount)` on the receiving account for a transfer.

A failed call has no effect: if a method raises, every balance and every
history is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes ids that are not strings passed to `open_account`, `bool` amounts,
what happens if a returned list is changed, the text of error messages, saving the ledger to a file, and use
from several threads.
