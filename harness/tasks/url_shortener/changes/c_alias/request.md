Tighten the rules for codes in `shortener.py`.

- A code passed to `add_link` must be 1 to 32 characters long and contain
  only ASCII letters, digits, `-` and `_`. Anything else raises
  `ValueError`, like an empty code did before.
- Codes match without regard to case. After `add_link("Sale", ...)`, adding
  `"sale"` or `"SALE"` raises `ShortenerError` as a duplicate, and
  `visit("sale")`, `get_target("SALE")`, `get_hits`, `set_target` and every
  other method that takes a code find the same link. `get_codes` and
  `get_most_visited` return each code spelled as it was added.
- Add `class ReservedCode(ShortenerError)` to `shortener.py`.
- `Shortener` takes a new keyword argument `reserved=()`: codes that may
  never be added, such as `("admin", "login")`. Each entry must be a valid
  code by the rules above, or `Shortener(...)` raises `ValueError`. Adding a
  reserved code, in any mix of upper and lower case, raises `ReservedCode`.
  Reserved codes do not appear in `get_codes`.

In `add_link`, errors are raised in this order: `ValueError` for the code,
`ValueError` for the target, `ReservedCode`, then `ShortenerError` for a
duplicate. All existing behavior must keep working.
