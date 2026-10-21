Make the number of riders a car can hold adjustable in `elevators.py`. The
building is getting a freight car, and other buildings use cars of other
sizes.

- `Building` takes a new keyword argument `capacity=4`: how many riders each
  car holds unless the car has its own capacity. It must be an `int` of at
  least 1 (not a `bool`); anything else raises `ValueError`.
- `add_car` takes a new keyword argument `capacity=None`. `None` means the
  car uses the building's capacity. Anything else must be an `int` of at
  least 1 (not a `bool`), or `ValueError` is raised and no car is added. If
  both the car id and the capacity are invalid, either `ValueError` may come
  first; both come before the `ElevatorError` for an id that is already a
  car.
- Add `Building.get_capacity(car_id) -> int`, which returns the car's
  current capacity. It raises `KeyError` for an id that is not a car.
- Add `Building.set_capacity(car_id, capacity)`, which replaces the car's
  capacity. It raises `KeyError` for an id that is not a car, then
  `ValueError` for an invalid capacity, then `ElevatorError` if the car
  already has more riders than the new capacity. In each case nothing
  changes. A capacity equal to the number of riders is fine.
- When a car's doors open, waiting passengers get in while the car has
  fewer riders than its own capacity. Changing a capacity does not put
  anyone in a car by itself; that happens only at the car's next stop.

All existing behavior must keep working.
