Add ways to look through the stock and the orders in `warehouse.py`.

- Add `Warehouse.get_low_stock(threshold) -> list[str]`: the skus of every
  product whose stock is strictly below `threshold`, in the order the
  products were added. `threshold` must be an `int` that is 0 or more (not
  a `bool`), or `ValueError` is raised; `get_low_stock(0)` is always `[]`.
- Add `Warehouse.get_orders(sku) -> list[int]`: the ids of every order for
  that product, in the order they were placed. It raises `KeyError` for a
  sku that is not a product. A product with no orders gives `[]`.
- Add `Warehouse.get_large_orders(min_quantity) -> list[int]`: the ids of
  every order, over all products, whose quantity is `min_quantity` or more,
  lowest id first. `min_quantity` must be an `int` greater than 0 (not a
  `bool`), or `ValueError` is raised.

All existing behavior must keep working.
