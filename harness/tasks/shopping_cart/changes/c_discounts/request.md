Add coupon discounts to `ShoppingCart`.

- Add `apply_discount_code(code)`. The supported code `SAVE10` applies a
  10-percent discount to the cart total.
- Applying the same valid code again is allowed: it raises nothing, and the
  discount stays 10 percent (it does not compound).
- An unknown code raises `ValueError` and leaves the currently applied
  discount unchanged.
- `get_total()` returns the discounted total; item quantities and prices are
  not changed by applying a coupon.

All existing behavior must keep working.
