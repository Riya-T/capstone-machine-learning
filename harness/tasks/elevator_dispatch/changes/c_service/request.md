Let cars in `elevators.py` be taken out of service, for example while a
technician inspects them.

- Add `Building.take_out_of_service(car_id)`,
  `Building.return_to_service(car_id)` and
  `Building.is_in_service(car_id) -> bool`. All three raise `KeyError` for
  an id that is not a car. New cars are in service. Taking out a car that is
  already out of service, or returning one that is already in service, does
  nothing.
- A car can only be taken out of service when nobody is riding in it.
  Otherwise `take_out_of_service` raises `ElevatorError` (after the
  `KeyError` check) and nothing changes.
- Add `class CarOutOfService(ElevatorError)` to `elevators.py`.
- While a car is out of service, `move_car` on it raises `CarOutOfService`
  and nothing changes: the car stays where it is and nobody gets in or out.
  This is checked after the `KeyError` and `ValueError` checks.
- A car that is out of service keeps its floor, and `get_car_floor`,
  `get_riders`, `get_capacity` and `set_capacity` work on it as before.
- Add `Building.get_cars_in_service() -> list[str]`: the ids of the cars
  that are in service, in the order the cars were added.

All existing behavior must keep working.
