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
    def call(self, passenger_id: str, floor: int) -> None: ...
    def move_car(self, car_id: str, floor: int) -> None: ...
    def get_car_floor(self, car_id: str) -> int: ...
    def get_riders(self, car_id: str) -> list[str]: ...
    def get_waiting(self, floor: int) -> list[str]: ...
    def get_delivered(self) -> list[str]: ...
```

## Floors and cars

- The building has the floors `0` up to and including `top_floor`.
  `Building(top_floor)` raises `ValueError` for a `top_floor` below 1.
- A floor below 0 or above `top_floor` is invalid: `call`, `move_car` and
  `get_waiting` raise `ValueError` when given one.
- `add_car(car_id)` adds a car. It starts on floor 0 with nobody in it. It
  raises:
  - `ValueError` for an empty id;
  - `ElevatorError` for an id that is already a car.
- Every other method that takes a `car_id` raises `KeyError` for an id that
  is not a car, including values that are not strings at all, such as
  `None` or `1`.
- `get_car_floor(car_id)` returns the floor the car is on.

## Passengers

- `call(passenger_id, floor)` adds a passenger who waits on `floor` for a
  car. It raises `ValueError` for an empty passenger id or an invalid
  floor.
- `get_waiting(floor)` returns the ids of the passengers waiting on that
  floor, in the order they called.
- Calling does not put anyone in a car; passengers get in only when a car
  is moved to their floor.

## Moving a car

`move_car(car_id, floor)` takes the car, with its riders, to `floor` and
opens its doors there. Then, in this order:

1. Every rider gets out. They have all arrived.
2. Passengers waiting on this floor get in, in the order they called, up
   to **4** of them. Whoever does not fit keeps waiting, in the same order
   as before.

Only the car that was moved picks anybody up. A car that brings 4 riders
to a floor where 4 passengers wait leaves with those 4 passengers.

For example:

```python
b = Building(6)
b.add_car("east")
b.call("ann", 2)
b.call("ben", 2)
b.move_car("east", 2)      # ann and ben get in
b.get_riders("east")       # ["ann", "ben"]
b.get_waiting(2)           # []
b.call("cy", 5)
b.move_car("east", 5)      # ann and ben get out, then cy gets in
b.get_riders("east")       # ["cy"]
b.get_delivered()          # ["ann", "ben"]
b.move_car("east", 0)      # cy gets out
b.get_delivered()          # ["ann", "ben", "cy"]
```

- `get_riders(car_id)` returns the ids of the passengers in the car, in the
  order they got in.
- `get_delivered()` returns the ids of every passenger who has arrived,
  oldest first, from every car. Passengers who leave a car at the same stop
  are listed in the order they got in.

A failed call has no effect: if a method raises, every car, every waiting
list and the list of arrived passengers are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes which error is raised when a call has several problems, moving a
car to the floor it is already on, a `call` with a passenger id that was
already used, passenger and car ids that are not strings passed to `call`
or `add_car`, floors or a `top_floor` that are not `int`s, such as `1.5`,
`"2"` or `None`, `bool` floors, what happens if a returned list is changed,
the text of error messages, saving the building to a file, and use from
several threads.
