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

- `record_lap(race_id, car_id, lap_time)` records one more lap of race
  `race_id` driven by car `car_id`, which took `lap_time` milliseconds.
  `lap_time` must be an `int` greater than 0, or `ValueError` is raised.
- Car `car_id` has finished race `race_id` once it has as many laps
  recorded in that race as the race is long. Recording another lap of that
  race for that car then raises `TelemetryError`. Its laps in other races
  are not affected.
- `get_lap_times(race_id, car_id)` returns the lap times recorded in race
  `race_id` for car `car_id`, in the order they were recorded; an empty
  list if there are none yet.

When `record_lap` has several problems, the first of these is raised:

1. `KeyError` for an unknown race or car;
2. `ValueError` for an invalid lap time;
3. `TelemetryError` for a car that has already finished.

## Results and points

- A car's total time in a race is the sum of its lap times there.
- `get_results(race_id)` returns the ids of the cars that have finished the
  race, lowest total time first. Cars with the same total time are in the
  same order as in `get_cars()`, whatever order they drove their laps in.
  Cars that have not finished are left out, so the list may be empty.
- A car's place in a race is its place in `get_results(race_id)`, and each
  place scores championship points:

  | place | 1st | 2nd | 3rd | 4th | 5th | 6th | 7th and later |
  |---|---|---|---|---|---|---|---|
  | points | 10 | 6 | 4 | 3 | 2 | 1 | 0 |

- `get_points(car_id)` returns the sum, over all races, of the points for
  the car's place in that race. A race the car has not finished adds
  nothing, so a car that has finished no race has 0 points. Points always
  follow the results as they are now: when a faster car finishes later,
  the cars behind it move down a place and get the points of their new
  place.

A failed call has no effect: if a method raises, every car, race, lap time
and result is unchanged.

## Example

```python
tel = RaceTelemetry()
for car in ["red", "blue", "green"]:
    tel.add_car(car)
tel.add_race("monza", 2)
tel.add_race("spa", 1)
tel.record_lap("monza", "red", 81000)
tel.get_results("monza")                # []: red has 1 of 2 laps
tel.record_lap("monza", "red", 80000)   # red has finished monza, total 161000
tel.get_results("monza")                # ["red"]
tel.get_points("red")                   # 10
tel.record_lap("monza", "red", 79000)   # TelemetryError: red has finished monza
tel.record_lap("monza", "green", 80000)
tel.record_lap("monza", "green", 80000) # green: total 160000
tel.get_results("monza")                # ["green", "red"]
tel.get_points("red")                   # 6: red is 2nd now
tel.record_lap("monza", "blue", 79000)
tel.record_lap("monza", "blue", 81000)  # blue: total 160000, the same as green
tel.get_results("monza")                # ["blue", "green", "red"]: blue was added before green
tel.get_points("green")                 # 6
tel.get_points("red")                   # 4
tel.record_lap("spa", "red", 90000)
tel.get_results("spa")                  # ["red"]
tel.get_points("red")                   # 14: 4 for monza and 10 for spa
tel.get_lap_times("monza", "red")       # [81000, 80000]
tel.get_lap_times("spa", "blue")        # []
```

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes ids that are not strings passed to `add_car` or `add_race`, `bool`
lap times or lap counts, what happens if a returned list is changed, the
text of error messages, saving the data to a file, and use from several
threads.
