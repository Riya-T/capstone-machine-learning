# Restaurant orders

Write a module `orders.py` that keeps a restaurant's menu, the tables that
are currently open, what each table has ordered and what it owes.

## Interface

```python
class RestaurantError(Exception): ...


class Restaurant:
    def __init__(self): ...
    def add_dish(self, name: str, price: int) -> None: ...
    def open_table(self, table: str) -> None: ...
    def order(self, table: str, dish: str, quantity: int) -> None: ...
    def get_order(self, table: str) -> list[tuple[str, int]]: ...
    def get_bill(self, table: str) -> int: ...
    def close_table(self, table: str) -> None: ...
    def get_open_tables(self) -> list[str]: ...
```

All prices and bills are whole cents, as `int`.

## Menu

- `add_dish(name, price)` puts a dish on the menu. The name must be a
  non-empty string and the price an `int` greater than 0, or `ValueError`
  is raised. A name that is already on the menu raises `RestaurantError`
  and the menu is unchanged. Both `ValueError` checks come before the
  duplicate check.
- Dishes are never removed and prices never change.

## Tables

- `open_table(table)` opens a table with nothing ordered. An empty name
  raises `ValueError`; a table that is already open raises
  `RestaurantError`.
- `close_table(table)` closes an open table. A table may be closed with
  nothing ordered. Once closed, the table is not open: it may later be
  opened again with `open_table`, and it then starts with nothing ordered.
- `get_open_tables()` returns the open tables in the order they were
  opened. A table that is closed and opened again goes to the end.
- `order`, `get_order`, `get_bill` and `close_table` raise `KeyError` for a
  table that is not open, including values that are not strings at all,
  such as `None` or `1`.

## Orders

- `order(table, dish, quantity)` adds `quantity` of `dish` to the table's
  order. The dish must be on the menu, or `KeyError` is raised. The
  quantity must be an `int` greater than 0, or `ValueError` is raised.
- `get_order(table)` returns what the table has ordered since it was
  opened as `(dish, quantity)` tuples: one tuple per dish, with the
  quantities of repeated orders of the same dish added together, in the
  order the dishes were first ordered at that table. A table with nothing
  ordered gives `[]`.
- `get_bill(table)` returns the sum of quantity times price over the
  table's order, 0 for a table with nothing ordered.

When a call has several problems, the first of these is raised:

1. `KeyError` for a table that is not open or a dish that is not on the
   menu (either may be reported first when both apply);
2. `ValueError` for an invalid quantity.

A failed call has no effect: if a method raises, the menu, the open tables
and every order are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes names that are not strings passed to `add_dish` or `open_table`,
`bool` prices and quantities, what happens if a returned list is changed,
the text of error messages, saving the restaurant to a file, and use from
several threads.
