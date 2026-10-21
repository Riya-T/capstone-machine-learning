Report how long passengers in `elevators.py` waited for a car.

- The building has a clock that starts at 0. Every `move_car` call that
  succeeds advances it by 1, before anybody gets out or in. Calls that raise
  do not advance it. Add `Building.get_clock() -> int`, which returns it.
- A passenger's wait is the clock when they got into a car minus the clock
  when they called. For example, a passenger who calls at clock 0 and gets
  in at the very next stop waited 1.
- Add `Building.get_wait(passenger_id) -> int`, which returns that
  passenger's wait. It raises `KeyError` for an id that was never called,
  then `ElevatorError` for a passenger who is still waiting. Passengers who
  have arrived keep their wait.
- Add `Building.get_longest_wait() -> int`: the largest wait of every
  passenger who has got into a car so far, riding or arrived, or 0 when
  nobody has. Passengers who are still waiting do not count.
- Add `Building.get_total_wait(car_id) -> int`: the sum of the waits of
  every passenger who got into that car. It raises `KeyError` for an id
  that is not a car.

All existing behavior must keep working.
