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
  `ValueError`, and so does a call whose `floor` equals its `destination`.
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
there. Moving a car to the floor it is already on is allowed and opens the
doors in the same way. `KeyError` for the car is checked before
`ValueError` for the floor. When the doors open, in this order:

1. Every rider whose destination is this floor gets out. They have arrived.
2. Passengers waiting on this floor get in, in the order they called, as
   long as the car has fewer than **4** riders. Whoever does not fit keeps
   waiting, in the same order as before.

Only the car that was moved picks anybody up.

- `get_riders(car_id)` returns the ids of the passengers in the car, in the
  order they got in.
- `get_delivered()` returns the ids of every passenger who has arrived,
  oldest first. Passengers who leave a car at the same stop are listed in
  the order they got in.

A failed call has no effect: if a method raises, every car, every waiting
list and the list of arrived passengers are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes passenger and car ids that are not strings passed to `call` or
`add_car`, `bool` floors, what happens if a returned list is changed, the
text of error messages, saving the building to a file, and use from several
threads.
