# Vending machine

Write a module `vending.py` that keeps track of one vending machine: the
slots it has, how many items each slot holds, and the coins a customer has
put in.

## Interface

```python
class VendingError(Exception): ...


class SoldOut(VendingError): ...


class NotEnoughCredit(VendingError): ...


class VendingMachine:
    def __init__(self): ...
    def add_slot(self, slot_id: str, price: int) -> None: ...
    def restock(self, slot_id: str, count: int) -> None: ...
    def insert_coins(self, amount: int) -> None: ...
    def buy(self, slot_id: str) -> None: ...
    def take_change(self) -> int: ...
    def get_credit(self) -> int: ...
    def get_stock(self, slot_id: str) -> int: ...
    def get_slots(self) -> list[str]: ...
```

All prices and coin amounts are whole cents, as `int`.

## Slots

- `add_slot(slot_id, price)` adds a slot that sells one kind of item at the
  given price. The slot starts with 0 items. An empty id raises `ValueError`.
  The price must be an `int` greater than 0, or `ValueError` is raised. An
  id that already exists raises `VendingError`; this is checked after the
  price.
- `get_slots()` returns the ids of all slots, in the order they were added.
- `restock(slot_id, count)` puts `count` more items into the slot. The count
  must be an `int` greater than 0, or `ValueError` is raised.
- `get_stock(slot_id)` returns the number of items in the slot.
- Every method that takes a slot id raises `KeyError` when the slot does not
  exist, including values that are not strings at all, such as `None` or
  `1`. This is checked before anything else.

## Coins and buying

- `insert_coins(amount)` adds the amount to the customer's credit. The
  amount must be an `int` greater than 0, or `ValueError` is raised.
- `get_credit()` returns the credit not yet spent.
- `buy(slot_id)` takes one item out of the slot and takes the slot's price
  out of the credit. The rest of the credit stays in the machine. A slot
  with 0 items raises `SoldOut`. A credit smaller than the price raises
  `NotEnoughCredit`.
- `take_change()` returns the whole remaining credit and sets it to 0. With
  no credit it returns 0.

When a call has several problems, the first of these is raised:

1. `KeyError` for a slot that does not exist;
2. `ValueError` for an invalid count, price or amount;
3. `SoldOut`;
4. `NotEnoughCredit`.

A failed call has no effect: if a method raises, every stock count and the
credit are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes ids that are not strings passed to `add_slot`, `bool` prices,
counts or amounts, what happens if a returned list is changed, the text of
error messages, saving the machine to a file, and use from several threads.
