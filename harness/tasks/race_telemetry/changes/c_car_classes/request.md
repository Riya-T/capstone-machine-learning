Split the cars in `telemetry.py` into classes (for example "pro" and
"amateur") that are also ranked among themselves.

- `add_car` takes a new keyword argument `car_class="open"`: the class the
  car races in. It must be a non-empty `str`, or `ValueError` is raised and
  no car is added. Which error is raised when a call also has another
  problem (an invalid car id, or a car id that is already entered) is
  unspecified.
- Add `RaceTelemetry.get_car_class(car_id) -> str`, which raises `KeyError`
  for an unknown car.
- Add `RaceTelemetry.get_classes() -> list[str]`: every class that has at
  least one car, in the order each class got its first car.
- `get_cars` takes a new keyword argument `car_class=None`. With a class,
  it returns only the cars of that class, still in the order they were
  added; a class without cars gives an empty list. `None` means all cars.
- `get_results` takes the same keyword argument `car_class=None`. With a
  class, it returns only the cars of that class from the race's results,
  in the same order. An unknown race still raises `KeyError`.
- Add `RaceTelemetry.get_class_points(car_id) -> int`: the car's points
  when every race is scored among the cars of its own class only. In each
  race the car's place is its place in that race's results for its class,
  and that place scores with the race's points table. `get_points` keeps
  scoring the overall results. Unknown cars raise `KeyError`.

All existing behavior must keep working.
