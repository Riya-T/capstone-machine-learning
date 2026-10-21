Let orders in `warehouse.py` be returned, so the units come back into
stock.

- Add `Warehouse.return_order(order_id)`. It raises `KeyError` for an id
  that is not an order id, then `WarehouseError` if the order has already
  been returned. In each case nothing changes.
- A successful return adds the order's quantity back to its product's stock
  and appends `("returned", quantity)` to that product's history.
- Add `Warehouse.is_returned(order_id) -> bool`, which is `False` for a new
  order and `True` once it has been returned. It raises `KeyError` for an
  id that is not an order id.
- A returned order keeps its id, and `get_order` still returns its
  `(sku, quantity)`. Order ids are never reused.

All existing behavior must keep working.
