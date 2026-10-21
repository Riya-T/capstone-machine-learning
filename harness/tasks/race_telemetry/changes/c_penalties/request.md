Let race stewards hand out time penalties in `telemetry.py`.

- Add `RaceTelemetry.add_penalty(race_id, car_id, penalty)`, which adds
  `penalty` milliseconds to the car's time in that race. `penalty` must be
  an `int` greater than 0, or `ValueError` is raised. A car can get several
  penalties in one race, and they add up. A penalty can be given at any
  time: before the car's first lap, during the race, or after it finished.
- Add `RaceTelemetry.get_penalty(race_id, car_id) -> int`, the sum of the
  car's penalties in that race (0 if it has none).
- Add `RaceTelemetry.get_total_time(race_id, car_id) -> int`: the sum of the
  car's lap times in that race plus its penalties there. It is 0 for a car
  with no laps and no penalties, and it is also returned for a car that
  has not finished.
- `get_results` now ranks finished cars by this total, penalties included,
  lowest first; equal totals still keep the order cars were added.
  Championship points follow these results. A penalty never makes a car
  finish or unfinish a race, and penalties do not appear in
  `get_lap_times`.
- `add_penalty`, `get_penalty` and `get_total_time` raise `KeyError` for an
  unknown race or car. For `add_penalty`, `KeyError` comes before
  `ValueError`. A failed `add_penalty` changes nothing.

All existing behavior must keep working.
