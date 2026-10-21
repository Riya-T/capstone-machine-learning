Let a customer reserve several products at once in `warehouse.py`, so a
bundle is either taken from stock completely or not at all.

- Add `Warehouse.place_bundle(lines) -> list[int]`, where `lines` is a list
  of `(sku, quantity)` pairs. Every line is checked before anything changes;
  if any check fails, no stock, order or history changes. The checks, in
  order:
  1. `ValueError` if `lines` is empty;
  2. `KeyError` for the first sku (in line order) that is not a product;
  3. `ValueError` for the first quantity (in line order) that is not an
     `int` greater than 0;
  4. `ValueError` if a sku appears in more than one line;
  5. `OutOfStock` if any line asks for more than its product's stock.
- When every check passes, each line becomes an order exactly as
  `place_order` would make it: stock goes down, the product's history gets
  an `("ordered", quantity)` entry, and the order gets the next unused id.
  The ids are given in line order and returned as a list, so
  `get_order(ids[i])` is `lines[i]`.
- Where orders can be returned, each order of a bundle can be returned on
  its own.

All existing behavior must keep working.
