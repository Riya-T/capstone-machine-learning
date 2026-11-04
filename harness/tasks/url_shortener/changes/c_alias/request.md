Tighten the rules for codes in `shortener.py`.

- A code passed to `add_link` must be 1 to 32 characters long and contain
  only ASCII letters, digits, `-` and `_`. Any other string raises
  `ValueError`, and an empty string or `None` still raises `ValueError` as
  before.
- Codes match without regard to case. After `add_link("Sale", ...)`, adding
  `"sale"` or `"SALE"` raises `ShortenerError` as a duplicate, and
  `visit("sale")`, `get_target("SALE")`, `get_hits`, `set_target` and every
  other method that takes a code find the same link. `get_codes` and
  `get_most_visited` return each code spelled as it was added.
- Those methods still raise `KeyError` for a code that does not exist,
  including values that are not strings at all, such as `None` or `1`:
  they count as unknown codes, so `visit(None)` and `get_target(1)` raise
  `KeyError`, not `ValueError`, as before.
- Add `class ReservedCode(ShortenerError)` to `shortener.py`.
- `Shortener` takes a new keyword argument `reserved=()`: codes that may
  never be added, such as `("admin", "login")`. Each entry must be a valid
  code by the rules above, or `Shortener(...)` raises `ValueError`; that
  includes an empty string and `None`, so `Shortener(reserved=("admin",
  None))` raises `ValueError`, not `TypeError`. Adding a reserved code, in
  any mix of upper and lower case, raises `ReservedCode`.
  Reserved codes do not appear in `get_codes`.

Which error `add_link` raises when one call has several of these problems
(for example a reserved code with an empty target) is unspecified. All
existing behavior must keep working.
