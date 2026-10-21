# URL shortener

Write a module `shortener.py` that keeps short codes, the web addresses they
point to, and how often each code has been visited.

## Interface

```python
class ShortenerError(Exception): ...


class Shortener:
    def __init__(self): ...
    def add_link(self, code: str, target: str) -> None: ...
    def visit(self, code: str) -> str: ...
    def set_target(self, code: str, target: str) -> None: ...
    def get_target(self, code: str) -> str: ...
    def get_hits(self, code: str) -> int: ...
    def get_codes(self) -> list[str]: ...
    def get_most_visited(self) -> list[str]: ...
```

## Links

- `add_link(code, target)` adds a link from `code` to `target`. The code and
  the target must both be non-empty strings, or `ValueError` is raised.
  Adding a code that already exists raises `ShortenerError`.
- `get_codes()` returns every code, in the order the links were added.
- `get_target(code)` returns the address the code currently points to.
- `set_target(code, target)` makes the code point to a different address.
  The target must be a non-empty string, or `ValueError` is raised. The
  code's hits are kept.
- Every method that takes an existing code raises `KeyError` when the code
  does not exist, including values that are not strings at all, such as
  `None` or `1`.

## Visits

- `visit(code)` records one hit on the code and returns the address it points
  to at that moment.
- `get_hits(code)` returns how many times the code has been visited. A new
  link has 0 hits.
- `get_most_visited()` returns every code, the most visited first. Codes
  with the same number of hits keep the order in which they were added.
  Codes with no hits are included.

When a call has several problems, the first of these is raised:

1. `KeyError` for a code that does not exist;
2. `ValueError` for an invalid code passed to `add_link`;
3. `ValueError` for an invalid target;
4. `ShortenerError` for a code that already exists.

A failed call has no effect: if a method raises, every target and every hit
count is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes whether a target looks like a real web address, what happens if a
returned list is changed, the text of error messages, saving the links to a
file, and use from several threads.
