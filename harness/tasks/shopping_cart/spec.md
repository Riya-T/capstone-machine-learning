# Shopping cart

Write a module `cart.py` that lets a shopper manage item quantities and
calculate the cost of the cart.

## Interface

```python
class ShoppingCart:
    def __init__(self): ...
    def add_item(
        self, item_id: str, name: str, price: float, quantity: int = 1
    ) -> None: ...
    def remove_item(self, item_id: str, quantity: int = 1) -> None: ...
    def get_total(self) -> float: ...
```

## Items

- Adding an item with a new id stores its name, price, and quantity.
- Adding an existing id increases its quantity. The original name and price
  remain in effect.
- Price must be non-negative and quantity must be an `int` greater than 0;
  anything else (such as `0`, `1.5` or `"2"`) is invalid. Invalid additions
  raise `ValueError` and leave the cart unchanged.
- Removing an item decreases its quantity. If the requested quantity is at
  least the quantity in the cart, the item is removed entirely.
- Removing an unknown id does nothing. The quantity follows the same rule
  as for adding (an `int` greater than 0); an invalid quantity raises
  `ValueError` and leaves the cart unchanged.

## Total

`get_total()` returns the sum of `price * quantity` for every item. An empty
cart has a total of `0.0`.

## Unspecified behavior

Behavior not described here is unspecified. This includes whether callers may
modify the public item data, the precision and rounding of floating-point
prices, validation of identifiers and names, and thread safety.
