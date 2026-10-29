# Elevator dispatch

Write a module `elevators.py` that keeps track of the elevator cars in a
building, the passengers waiting on each floor and the passengers riding in
each car.

## Interface

```python
class ElevatorError(Exception): ...


class Building:
    def __init__(self, top_floor: int): ...
    def add_car(self, car_id: str) -> None: ...
    def call(self, passenger_id: str, floor: int, destination: int) -> None: ...
    def move_car(self, car_id: str, floor: int) -> None: ...
    def get_car_floor(self, car_id: str) -> int: ...
    def get_riders(self, car_id: str) -> list[str]: ...
    def get_waiting(self, floor: int) -> list[str]: ...
    def get_delivered(self) -> list[str]: ...
    def get_destination(self, passenger_id: str) -> int: ...
```

## Floors and cars

- The building has the floors `0` up to and including `top_floor`.
  `top_floor` must be an `int` of at least 1, or `ValueError` is raised.
- A floor is valid when it is an `int` from `0` to `top_floor`. Any method
  given an invalid floor raises `ValueError`.
- `add_car(car_id)` adds a car. It starts on floor 0 with nobody in it. An
  empty id raises `ValueError`, and adding an id that is already a car
  raises `ElevatorError`.
- Every other method that takes a `car_id` raises `KeyError` for an id that
  is not a car, including values that are not strings at all, such as
  `None` or `1`.
- `get_car_floor(car_id)` returns the floor the car is on.

## Passengers

- `call(passenger_id, floor, destination)` adds a passenger who waits on
  `floor` to be taken to `destination`. An empty passenger id raises
  `ValueError`, and so does an invalid `floor` or `destination`, or a call
  whose `floor` equals its `destination`.
- `call` records the passenger's id and destination. That record is kept
  for good: it is never removed, not when the passenger gets in and not
  when they arrive.
- `get_destination(passenger_id)` returns the `destination` the passenger
  gave to `call` (not the floor they are on now), whether they are still
  waiting, riding or have arrived. An id that was never used in a call
  raises `KeyError`. The same record of every id ever called is what makes
  a second call with that id raise `ElevatorError`.
- A passenger id can be used by one call only. Calling with an id that was
  already used, whether that passenger is still waiting, riding or has
  arrived, raises `ElevatorError`. Every `ValueError` check comes before
  this one.
- `get_waiting(floor)` returns the ids of the passengers waiting on that
  floor, in the order they called.
- Calling does not put anyone in a car; passengers get in only when a car
  is moved to their floor.

## Moving a car

`move_car(car_id, floor)` sends the car to `floor` and opens its doors
there. `KeyError` for the car is checked before `ValueError` for the floor.
When the doors open, in this order:

1. Every rider whose destination is this floor gets out, however many
   there are (several riders can get out at one stop). They have arrived.
2. Passengers waiting on this floor get in, in the order they called,
   while the car has fewer than **4** riders in total, counting the riders
   already inside. A car with 3 riders takes 1 more; a car with 4 takes
   nobody. Whoever does not fit keeps waiting, in the same order as before.

Only the car that was moved picks anybody up. A passenger keeps the
destination they called with while they wait and while they ride, so the
car knows where each rider gets out.

For example, with `Building(6)` and a car `"east"`: `call("ann", 2, 5)`
and `call("ben", 2, 4)`, then `move_car("east", 2)` gives riders
`["ann", "ben"]`. Then `move_car("east", 4)` lets ben out: the riders are
`["ann"]` and `get_delivered()` is `["ben"]`.

- `get_riders(car_id)` returns the ids of the passengers in the car, in the
  order they got in.
- `get_delivered()` returns the ids of every passenger who has arrived,
  oldest first. Passengers who leave a car at the same stop are listed in
  the order they got in.

A failed call has no effect: if a method raises, every car, every waiting
list and the list of arrived passengers are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes moving a car to the floor it is already on, passenger and car ids
that are not strings passed to `call` or `add_car`, `bool` floors, what
happens if a returned list is changed, the text of error messages, saving
the building to a file, and use from several threads.
