# Race telemetry

Write a module `telemetry.py` that collects lap times from a racing series:
which cars take part, how many laps each race has, the time of every lap a
car completes, and from that the results of each race and the championship
points of each car.

## Interface

```python
class TelemetryError(Exception): ...


class RaceTelemetry:
    def __init__(self): ...
    def add_car(self, car_id: str) -> None: ...
    def add_race(self, race_id: str, laps: int) -> None: ...
    def record_lap(self, race_id: str, car_id: str, lap_time: int) -> None: ...
    def get_lap_times(self, race_id: str, car_id: str) -> list[int]: ...
    def get_results(self, race_id: str) -> list[str]: ...
    def get_points(self, car_id: str) -> int: ...
    def get_cars(self) -> list[str]: ...
```

All lap times are whole milliseconds, as `int`.

## Cars and races

- `add_car(car_id)` enters a car in the series. An empty id raises
  `ValueError`, and an id that is already entered raises `TelemetryError`.
- `get_cars()` returns the ids of all cars, in the order they were added.
- `add_race(race_id, laps)` adds a race that is `laps` laps long. An empty
  id raises `ValueError`; `laps` must be an `int` of at least 1, or
  `ValueError` is raised; a race id that is already in use raises
  `TelemetryError`. If both the id and `laps` are invalid, either
  `ValueError` may come first.
- Every method that takes a race id or a car id raises `KeyError` when it
  is not a known race or car, including values that are not strings at all,
  such as `None` or `1`. When both are unknown, either `KeyError` may come
  first. Any car may drive in any race.

## Laps

- `record_lap(race_id, car_id, lap_time)` records that the car completed
  one more lap of that race in `lap_time` milliseconds. `lap_time` must be
  an `int` greater than 0, or `ValueError` is raised.
- A car has finished a race once it has completed as many laps as the race
  is long. Recording another lap for a car that has finished raises
  `TelemetryError`.
- `get_lap_times(race_id, car_id)` returns the car's lap times in that race,
  in the order they were recorded; an empty list if it has none yet.

When `record_lap` has several problems, the first of these is raised:

1. `KeyError` for an unknown race or car;
2. `ValueError` for an invalid lap time;
3. `TelemetryError` for a car that has already finished.

## Results and points

- A car's total time in a race is the sum of its lap times there.
- `get_results(race_id)` returns the ids of the cars that have finished the
  race, fastest first: lowest total time first. Cars with the same total
  time are listed in the order they were added with `add_car`. Cars that
  have not finished are left out, so the list may be empty.
- Places in a race score championship points: 1st place 10 points, 2nd 6,
  3rd 4, 4th 3, 5th 2, 6th 1, and every later place 0.
- `get_points(car_id)` returns the car's points summed over all races,
  according to the results as they stand now. A faster car finishing later
  can push others down a place, and their points change with it. A car
  that has finished no race has 0 points.

A failed call has no effect: if a method raises, every car, race, lap time
and result is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes ids that are not strings passed to `add_car` or `add_race`, `bool`
lap times or lap counts, what happens if a returned list is changed, the
text of error messages, saving the data to a file, and use from several
threads.
