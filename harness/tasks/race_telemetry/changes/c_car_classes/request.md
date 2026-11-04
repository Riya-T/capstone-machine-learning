Split the cars in `telemetry.py` into classes (for example "pro" and
"amateur") that are also ranked among themselves.

- `add_car` takes a new keyword argument `car_class="open"`: the class the
  car races in. It must be a non-empty `str`, or `ValueError` is raised and
  no car is added. Which error is raised when a call also has another
  problem (an invalid car id, or a car id that is already entered) is
  unspecified.
- Add `RaceTelemetry.get_car_class(car_id) -> str`, which raises `KeyError`
  for a car that was not added.
- Add `RaceTelemetry.get_classes() -> list[str]`: every class that has at
  least one car, each once, in the order each class got its first car.
- `get_cars` takes a new keyword argument `car_class=None`. With a class,
  it returns only the cars of that class, still in the order they were
  added; a class without cars gives an empty list. `None` means all cars.
- `get_results` takes the same keyword argument `car_class=None`. With a
  class, it ranks only the finished cars of that class, in the same order
  as before, and scores their places within the class: the fastest car of
  the class gets the points of 1st place, the next one those of 2nd place,
  and so on, with the same points table. A class without finished cars
  gives an empty list. `None` ranks all cars, as before.

For example, with red and green in "pro" and blue in "amateur", if blue,
green and red finish in that order, `get_results()` is
`[("blue", 10), ("green", 6), ("red", 4)]` and
`get_results(car_class="pro")` is `[("green", 10), ("red", 6)]`.

All existing behavior must keep working.
