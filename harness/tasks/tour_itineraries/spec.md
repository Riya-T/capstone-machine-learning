# Tour itineraries

Write a module `tours.py` that keeps track of the itineraries of a travel
agency's tours: which cities each tour visits, in what order, as cities are
added and removed, a city is cancelled on every tour, and tours are merged.

## Interface

```python
class TourError(Exception): ...


class TourPlanner:
    def __init__(self): ...
    def add_tour(self, name: str) -> None: ...
    def add_city(self, tour: str, city: str) -> None: ...
    def remove_city(self, tour: str, city: str) -> None: ...
    def cancel_city(self, city: str) -> int: ...
    def merge_tours(self, first: str, second: str) -> int: ...
    def get_cities(self, tour: str) -> list[str]: ...
    def get_tours(self) -> list[str]: ...
```

Tour names and city names are non-empty strings.

## Tours

- `add_tour(name)` adds a tour with no cities. A name that is already in
  use raises `TourError`.
- `get_tours()` returns the names of the tours in use, in the order they
  were added.
- Every other method that takes a tour name raises `KeyError` when that
  name is not in use: one that was never added, or one that was merged
  into another tour.

## Cities

- A tour visits its cities in order. A city is on a tour at most once, but
  the same city may be on several tours.
- `get_cities(tour)` returns the cities of the tour in order, first stop
  first. A new tour has none.
- `add_city(tour, city)` adds the city at the end of the tour. A city that
  is already on that tour raises `TourError`.
- `remove_city(tour, city)` removes the city from the tour. The other
  cities keep their order. A city that is not on that tour raises
  `TourError`.
- `cancel_city(city)` removes the city from every tour that has it. On
  each of those tours, the other cities keep their order. It returns how
  many tours it removed the city from. A city that is on no tour is not an
  error: nothing changes and it returns 0. Whether a tour that loses its
  last city this way stays is unspecified.

## Merging tours

- `merge_tours(first, second)` adds the cities of tour `second` at the end
  of tour `first`, in the order `second` visits them, skipping the cities
  that `first` already has. Then it removes tour `second`: it is removed
  from `get_tours()`, and every method treats it as not in use. It returns
  how many cities it added to `first`.
- The name of the merged tour is then free: `add_tour` may add it again
  later, as a new tour with no cities.
- `merge_tours` raises `ValueError` when `first` and `second` are the same.

## Errors

A failed call has no effect: if a method raises, the tours and every tour's
cities, in their order, are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes which error is raised when a call has more than one problem (for
example a tour that is not in use and the same tour twice), names that are
not non-empty strings (such as `""`, `None` or `1`), what happens if a
returned list is changed, the text of error messages, saving the tours to a
file, and use from several threads.
