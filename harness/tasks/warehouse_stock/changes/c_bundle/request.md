Let a customer reserve several products at once in `warehouse.py`, so a
bundle is either taken from stock completely or not at all.

- Add `Warehouse.place_bundle(lines) -> list[int]`, where `lines` is a list
  of `(sku, quantity)` pairs. Every line is checked before anything changes;
  if any check fails, no stock, order or history changes. The checks:
  - `ValueError` if `lines` is empty;
  - `KeyError` if a sku is not a product;
  - `ValueError` if a quantity is not an `int` greater than 0;
  - `ValueError` if a sku appears in more than one line;
  - `OutOfStock` if any line asks for more than its product's stock.

  Which error is raised when a bundle has several of these problems (for
  example an unknown sku in one line and a bad quantity in another) is
  unspecified.
- When every check passes, each line becomes an order exactly as
  `place_order` would make it: stock goes down, the product's history gets
  an `("ordered", quantity)` entry, and the order gets the next unused id.
  The ids are given in line order and returned as a list, so
  `get_order(ids[i])` is `lines[i]`.
- Where orders can be returned, each order of a bundle can be returned on
  its own.

All existing behavior must keep working.
