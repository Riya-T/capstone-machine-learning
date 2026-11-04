# Race telemetry

Write a module `telemetry.py` that collects the lap times of one race: which
cars take part, the time of every lap a car completes, and from that the
results of the race and the points each finishing car scores.

## Interface

```python
class TelemetryError(Exception): ...


class RaceTelemetry:
    def __init__(self, laps: int): ...
    def add_car(self, car_id: str) -> None: ...
    def get_cars(self) -> list[str]: ...
    def record_lap(self, car_id: str, lap_time: int) -> None: ...
    def get_lap_times(self, car_id: str) -> list[int]: ...
    def get_results(self) -> list[tuple[str, int]]: ...
```

All lap times are whole milliseconds, as `int`.

## The race and its cars

- `RaceTelemetry(laps)` is a race that is `laps` laps long.
  - `laps` of 0 or less raises `ValueError`.
- `add_car(car_id)` enters a car in the race.
  - An empty id raises `ValueError`.
  - An id that is already entered raises `TelemetryError`.
- `get_cars()` returns the ids of all cars, in the order they were added.

## Laps

- `record_lap(car_id, lap_time)` records one more lap driven by car
  `car_id`, which took `lap_time` milliseconds.
  - A car that was not added raises `KeyError`, also for values that are
    not strings, such as `None` or `1`.
  - A lap time of 0 or less raises `ValueError`.
  - A car has finished once it has `laps` laps recorded. Recording another
    lap for a car that has finished raises `TelemetryError`.
- `get_lap_times(car_id)` returns the car's lap times, in the order they
  were recorded, or `[]` if it has none yet.
  - A car that was not added raises `KeyError`.

## Results and points

- A car's total time is the sum of its lap times.
- `get_results()` returns one `(car_id, points)` pair for every car that
  has finished, lowest total time first. Cars that have not finished are
  left out, so the list may be empty.
- Cars with the same total time are in the same order as in `get_cars()`,
  whatever order they drove their laps in.
- The points of a pair depend only on its place in the list:

  | place | 1st | 2nd | 3rd | 4th | 5th | 6th | 7th and later |
  |---|---|---|---|---|---|---|---|
  | points | 10 | 6 | 4 | 3 | 2 | 1 | 0 |

- The results always follow the laps recorded so far: when a faster car
  finishes later, the cars behind it move down a place and get the points
  of their new place.

A failed call has no effect: if a method raises, every car, lap time and
result is unchanged.

## Example

```python
tel = RaceTelemetry(2)              # a race of 2 laps
for car in ["red", "blue", "green"]:
    tel.add_car(car)
tel.record_lap("red", 81000)
tel.get_results()                   # []: red has 1 of 2 laps
tel.record_lap("red", 80000)        # red has finished, total 161000
tel.get_results()                   # [("red", 10)]
tel.record_lap("red", 79000)        # TelemetryError: red has finished
tel.record_lap("green", 80000)
tel.record_lap("green", 80000)      # green: total 160000
tel.get_results()                   # [("green", 10), ("red", 6)]: red is 2nd now
tel.record_lap("blue", 79000)
tel.record_lap("blue", 81000)       # blue: total 160000, the same as green
tel.get_results()                   # [("blue", 10), ("green", 6), ("red", 4)]
                                    # blue was added before green
tel.get_lap_times("red")            # [81000, 80000]
tel.record_lap("pink", 80000)       # KeyError: pink was not added
```

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes which error is raised when one call has several problems, numbers
of laps or lap times that are not `int`s (such as `1.5`, `"10"` or `None`;
0 and negative numbers are tested), `bool` values, ids that are not strings
passed to `add_car`, whether `get_results` gives tuples or lists of two,
what happens if a returned list is changed, the text of error messages,
saving the data to a file, and use from several threads.
