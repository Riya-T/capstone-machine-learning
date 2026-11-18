# Trail huts

Write a module `trails.py` that keeps the map of a mountain hut network:
the huts, and the trails that join pairs of huts.

## Interface

```python
class TrailError(Exception): ...


class TrailMap:
    def __init__(self): ...
    def add_hut(self, name: str) -> None: ...
    def add_trail(self, hut_a: str, hut_b: str) -> None: ...
    def remove_trail(self, hut_a: str, hut_b: str) -> None: ...
    def close_hut(self, hut: str) -> int: ...
    def merge_huts(self, hut: str, into_hut: str) -> None: ...
    def get_huts(self) -> list[str]: ...
    def get_neighbors(self, hut: str) -> list[str]: ...
```

Hut names are non-empty strings.

## Huts

- `add_hut(name)` adds a hut with no trails. A name that is already in use
  raises `TrailError`.
- `get_huts()` returns the names of the huts in use, in the order they were
  added.
- Every other method raises `KeyError` when given a hut that is not in
  use: one that was never added, or one that was closed or merged.

## Trails

- A trail joins two different huts, and works both ways: the trail added
  by `add_trail("A", "B")` is the same trail as `add_trail("B", "A")`. Two
  huts are joined by at most one trail.
- `add_trail(hut_a, hut_b)` adds a trail between the two huts. It raises
  `ValueError` when both huts are the same, and `TrailError` when the two
  huts are already joined.
- `remove_trail(hut_a, hut_b)` removes the trail between the two huts, in
  either order. It raises `TrailError` when the two huts are not joined.
- `get_neighbors(hut)` returns the huts joined to `hut` by a trail, in the
  order those trails were added. When a trail is removed, the other
  trails keep their order; a trail added again later counts as new and
  comes last.
- `close_hut(hut)` removes every trail of `hut`, then removes `hut` itself:
  it is no longer listed by `get_huts()`, and every method treats it as not
  in use. It returns how many trails it removed.
- `merge_huts(hut, into_hut)` hands every trail of `hut` over to
  `into_hut`: each trail between `hut` and another hut X, taken in the
  order of `get_neighbors(hut)`, is replaced by a new trail between
  `into_hut` and X. In `get_neighbors(X)`, `into_hut` then comes last, like
  any new trail. Then `hut` is removed the way `close_hut` removes it.
  `merge_huts` raises `ValueError` when both huts are the same.
- After a merge, `get_neighbors(into_hut)` lists the right huts, but their
  order is unspecified.
- After `close_hut` or `merge_huts` the removed hut's name is free:
  `add_hut` may add it again later, as a new hut with no trails, listed
  last.

Example: with huts A, B, C, D, and trails added in the order A-B, A-D, B-D,
`merge_huts("A", "C")` removes A, and the trails A-B and A-D become C-B and
C-D. Afterwards `get_neighbors("C")` lists B and D (in either order),
`get_neighbors("B")` is `["D", "C"]` and `get_neighbors("D")` is
`["B", "C"]`.

Python note: a loop that removes items from the list it is walking over
skips items (for example when removing a hut's trails one by one while
looping over its list of neighbors); loop over a copy such as
`list(neighbors)` instead.

## Errors

A failed call has no effect: if a method raises, the list of huts and
every hut's neighbors are unchanged.

When a call has more than one problem (for example a hut that is not in
use and both huts being the same), which of the errors is raised is
unspecified.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it.
This includes hut names that are not non-empty strings (such as `""`,
`None` or `1`), wherever they are passed, `remove_trail` with the same
hut on both sides, `merge_huts` of two huts that are joined by a trail or
are both joined to the same hut, and the order of `into_hut`'s neighbors
after a merge. It also includes which error is raised
when a call has more than one problem, what happens if a returned list is
changed, the text of error messages, saving the map to a file, and use
from several threads.
