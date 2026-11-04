Let race stewards hand out time penalties in `telemetry.py`.

- Add `RaceTelemetry.add_penalty(car_id, penalty)`, which adds `penalty`
  milliseconds to the car's time. A penalty of 0 or less raises
  `ValueError`. A car can get several penalties, and they add up. A
  penalty can be given at any time: before the car's first lap, during the
  race, or after it finished.
- Add `RaceTelemetry.get_penalty(car_id) -> int`, the sum of the car's
  penalties (0 if it has none).
- Add `RaceTelemetry.get_total_time(car_id) -> int`: the sum of the car's
  lap times plus its penalties. It is 0 for a car with no laps and no
  penalties, and it is also returned for a car that has not finished.
- `get_results` now ranks finished cars by this total, penalties included,
  lowest first; equal totals still keep the order cars were added, and the
  points still follow the places. For example, if red finishes in 180000
  and blue in 181000, a penalty of 2000 for red makes the results
  `[("blue", 10), ("red", 6)]`.
- A penalty never makes a car finish or unfinish the race, and penalties
  do not appear in `get_lap_times`.
- `add_penalty`, `get_penalty` and `get_total_time` raise `KeyError` for a
  car that was not added. Which error `add_penalty` raises when it also
  gets an invalid penalty is unspecified. A failed `add_penalty` changes
  nothing.

All existing behavior must keep working.
