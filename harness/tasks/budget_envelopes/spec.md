# Budget envelopes

Write a module `envelopes.py` that keeps a household budget: income arrives
as unassigned money, gets put into named envelopes, and is spent from them.

## Interface

```python
class BudgetError(Exception): ...


class NotEnoughMoney(BudgetError): ...


class Budget:
    def __init__(self): ...
    def add_envelope(self, name: str) -> None: ...
    def add_income(self, amount: int) -> None: ...
    def allocate(self, name: str, amount: int) -> None: ...
    def spend(self, name: str, amount: int) -> None: ...
    def get_balance(self, name: str) -> int: ...
    def get_unassigned(self) -> int: ...
    def get_envelopes(self) -> list[str]: ...
```

All amounts are whole cents, as `int`.

## Envelopes

- `add_envelope(name)` creates an envelope holding 0. An empty name raises
  `ValueError`, and a name that already exists raises `BudgetError`.
- `get_envelopes()` returns the names of all envelopes, in the order they
  were created.
- Every method that takes an envelope name raises `KeyError` when no
  envelope has that name, including values that are not strings at all,
  such as `None` or `1`.

## Money

- An amount must be an `int` greater than 0, or `ValueError` is raised.
- `add_income(amount)` adds the amount to the unassigned money. A new budget
  has 0 unassigned.
- `allocate(name, amount)` moves the amount from the unassigned money into
  the envelope. Allocating more than is unassigned raises `NotEnoughMoney`.
- `spend(name, amount)` takes the amount out of the envelope. Spending more
  than the envelope holds raises `NotEnoughMoney`. Spending does not touch
  the unassigned money.
- `get_balance(name)` returns what the envelope currently holds.
  `get_unassigned()` returns the unassigned money. Neither is ever below 0.

When a call has several problems, the first of these is raised:

1. `KeyError` for an envelope that does not exist;
2. `ValueError` for an invalid amount;
3. `NotEnoughMoney`.

A failed call has no effect: if a method raises, every balance and the
unassigned money are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes names that are not strings passed to `add_envelope`, `bool`
amounts, what happens if a returned list is changed, the text of error
messages, saving the budget to a file, and use from several threads.
