# Seating chart

Write a module `seating.py` that keeps the seating chart of a dinner: which
guests sit at which table, and in what order they sit around it.

## Interface

```python
class SeatingError(Exception): ...


class SeatingChart:
    def __init__(self): ...
    def add_table(self, name: str) -> None: ...
    def seat(self, guest: str, table: str) -> None: ...
    def unseat(self, guest: str) -> None: ...
    def move_guest(self, guest: str, table: str) -> None: ...
    def merge_tables(self, table: str, into_table: str) -> int: ...
    def clear_table(self, table: str) -> int: ...
    def get_guests(self, table: str) -> list[str]: ...
    def get_tables(self) -> list[str]: ...
```

Table names and guest names are non-empty strings.

## Tables

- `add_table(name)` adds an empty table. A name that is already in use
  raises `SeatingError`.
- `get_tables()` returns the names of the tables in use, in the order they
  were added.
- Every method that takes a table raises `KeyError` when given a table
  that is not in use: one that was never added, or one that was removed by
  `merge_tables` or `clear_table`.

## Guests

- A guest sits at no more than one table at a time.
- `seat(guest, table)` seats the guest at the table, after the guests
  already there. Seating a guest who is already seated, at this table or
  at any other one, raises `SeatingError`.
- `unseat(guest)` takes the guest off the chart. Unseating a guest who is
  not seated raises `KeyError`.
- `move_guest(guest, table)` moves a seated guest to `table`, after the
  guests already there. A guest who is not seated raises `KeyError`, and
  moving a guest to the table they already sit at raises `ValueError`.
- `merge_tables(table, into_table)` moves every guest at `table` to
  `into_table`, after the guests already there and keeping their order,
  then removes `table`: it is no longer listed by `get_tables()`, and every
  method treats it as not in use. It returns how many guests it moved.
  Both tables being the same raises `ValueError`.
- `clear_table(table)` removes the table together with every guest at it,
  and returns how many guests there were. The table is no longer listed by
  `get_tables()`, and every method treats it as not in use.
- After `merge_tables` or `clear_table` the removed table's name is free:
  `add_table` may add it again later, as a new empty table listed last.
- `get_guests(table)` returns the guests at the table in seating order:
  the order in which they were seated at it or moved to it. When a guest
  leaves a table, the others keep their order.

Python notes: `guest in d.values()` compares the guest with each value as
a whole; when the values are lists of guests it does not look inside them,
so it cannot tell whether a guest sits at some table. A loop that removes
items from the list it is walking over skips items; loop over a copy such
as `list(guests)` instead. `seat` rejects guests who are already seated, so
code that moves seated guests cannot simply call `seat` for them.

## Errors

A failed call has no effect: if a method raises, every table's guests and
the list of tables are unchanged.

When a call has more than one problem (for example a guest who is not
seated and a table that is not in use), which of the errors is raised is
unspecified.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it.
This includes table or guest names that are not non-empty strings (such as
`""`, `None` or `1`), wherever they are passed, and what happens to the
guests of a removed table after `clear_table` (for example whether they
may be seated again). It also includes which error is raised when a call
has more than one problem, what happens if a returned list is changed, the
text of error messages, saving the chart to a file, and use from several
threads.
