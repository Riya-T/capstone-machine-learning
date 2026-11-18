# Bike docks

Write a module `bikes.py` that keeps track of a bike-share network: which
bikes are docked at which station, and in what order, as bikes are docked,
taken out and moved from one station to another.

## Interface

```python
class DockError(Exception): ...


class BikeNetwork:
    def __init__(self): ...
    def add_station(self, name: str) -> None: ...
    def dock(self, station: str, bike: str) -> None: ...
    def undock(self, bike: str) -> None: ...
    def rebalance(self, from_station: str, to_station: str, count: int) -> None: ...
    def close_station(self, name: str, into: str) -> int: ...
    def get_bikes(self, station: str) -> list[str]: ...
    def get_station_of(self, bike: str) -> str: ...
    def get_stations(self) -> list[str]: ...
```

Station names and bike ids are non-empty strings, and counts are `int`.

## Stations

- `add_station(name)` adds a station with no bikes. A name that is already
  in use raises `DockError`.
- `get_stations()` returns the names of the stations in use, in the order
  they were added.
- Every other method raises `KeyError` when given a station name that is
  not in use: one that was never added, or one that was closed.

## Bikes

- `dock(station, bike)` docks the bike at the end of the station's list. A
  bike that is already docked (at any station) raises `DockError`. A bike
  that was undocked may be docked again.
- `undock(bike)` takes the bike out of the network. The other bikes at its
  station keep their order. A bike that is not docked raises `KeyError`.
- `get_bikes(station)` returns the bikes at the station in the order they
  arrived there (by `dock`, `rebalance` or `close_station`), earliest first.
- `get_station_of(bike)` returns the name of the station where the bike is
  docked. A bike that is not docked raises `KeyError`.
- `rebalance(from_station, to_station, count)` moves the first `count`
  bikes of `get_bikes(from_station)` to the end of `to_station`'s list,
  keeping their order. `count` must be greater than 0; otherwise
  `ValueError` is raised. If `from_station` has fewer than `count` bikes,
  `DockError` is raised.
- `close_station(name, into)` moves every bike of station `name` to the end
  of `into`'s list, keeping their order, then closes station `name`: it is
  removed from `get_stations()`, and every method treats it as not in use.
  It returns how many bikes it moved (0 if the station had none).
- `rebalance` and `close_station` raise `ValueError` when both stations are
  the same.

## Errors

A failed call has no effect: if a method raises, the list of stations and
every station's bikes are unchanged. When a call has more than one problem,
which of its errors is raised is unspecified.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes values of the wrong type (counts that are not `int`, such as `1.5`
or `True`; names or bike ids that are not non-empty strings), which error is
raised when a call has several problems, whether the name of a closed
station may be added again, what happens if a returned list is changed, the
text of error messages, saving the network to a file, and use from several
threads.
