# Warehouse stock

Write a module `warehouse.py` that keeps the stock of the products in a
warehouse, the deliveries that come in, and the orders that take stock out.

## Interface

```python
class WarehouseError(Exception): ...


class OutOfStock(WarehouseError): ...


class Warehouse:
    def __init__(self): ...
    def add_product(self, sku: str) -> None: ...
    def receive(self, sku: str, quantity: int) -> None: ...
    def place_order(self, sku: str, quantity: int) -> int: ...
    def get_stock(self, sku: str) -> int: ...
    def get_order(self, order_id: int) -> tuple[str, int]: ...
    def get_history(self, sku: str) -> list[tuple[str, int]]: ...
    def get_products(self) -> list[str]: ...
```

All quantities are whole units, as `int`.

## Products

- `add_product(sku)` adds a product with a stock of 0. An empty sku raises
  `ValueError`, and adding a sku that is already a product raises
  `WarehouseError`.
- `get_products()` returns the skus of all products, in the order they were
  added.
- `receive`, `place_order`, `get_stock` and `get_history` raise `KeyError`
  when given a sku that is not a product, including values that are not
  strings at all, such as `None` or `7`.

## Stock

- A quantity must be an `int` greater than 0, or `ValueError` is raised.
- `receive(sku, quantity)` adds the quantity to the product's stock.
- `place_order(sku, quantity)` takes the quantity out of the product's stock
  and returns the order's id. The first successful order gets id 1, the next
  one id 2, and so on; a failed call uses up no id.
- Stock never goes below 0: an order for more than the stock raises
  `OutOfStock`. An order for exactly the stock is fine and leaves 0.
- `get_stock(sku)` returns the product's current stock.
- `get_order(order_id)` returns the order's `(sku, quantity)`. It raises
  `KeyError` for an id that is not an order id, including values such as
  `None` or `"1"`.

When a call to `receive` or `place_order` has several problems, the first of
these is raised:

1. `KeyError` for a sku that is not a product;
2. `ValueError` for an invalid quantity;
3. `OutOfStock`.

## History

`get_history(sku)` returns the product's stock movements, oldest first, as
`(kind, quantity)` tuples with a positive quantity:

- `("received", quantity)` for a delivery;
- `("ordered", quantity)` for an order.

A failed call has no effect: if a method raises, every stock, order and
history is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes skus that are not strings passed to `add_product`, `bool`
quantities, what happens if a returned list is changed, the text of error
messages, saving the warehouse to a file, and use from several threads.
