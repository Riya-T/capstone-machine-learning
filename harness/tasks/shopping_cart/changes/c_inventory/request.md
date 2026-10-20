Add optional stock limits to `ShoppingCart`.

- `ShoppingCart(stock_inventory=None)` accepts a mapping from item id to the
  maximum quantity that can be added to the cart. An item missing from the
  mapping has no stock limit.
- Adding an item must raise `ValueError` if its resulting cart quantity would
  exceed that item's stock. The cart must be unchanged on failure.
- Existing positive-quantity and non-negative-price validation still applies.
- Removing items does not modify the configured stock.

All existing behavior must keep working.
